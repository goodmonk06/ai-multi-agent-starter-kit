"""
Runner Main - 24時間稼働のメインループ

機能:
- ジョブの定期実行
- エラーハンドリングとバックオフ
- グレースフルシャットダウン
- ウォッチドッグによる健全性監視
- JSONL形式でのログ出力
"""

import asyncio
import signal
import sys
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from collections import deque
import structlog

from runner.config import RunnerConfig, default_config
from runner.jobs import JobRegistry, default_registry

logger = structlog.get_logger()


class Runner:
    """24時間稼働のメインランナー"""

    def __init__(self, config: Optional[RunnerConfig] = None, registry: Optional[JobRegistry] = None):
        self.config = config or default_config
        self.registry = registry or default_registry

        # 状態管理
        self.running = False
        self.shutdown_requested = False
        self.consecutive_errors = 0
        self.last_heartbeat = None

        # レート制限用
        self.job_timestamps = deque(maxlen=self.config.max_jobs_per_hour)

        # ウォッチドッグ
        self.watchdog_last_update = datetime.now()

        # ログディレクトリの作成
        self.log_dir = Path(self.config.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # シグナルハンドラー設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Runner initialized", config=self.config.to_dict())

    def _signal_handler(self, signum, frame):
        """シグナルハンドラー（SIGINT, SIGTERM）"""
        logger.info("Shutdown signal received", signal=signum)
        self.shutdown_requested = True

    async def start(self):
        """Runnerを開始"""
        if not self.config.enabled:
            logger.warning("Runner is disabled (RUNNER_ENABLED=false)")
            return

        if not self.config.validate():
            logger.error("Invalid configuration")
            return

        self.running = True
        logger.info(
            "Runner starting",
            dry_run=self.config.dry_run,
            loop_interval=self.config.main_loop_interval,
        )

        # ウォッチドッグ開始
        if self.config.watchdog_enabled:
            asyncio.create_task(self._watchdog())

        # メインループ
        await self._main_loop()

    async def _main_loop(self):
        """メインジョブループ"""
        while self.running and not self.shutdown_requested:
            try:
                # レート制限チェック
                if not self._check_rate_limit():
                    logger.warning("Rate limit exceeded, waiting...")
                    await asyncio.sleep(60)
                    continue

                # 実行すべきジョブを収集
                jobs_to_run = [job for job in self.registry.list() if job.should_run()]

                if jobs_to_run:
                    logger.info("Jobs to execute", count=len(jobs_to_run))

                    # ジョブを実行（同時実行数制限）
                    for i in range(0, len(jobs_to_run), self.config.max_concurrency):
                        batch = jobs_to_run[i : i + self.config.max_concurrency]

                        # バッチ実行
                        results = await asyncio.gather(
                            *[self._execute_job(job) for job in batch], return_exceptions=True
                        )

                        # 結果をログに記録
                        for result in results:
                            if isinstance(result, Exception):
                                logger.error("Job execution exception", error=str(result))
                            else:
                                self._log_job_result(result)

                # ウォッチドッグ更新
                self.watchdog_last_update = datetime.now()
                self.consecutive_errors = 0

                # 次のループまで待機
                await asyncio.sleep(self.config.main_loop_interval)

            except Exception as e:
                self.consecutive_errors += 1
                logger.error(
                    "Main loop error",
                    error=str(e),
                    consecutive_errors=self.consecutive_errors,
                )

                # 連続エラーが上限を超えたら停止
                if self.consecutive_errors >= self.config.max_consecutive_errors:
                    logger.critical(
                        "Too many consecutive errors, stopping runner",
                        errors=self.consecutive_errors,
                    )
                    break

                # エクスポネンシャルバックオフ
                backoff_time = min(
                    self.config.backoff_base_seconds ** self.consecutive_errors,
                    self.config.max_backoff,
                )
                logger.info("Backing off", backoff_seconds=backoff_time)
                await asyncio.sleep(backoff_time)

        # グレースフルシャットダウン
        await self._shutdown()

    async def _execute_job(self, job) -> Dict[str, Any]:
        """ジョブを実行"""
        try:
            result = await job.run()

            # レート制限用のタイムスタンプ記録
            self.job_timestamps.append(datetime.now())

            return result

        except Exception as e:
            logger.error("Job execution failed", job=job.name, error=str(e))
            return {
                "status": "error",
                "job": job.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _check_rate_limit(self) -> bool:
        """レート制限をチェック"""
        now = datetime.now()

        # 1分間のジョブ数チェック
        recent_jobs = [ts for ts in self.job_timestamps if (now - ts).total_seconds() < 60]

        if len(recent_jobs) >= self.config.max_jobs_per_minute:
            logger.warning(
                "Per-minute rate limit reached",
                jobs=len(recent_jobs),
                limit=self.config.max_jobs_per_minute,
            )
            return False

        # 1時間のジョブ数チェック
        if len(self.job_timestamps) >= self.config.max_jobs_per_hour:
            oldest_job = min(self.job_timestamps)
            if (now - oldest_job).total_seconds() < 3600:
                logger.warning(
                    "Per-hour rate limit reached",
                    jobs=len(self.job_timestamps),
                    limit=self.config.max_jobs_per_hour,
                )
                return False

        return True

    def _log_job_result(self, result: Dict[str, Any]):
        """ジョブ結果をJSONLファイルに記録"""
        try:
            # 今日の日付でログファイル名を決定
            log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"

            # JSONL形式のイベントログを作成
            event_log = {
                "timestamp": result.get("start_time", datetime.now().isoformat()),
                "job": result.get("job", "unknown"),
                "status": result.get("status", "unknown"),
                "duration_ms": int(result.get("duration", 0) * 1000),
                "dry_run": self.config.dry_run,
                "result": result.get("result", {}),
            }

            # JSONL形式で追記
            with open(log_file, "a") as f:
                json.dump(event_log, f)
                f.write("\n")

        except Exception as e:
            logger.error("Failed to log job result", error=str(e))

    async def _watchdog(self):
        """ウォッチドッグ - 長時間応答がない場合にアラート"""
        while self.running:
            await asyncio.sleep(self.config.watchdog_timeout // 2)

            elapsed = (datetime.now() - self.watchdog_last_update).total_seconds()

            if elapsed > self.config.watchdog_timeout:
                logger.critical(
                    "Watchdog timeout - runner may be stuck",
                    elapsed=f"{elapsed:.0f}s",
                    timeout=self.config.watchdog_timeout,
                )

                # 必要に応じて緊急停止
                # self.shutdown_requested = True

    async def _shutdown(self):
        """グレースフルシャットダウン"""
        logger.info("Runner shutting down gracefully...")

        self.running = False

        # 実行中のジョブを待つ（タイムアウト付き）
        try:
            await asyncio.wait_for(
                asyncio.gather(*asyncio.all_tasks() - {asyncio.current_task()}),
                timeout=self.config.graceful_shutdown_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("Graceful shutdown timeout, forcing shutdown")

        # 最終統計をログ出力
        stats = self.registry.get_stats()
        logger.info("Final stats", stats=stats)

        logger.info("Runner stopped")

    def get_status(self) -> Dict[str, Any]:
        """Runnerのステータスを取得"""
        return {
            "running": self.running,
            "shutdown_requested": self.shutdown_requested,
            "consecutive_errors": self.consecutive_errors,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "watchdog_last_update": self.watchdog_last_update.isoformat(),
            "jobs_executed_last_hour": len(self.job_timestamps),
            "registry_stats": self.registry.get_stats(),
        }


async def main():
    """エントリーポイント"""
    logger.info("=== AI Multi-Agent Runner Starting ===")

    # 環境確認
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
    runner_enabled = os.getenv("RUNNER_ENABLED", "false").lower() == "true"

    if not runner_enabled:
        logger.warning(
            "Runner is disabled",
            hint="Set RUNNER_ENABLED=true in .env to enable",
        )
        return

    if dry_run:
        logger.info(
            "🔵 DRY_RUN MODE",
            message="All external API calls will be mocked (cost: $0.00)",
        )

    # Runnerインスタンス作成と実行
    runner = Runner()

    try:
        await runner.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.critical("Unexpected error", error=str(e))
        raise
    finally:
        logger.info("=== AI Multi-Agent Runner Stopped ===")


if __name__ == "__main__":
    # Python 3.7+の場合
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
        sys.exit(0)
