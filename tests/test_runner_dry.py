"""
Tests for Runner in DRY_RUN Mode - ゼロコストでの動作確認

すべてのテストはDRY_RUNモードで実行され、実際のLLM APIは呼ばれません。
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from runner import Runner, RunnerConfig, JobRegistry, heartbeat_job, cleanup_job, demo_job
from scripts.morning_report import MorningReportGenerator


class TestRunnerConfig:
    """RunnerConfigのテスト"""

    def test_default_config(self):
        """デフォルト設定が正しく読み込まれるか"""
        config = RunnerConfig()

        assert config.dry_run is True  # デフォルトはDRY_RUN
        assert config.enabled is False  # デフォルトは無効
        assert config.heartbeat_seconds == 30
        assert config.cleanup_seconds == 600
        assert config.max_concurrency == 4
        assert config.backoff_base_seconds == 2

    def test_config_validation(self):
        """設定の妥当性チェックが機能するか"""
        config = RunnerConfig()

        # 正常な設定
        assert config.validate() is True

        # 不正な設定（同時実行数が0以下）
        config.max_concurrency = 0
        with pytest.raises(ValueError, match="max_concurrency must be >= 1"):
            config.validate()

    def test_config_to_dict(self):
        """設定が辞書形式で出力されるか"""
        config = RunnerConfig()
        config_dict = config.to_dict()

        assert "dry_run" in config_dict
        assert "heartbeat_seconds" in config_dict
        assert "cleanup_seconds" in config_dict
        assert "max_concurrency" in config_dict
        assert "backoff_base_seconds" in config_dict


class TestJobsInDryMode:
    """ジョブのDRY_RUNモードテスト"""

    @pytest.mark.asyncio
    async def test_heartbeat_job(self):
        """Heartbeatジョブが正常に実行されるか"""
        result = await heartbeat_job()

        assert result["status"] == "alive"
        assert "timestamp" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_cleanup_job_dry_run(self, tmp_path):
        """Cleanupジョブ（DRY_RUN）が正常に実行されるか"""
        # 環境変数を一時的に設定
        os.environ["RUNNER_LOG_DIR"] = str(tmp_path)
        os.environ["DRY_RUN"] = "true"

        # 古いファイルを作成（削除対象）
        old_file = tmp_path / "2020-01-01.jsonl"
        old_file.write_text('{"test": "data"}\n')

        result = await cleanup_job()

        assert result["dry_run"] is True
        assert result["mode"] == "simulated"
        # DRY_RUNモードでは実際には削除されない
        assert old_file.exists()

    @pytest.mark.asyncio
    async def test_demo_job(self):
        """Demoジョブが正常に実行されるか"""
        result = await demo_job()

        assert result["status"] == "completed"
        assert result["mode"] == "DRY_RUN"
        assert result["cost"] == "$0.00"
        assert "task_id" in result


class TestJobRegistry:
    """JobRegistryのテスト"""

    def test_register_job(self):
        """ジョブの登録が機能するか"""
        registry = JobRegistry()

        async def test_job():
            return {"status": "success"}

        job = registry.register(
            name="test_job",
            func=test_job,
            interval=60,
            enabled=True,
            description="Test job"
        )

        assert job.name == "test_job"
        assert job.interval == 60
        assert job.enabled is True

    def test_get_job(self):
        """ジョブの取得が機能するか"""
        registry = JobRegistry()

        async def test_job():
            return {"status": "success"}

        registry.register("test_job", test_job, 60)

        job = registry.get("test_job")
        assert job is not None
        assert job.name == "test_job"

    def test_enable_disable_job(self):
        """ジョブの有効化/無効化が機能するか"""
        registry = JobRegistry()

        async def test_job():
            return {"status": "success"}

        registry.register("test_job", test_job, 60)

        # 無効化
        assert registry.disable("test_job") is True
        job = registry.get("test_job")
        assert job.enabled is False

        # 有効化
        assert registry.enable("test_job") is True
        job = registry.get("test_job")
        assert job.enabled is True

    def test_get_stats(self):
        """統計情報の取得が機能するか"""
        registry = JobRegistry()

        async def test_job():
            return {"status": "success"}

        registry.register("job1", test_job, 60, enabled=True)
        registry.register("job2", test_job, 120, enabled=False)

        stats = registry.get_stats()

        assert stats["total_jobs"] == 2
        assert stats["enabled_jobs"] == 1
        assert stats["disabled_jobs"] == 1


class TestRunner:
    """Runnerのテスト"""

    @pytest.mark.asyncio
    async def test_runner_initialization(self):
        """Runnerの初期化が正常に行われるか"""
        config = RunnerConfig()
        registry = JobRegistry()

        runner = Runner(config=config, registry=registry)

        assert runner.config == config
        assert runner.registry == registry
        assert runner.running is False
        assert runner.shutdown_requested is False

    @pytest.mark.asyncio
    async def test_runner_disabled(self):
        """Runnerが無効の場合、起動しないか"""
        config = RunnerConfig()
        config.enabled = False

        runner = Runner(config=config)

        # 起動を試みる
        await runner.start()

        # 無効なので起動されない
        assert runner.running is False

    @pytest.mark.asyncio
    async def test_runner_get_status(self):
        """ステータス取得が機能するか"""
        runner = Runner()
        status = runner.get_status()

        assert "running" in status
        assert "consecutive_errors" in status
        assert "jobs_executed_last_hour" in status
        assert "registry_stats" in status

    @pytest.mark.asyncio
    async def test_runner_rate_limiting(self):
        """レート制限が機能するか"""
        config = RunnerConfig()
        config.max_jobs_per_minute = 2

        runner = Runner(config=config)

        # 2つのジョブを実行
        runner.job_timestamps.append(datetime.now())
        runner.job_timestamps.append(datetime.now())

        # レート制限に達しているはず
        assert runner._check_rate_limit() is False

    @pytest.mark.asyncio
    async def test_runner_log_job_result(self, tmp_path):
        """ジョブ結果のJSONLログが正常に記録されるか"""
        config = RunnerConfig()
        config.log_dir = str(tmp_path)

        runner = Runner(config=config)

        result = {
            "status": "success",
            "job": "test_job",
            "start_time": datetime.now().isoformat(),
            "duration": 1.5,
            "result": {"data": "test"}
        }

        runner._log_job_result(result)

        # ログファイルが作成されたか確認
        log_file = tmp_path / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        assert log_file.exists()

        # ログ内容を確認
        with open(log_file, "r") as f:
            log_entry = json.loads(f.read())

        assert log_entry["job"] == "test_job"
        assert log_entry["status"] == "success"
        assert log_entry["duration_ms"] == 1500
        assert log_entry["dry_run"] is True


class TestMorningReport:
    """MorningReportGeneratorのテスト"""

    def test_report_generator_initialization(self, tmp_path):
        """レポート生成器の初期化が正常に行われるか"""
        runs_dir = tmp_path / "runs"
        reports_dir = tmp_path / "reports"

        generator = MorningReportGenerator(
            runs_dir=str(runs_dir),
            reports_dir=str(reports_dir)
        )

        assert generator.runs_dir == runs_dir
        assert generator.reports_dir == reports_dir
        assert reports_dir.exists()

    def test_collect_events(self, tmp_path):
        """イベント収集が機能するか"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()

        # テストイベントを作成
        events = [
            {
                "timestamp": datetime.now().isoformat(),
                "job": "test_job",
                "status": "success",
                "duration_ms": 100,
                "dry_run": True
            }
            for _ in range(5)
        ]

        # JSONLファイルに書き込み
        log_file = runs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "w") as f:
            for event in events:
                json.dump(event, f)
                f.write("\n")

        # イベント収集
        generator = MorningReportGenerator(runs_dir=str(runs_dir))
        collected = generator.collect_events(hours=24)

        assert len(collected) == 5

    def test_aggregate_stats(self):
        """統計集計が機能するか"""
        events = [
            {
                "timestamp": datetime.now().isoformat(),
                "job": "heartbeat",
                "status": "success",
                "duration_ms": 50,
                "dry_run": True
            },
            {
                "timestamp": datetime.now().isoformat(),
                "job": "heartbeat",
                "status": "success",
                "duration_ms": 60,
                "dry_run": True
            },
            {
                "timestamp": datetime.now().isoformat(),
                "job": "cleanup",
                "status": "error",
                "duration_ms": 100,
                "dry_run": True
            },
        ]

        generator = MorningReportGenerator()
        stats = generator.aggregate_stats(events)

        assert stats["total_events"] == 3
        assert stats["by_job"]["heartbeat"]["count"] == 2
        assert stats["by_job"]["heartbeat"]["success"] == 2
        assert stats["by_job"]["cleanup"]["error"] == 1
        assert stats["by_status"]["success"] == 2
        assert stats["by_status"]["error"] == 1

    def test_generate_markdown_report(self):
        """Markdownレポート生成が機能するか"""
        events = [
            {
                "timestamp": datetime.now().isoformat(),
                "job": "heartbeat",
                "status": "success",
                "duration_ms": 50,
                "dry_run": True
            }
        ]

        generator = MorningReportGenerator()
        stats = generator.aggregate_stats(events)
        markdown = generator.generate_markdown_report(stats, events)

        assert "# 24時間稼働レポート" in markdown
        assert "総イベント数" in markdown
        assert "ジョブ別統計" in markdown

    def test_generate_csv_report(self):
        """CSVレポート生成が機能するか"""
        events = [
            {
                "timestamp": "2024-01-01T00:00:00",
                "job": "heartbeat",
                "status": "success",
                "duration_ms": 50,
                "dry_run": True
            }
        ]

        generator = MorningReportGenerator()
        csv_content = generator.generate_csv_report(events)

        lines = csv_content.split("\n")
        assert lines[0] == "timestamp,job,status,duration_ms,dry_run"
        assert "heartbeat" in lines[1]
        assert "success" in lines[1]

    def test_generate_full_report(self, tmp_path):
        """完全なレポート生成が機能するか"""
        runs_dir = tmp_path / "runs"
        reports_dir = tmp_path / "reports"
        runs_dir.mkdir()

        # テストイベントを作成
        events = [
            {
                "timestamp": datetime.now().isoformat(),
                "job": "heartbeat",
                "status": "success",
                "duration_ms": 50,
                "dry_run": True
            },
            {
                "timestamp": datetime.now().isoformat(),
                "job": "cleanup",
                "status": "success",
                "duration_ms": 100,
                "dry_run": True
            },
        ]

        # JSONLファイルに書き込み
        log_file = runs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "w") as f:
            for event in events:
                json.dump(event, f)
                f.write("\n")

        # レポート生成
        generator = MorningReportGenerator(
            runs_dir=str(runs_dir),
            reports_dir=str(reports_dir)
        )
        result = generator.generate_report(hours=24)

        # ファイルが生成されたか確認
        assert result["markdown"] is not None
        assert result["csv"] is not None
        assert Path(result["markdown"]).exists()
        assert Path(result["csv"]).exists()
        assert result["events_count"] == 2


class TestIntegration:
    """統合テスト"""

    @pytest.mark.asyncio
    async def test_full_workflow_dry_run(self, tmp_path):
        """DRY_RUNモードでの完全なワークフローテスト"""
        # 設定
        config = RunnerConfig()
        config.enabled = True
        config.dry_run = True
        config.log_dir = str(tmp_path / "runs")

        # ジョブレジストリ
        registry = JobRegistry()
        registry.register("heartbeat", heartbeat_job, interval=1, enabled=True)
        registry.register("demo", demo_job, interval=1, enabled=True)

        # Runner作成
        runner = Runner(config=config, registry=registry)

        # ジョブを1つ実行
        jobs = registry.list()
        for job in jobs:
            result = await runner._execute_job(job)
            runner._log_job_result(result)

        # ログファイルが作成されたか確認
        log_file = Path(config.log_dir) / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        assert log_file.exists()

        # レポート生成
        generator = MorningReportGenerator(
            runs_dir=config.log_dir,
            reports_dir=str(tmp_path / "reports")
        )
        report_result = generator.generate_report(hours=1)

        # レポートが生成されたか確認
        assert report_result["markdown"] is not None
        assert report_result["csv"] is not None
        assert report_result["events_count"] >= 2  # heartbeat + demo
