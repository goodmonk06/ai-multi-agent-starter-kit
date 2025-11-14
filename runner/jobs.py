"""
Runner Jobs - 定期実行ジョブの定義と管理

機能:
- ジョブの登録・管理
- Heartbeat（生存確認）
- Cleanup（古いログの削除）
- Mock Daily Task（DRY_RUNテスト用）
"""

import asyncio
import os
import json
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import structlog

logger = structlog.get_logger()


class Job:
    """ジョブを表すクラス"""

    def __init__(
        self,
        name: str,
        func: Callable,
        interval: int,
        enabled: bool = True,
        description: str = "",
    ):
        """
        Args:
            name: ジョブ名
            func: 実行する非同期関数
            interval: 実行間隔（秒）
            enabled: 有効/無効
            description: ジョブの説明
        """
        self.name = name
        self.func = func
        self.interval = interval
        self.enabled = enabled
        self.description = description
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.error_count = 0
        self.last_error = None

    def should_run(self) -> bool:
        """ジョブを実行すべきか判定"""
        if not self.enabled:
            return False

        if self.last_run is None:
            return True

        elapsed = (datetime.now() - self.last_run).total_seconds()
        return elapsed >= self.interval

    async def run(self) -> Dict[str, Any]:
        """ジョブを実行"""
        start_time = datetime.now()

        try:
            logger.info("Job starting", job=self.name, run_count=self.run_count + 1)

            result = await self.func()

            self.last_run = datetime.now()
            self.next_run = self.last_run + timedelta(seconds=self.interval)
            self.run_count += 1

            duration = (datetime.now() - start_time).total_seconds()

            logger.info(
                "Job completed",
                job=self.name,
                duration=f"{duration:.2f}s",
                run_count=self.run_count,
            )

            return {
                "status": "success",
                "job": self.name,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration": duration,
                "result": result,
            }

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)

            logger.error(
                "Job failed",
                job=self.name,
                error=str(e),
                error_count=self.error_count,
            )

            return {
                "status": "error",
                "job": self.name,
                "start_time": start_time.isoformat(),
                "error": str(e),
                "error_count": self.error_count,
            }


class JobRegistry:
    """ジョブの登録と管理"""

    def __init__(self):
        self.jobs: Dict[str, Job] = {}

    def register(
        self,
        name: str,
        func: Callable,
        interval: int,
        enabled: bool = True,
        description: str = "",
    ) -> Job:
        """ジョブを登録"""
        job = Job(name, func, interval, enabled, description)
        self.jobs[name] = job
        logger.info("Job registered", job=name, interval=interval, enabled=enabled)
        return job

    def get(self, name: str) -> Optional[Job]:
        """ジョブを取得"""
        return self.jobs.get(name)

    def list(self) -> List[Job]:
        """すべてのジョブを取得"""
        return list(self.jobs.values())

    def enable(self, name: str) -> bool:
        """ジョブを有効化"""
        job = self.get(name)
        if job:
            job.enabled = True
            logger.info("Job enabled", job=name)
            return True
        return False

    def disable(self, name: str) -> bool:
        """ジョブを無効化"""
        job = self.get(name)
        if job:
            job.enabled = False
            logger.info("Job disabled", job=name)
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """ジョブ統計を取得"""
        return {
            "total_jobs": len(self.jobs),
            "enabled_jobs": sum(1 for j in self.jobs.values() if j.enabled),
            "disabled_jobs": sum(1 for j in self.jobs.values() if not j.enabled),
            "jobs": [
                {
                    "name": j.name,
                    "enabled": j.enabled,
                    "run_count": j.run_count,
                    "error_count": j.error_count,
                    "last_run": j.last_run.isoformat() if j.last_run else None,
                    "next_run": j.next_run.isoformat() if j.next_run else None,
                }
                for j in self.jobs.values()
            ],
        }


# =======================================
# ビルトインジョブ定義
# =======================================


async def heartbeat_job() -> Dict[str, Any]:
    """
    Heartbeat Job - 生存確認

    定期的に実行され、Runnerが正常に動作していることを確認
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Runner is healthy",
    }


async def cleanup_job() -> Dict[str, Any]:
    """
    Cleanup Job - 古いログファイルの削除

    30日以上前のJSONLログファイルを削除
    """
    log_dir = Path(os.getenv("RUNNER_LOG_DIR", "storage/runs"))
    retention_days = int(os.getenv("RUNNER_LOG_ROTATION_DAYS", "30"))
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if not log_dir.exists():
        return {"deleted_files": 0, "message": "Log directory does not exist", "dry_run": dry_run}

    cutoff_date = datetime.now() - timedelta(days=retention_days)
    deleted_files = []

    for log_file in log_dir.glob("*.jsonl"):
        # ファイル名から日付を取得（例: 2024-01-01.jsonl）
        try:
            file_date_str = log_file.stem  # 拡張子を除いた名前
            file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

            if file_date < cutoff_date:
                if not dry_run:
                    log_file.unlink()
                    logger.info("Deleted old log file", file=str(log_file))
                else:
                    logger.info("Would delete old log file (DRY_RUN)", file=str(log_file))
                deleted_files.append(str(log_file))

        except ValueError:
            # 日付形式でないファイル名はスキップ
            continue

    return {
        "deleted_files": len(deleted_files),
        "files": deleted_files[:10],  # 最大10件表示
        "retention_days": retention_days,
        "dry_run": dry_run,
        "mode": "simulated" if dry_run else "actual",
    }


async def demo_job() -> Dict[str, Any]:
    """
    Demo Job - 疑似タスク実行のデモ

    DRY_RUNモードでの動作確認用
    決定的な疑似タスクを生成し、実行イベントを返す
    """
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    # 決定的な疑似タスクデータを生成
    task_id = f"demo_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if dry_run:
        # DRY_RUNモードではモックデータを返す
        logger.info("Demo job executed (DRY_RUN mode)", task_id=task_id)
        return {
            "status": "completed",
            "mode": "DRY_RUN",
            "task_id": task_id,
            "task_type": "demo",
            "tasks_processed": 0,
            "cost": "$0.00",
            "message": "Demo task completed successfully (no real operations)",
        }
    else:
        # 実モードでは実際の処理を実行
        logger.info("Demo job executed (REAL mode)", task_id=task_id)
        return {
            "status": "completed",
            "mode": "REAL",
            "task_id": task_id,
            "task_type": "demo",
            "tasks_processed": 5,
            "message": "Demo task completed",
        }


# デフォルトジョブレジストリ
default_registry = JobRegistry()

# ビルトインジョブを登録
default_registry.register(
    name="heartbeat",
    func=heartbeat_job,
    interval=30,  # 30秒ごと
    enabled=True,
    description="Runner health check",
)

default_registry.register(
    name="cleanup",
    func=cleanup_job,
    interval=3600,  # 1時間ごと
    enabled=True,
    description="Clean up old log files",
)

default_registry.register(
    name="demo",
    func=demo_job,
    interval=300,  # 5分ごと（デモ用）
    enabled=True,
    description="Demo job for testing DRY_RUN mode",
)
