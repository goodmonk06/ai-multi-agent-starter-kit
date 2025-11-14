"""
Tests for UI Dashboard and Notifier - DRY_RUN Mode

すべてのテストはDRY_RUNモードで実行され、外部APIは呼ばれません。
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from fastapi.testclient import TestClient
from core.notifier import Notifier, NotifierConfig, send_notification


class TestNotifier:
    """Notifierのテスト"""

    def test_notifier_config_dry_run(self):
        """NotifierConfigがDRY_RUNモードを正しく読み込むか"""
        config = NotifierConfig()

        # デフォルトはDRY_RUN=true
        assert config.dry_run is True

    def test_notifier_config_channels(self, monkeypatch):
        """通知チャネルが正しく読み込まれるか"""
        monkeypatch.setenv("NOTIFY_CHANNELS", "email,slack")

        config = NotifierConfig()

        assert "email" in config.channels
        assert "slack" in config.channels

    @pytest.mark.asyncio
    async def test_send_notification_dry_run(self, tmp_path):
        """DRY_RUNモードで通知がnotifications.jsonlに記録されるか"""
        # 一時ファイルを設定
        notifications_file = tmp_path / "notifications.jsonl"
        os.environ["NOTIFICATIONS_FILE"] = str(notifications_file)

        config = NotifierConfig()
        config.dry_run = True
        config.notifications_file = notifications_file

        notifier = Notifier(config)

        # 通知送信
        result = await notifier.send(
            subject="Test Subject",
            body="Test Body",
            channels=["email", "slack"]
        )

        # DRY_RUNモードの確認
        assert result["dry_run"] is True
        assert result["results"]["status"] == "dry_run"

        # ファイルに記録されているか確認
        assert notifications_file.exists()

        with open(notifications_file, "r") as f:
            notification = json.loads(f.read())

        assert notification["subject"] == "Test Subject"
        assert notification["body"] == "Test Body"
        assert notification["dry_run"] is True

    @pytest.mark.asyncio
    async def test_send_notification_helper(self, tmp_path):
        """send_notification ヘルパー関数が動作するか"""
        notifications_file = tmp_path / "notifications.jsonl"
        os.environ["NOTIFICATIONS_FILE"] = str(notifications_file)
        os.environ["DRY_RUN"] = "true"

        result = await send_notification(
            subject="Helper Test",
            body="This is a test from helper function",
            test=True
        )

        assert result["subject"] == "Helper Test"
        assert result["dry_run"] is True

    @pytest.mark.asyncio
    async def test_notifier_email_not_configured(self):
        """Email設定がない場合のエラーハンドリング"""
        config = NotifierConfig()
        config.dry_run = False  # 実モード
        config.smtp_user = ""
        config.smtp_pass = ""

        notifier = Notifier(config)

        result = await notifier._send_email("Test", "Body")

        assert result["status"] == "error"
        assert "not configured" in result["message"]

    @pytest.mark.asyncio
    async def test_notifier_slack_not_configured(self):
        """Slack設定がない場合のエラーハンドリング"""
        config = NotifierConfig()
        config.dry_run = False  # 実モード
        config.slack_webhook_url = ""

        notifier = Notifier(config)

        result = await notifier._send_slack("Test", "Body")

        assert result["status"] == "error"
        assert "not configured" in result["message"]


class TestDashboard:
    """ダッシュボードのテスト"""

    def test_dashboard_endpoint_exists(self):
        """GET /dashboard エンドポイントが存在するか"""
        from api.server import app

        client = TestClient(app)
        response = client.get("/dashboard")

        # HTMLが返ってくるか確認
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_dashboard_contains_title(self):
        """ダッシュボードにタイトルが含まれているか"""
        from api.server import app

        client = TestClient(app)
        response = client.get("/dashboard")

        assert "AI Multi-Agent Runner Dashboard" in response.text

    def test_dashboard_runner_disabled_status(self):
        """Runnerが無効の場合、ステータスが正しく表示されるか"""
        from api.server import app

        client = TestClient(app)
        response = client.get("/dashboard")

        # RunnerがNoneの場合はDISABLEDと表示される
        assert "DISABLED" in response.text or "disabled" in response.text.lower()


class TestIntegration:
    """統合テスト"""

    @pytest.mark.asyncio
    async def test_dashboard_and_notification_flow(self, tmp_path):
        """ダッシュボード→通知の完全なフロー"""
        from api.server import app

        # 1. ダッシュボードにアクセス
        client = TestClient(app)
        response = client.get("/dashboard")
        assert response.status_code == 200

        # 2. 通知を送信（DRY_RUN）
        notifications_file = tmp_path / "notifications.jsonl"
        os.environ["NOTIFICATIONS_FILE"] = str(notifications_file)
        os.environ["DRY_RUN"] = "true"

        result = await send_notification(
            subject="Integration Test",
            body="Testing dashboard and notification integration"
        )

        assert result["dry_run"] is True

        # 3. 通知ファイルが作成されたか確認
        assert notifications_file.exists()

        with open(notifications_file, "r") as f:
            notification = json.loads(f.read())

        assert notification["subject"] == "Integration Test"

    @pytest.mark.asyncio
    async def test_morning_report_with_notification(self, tmp_path):
        """Morning Reportと通知の統合テスト"""
        # Run用のディレクトリを作成
        runs_dir = tmp_path / "runs"
        reports_dir = tmp_path / "reports"
        notifications_file = tmp_path / "notifications.jsonl"

        runs_dir.mkdir()
        reports_dir.mkdir()

        # テストデータを作成
        test_events = [
            {
                "timestamp": datetime.now().isoformat(),
                "job": "heartbeat",
                "status": "success",
                "duration_ms": 50,
                "dry_run": True,
                "result": {"status": "alive"}
            },
            {
                "timestamp": datetime.now().isoformat(),
                "job": "cleanup",
                "status": "success",
                "duration_ms": 100,
                "dry_run": True,
                "result": {"deleted_files": 0}
            }
        ]

        # JSONLファイルに書き込み
        log_file = runs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "w") as f:
            for event in test_events:
                json.dump(event, f)
                f.write("\n")

        # レポート生成（通知付き）
        from scripts.morning_report import MorningReportGenerator
        from core.notifier import Notifier, NotifierConfig

        generator = MorningReportGenerator(
            runs_dir=str(runs_dir),
            reports_dir=str(reports_dir)
        )

        report_result = generator.generate_report(hours=24)

        assert report_result["markdown"] is not None
        assert report_result["csv"] is not None
        assert report_result["events_count"] == 2

        # 通知送信
        config = NotifierConfig()
        config.dry_run = True
        config.notifications_file = notifications_file

        notifier = Notifier(config)

        notification_result = await notifier.send(
            subject="Daily Report Test",
            body="Test report notification",
            report=report_result
        )

        # 通知が記録されたか確認
        assert notification_result["dry_run"] is True
        assert notifications_file.exists()
