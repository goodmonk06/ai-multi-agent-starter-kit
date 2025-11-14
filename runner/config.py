"""
Runner Configuration - 24時間稼働用の設定管理

機能:
- ジョブ実行間隔の設定
- エラーハンドリング設定
- 同時実行数の管理
- ウォッチドッグ設定
"""

import os
from typing import Dict, Any
from datetime import timedelta


class RunnerConfig:
    """Runnerの設定を管理するクラス"""

    def __init__(self):
        # 実行モード
        self.enabled = os.getenv("RUNNER_ENABLED", "false").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        # ジョブループ設定
        self.main_loop_interval = int(os.getenv("RUNNER_LOOP_INTERVAL", "60"))  # 秒
        self.heartbeat_seconds = int(os.getenv("RUNNER_HEARTBEAT_SECONDS", "30"))  # 秒
        self.cleanup_seconds = int(os.getenv("RUNNER_CLEANUP_SECONDS", "600"))  # 10分

        # エラーハンドリング
        self.max_consecutive_errors = int(os.getenv("RUNNER_MAX_ERRORS", "5"))
        self.backoff_base_seconds = int(os.getenv("BACKOFF_BASE_SECONDS", "2"))  # 秒
        self.max_backoff = int(os.getenv("RUNNER_MAX_BACKOFF", "300"))  # 5分

        # 同時実行設定
        self.max_concurrency = int(os.getenv("RUNNER_MAX_CONCURRENCY", "4"))

        # ウォッチドッグ設定
        self.watchdog_timeout = int(os.getenv("RUNNER_WATCHDOG_TIMEOUT", "600"))  # 10分
        self.watchdog_enabled = os.getenv("RUNNER_WATCHDOG_ENABLED", "true").lower() == "true"

        # レート制限
        self.max_jobs_per_minute = int(os.getenv("RUNNER_MAX_JOBS_PER_MINUTE", "10"))
        self.max_jobs_per_hour = int(os.getenv("RUNNER_MAX_JOBS_PER_HOUR", "100"))

        # ログ設定
        self.log_dir = os.getenv("RUNNER_LOG_DIR", "storage/jobs")
        self.log_rotation_days = int(os.getenv("RUNNER_LOG_ROTATION_DAYS", "30"))

        # シャットダウン設定
        self.graceful_shutdown_timeout = int(os.getenv("RUNNER_SHUTDOWN_TIMEOUT", "30"))  # 秒

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で返す"""
        return {
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "main_loop_interval": self.main_loop_interval,
            "heartbeat_seconds": self.heartbeat_seconds,
            "cleanup_seconds": self.cleanup_seconds,
            "max_consecutive_errors": self.max_consecutive_errors,
            "backoff_base_seconds": self.backoff_base_seconds,
            "max_backoff": self.max_backoff,
            "max_concurrency": self.max_concurrency,
            "watchdog_timeout": self.watchdog_timeout,
            "watchdog_enabled": self.watchdog_enabled,
            "max_jobs_per_minute": self.max_jobs_per_minute,
            "max_jobs_per_hour": self.max_jobs_per_hour,
            "log_dir": self.log_dir,
            "log_rotation_days": self.log_rotation_days,
            "graceful_shutdown_timeout": self.graceful_shutdown_timeout,
        }

    def validate(self) -> bool:
        """設定の妥当性をチェック"""
        if self.main_loop_interval < 1:
            raise ValueError("main_loop_interval must be >= 1")

        if self.max_consecutive_errors < 1:
            raise ValueError("max_consecutive_errors must be >= 1")

        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")

        if self.watchdog_timeout < self.main_loop_interval:
            raise ValueError("watchdog_timeout must be >= main_loop_interval")

        return True


# デフォルト設定インスタンス
default_config = RunnerConfig()
