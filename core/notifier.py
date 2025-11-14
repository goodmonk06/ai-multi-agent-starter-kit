"""
Notifier - 通知システム（DRY_RUN対応）

機能:
- DRY_RUN=true: 外部送信せず notifications.jsonl に記録
- DRY_RUN=false: SMTP/Slack に実際に送信
- チャネル: email, slack（環境変数で設定）
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import structlog
import httpx

logger = structlog.get_logger()


class NotifierConfig:
    """通知設定"""

    def __init__(self):
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        # 通知チャネル（カンマ区切り）
        channels_str = os.getenv("NOTIFY_CHANNELS", "")
        self.channels = [c.strip() for c in channels_str.split(",") if c.strip()]

        # SMTP設定
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_pass = os.getenv("SMTP_PASS", "")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user)
        self.smtp_to = os.getenv("SMTP_TO", "")

        # Slack設定
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")

        # ストレージ
        self.notifications_file = Path(os.getenv("NOTIFICATIONS_FILE", "storage/notifications.jsonl"))
        self.notifications_file.parent.mkdir(parents=True, exist_ok=True)


class Notifier:
    """通知クラス"""

    def __init__(self, config: Optional[NotifierConfig] = None):
        self.config = config or NotifierConfig()

    async def send(
        self,
        subject: str,
        body: str,
        channels: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        通知を送信

        Args:
            subject: 件名
            body: 本文
            channels: 送信チャネル（Noneの場合はconfig.channelsを使用）
            **kwargs: 追加情報

        Returns:
            結果の辞書
        """
        channels = channels or self.config.channels
        timestamp = datetime.now().isoformat()

        notification = {
            "timestamp": timestamp,
            "subject": subject,
            "body": body,
            "channels": channels,
            "dry_run": self.config.dry_run,
            "metadata": kwargs,
            "results": {}
        }

        if self.config.dry_run:
            # DRY_RUNモード: notifications.jsonlに記録のみ
            logger.info("Notification (DRY_RUN)", subject=subject, channels=channels)

            notification["results"]["status"] = "dry_run"
            notification["results"]["message"] = "Recorded to notifications.jsonl (no actual sending)"

            # JSONLファイルに追記
            with open(self.config.notifications_file, "a") as f:
                json.dump(notification, f)
                f.write("\n")

            return notification

        # 実モード: 実際に送信
        logger.info("Sending notification", subject=subject, channels=channels)

        for channel in channels:
            if channel == "email":
                result = await self._send_email(subject, body)
                notification["results"]["email"] = result

            elif channel == "slack":
                result = await self._send_slack(subject, body)
                notification["results"]["slack"] = result

            else:
                logger.warning("Unknown notification channel", channel=channel)
                notification["results"][channel] = {
                    "status": "error",
                    "message": f"Unknown channel: {channel}"
                }

        # 実モードでもログに記録
        with open(self.config.notifications_file, "a") as f:
            json.dump(notification, f)
            f.write("\n")

        return notification

    async def _send_email(self, subject: str, body: str) -> Dict[str, Any]:
        """Email送信"""
        try:
            if not self.config.smtp_user or not self.config.smtp_pass:
                return {
                    "status": "error",
                    "message": "SMTP credentials not configured"
                }

            if not self.config.smtp_to:
                return {
                    "status": "error",
                    "message": "SMTP_TO not configured"
                }

            # MIMEメッセージを作成
            msg = MIMEMultipart()
            msg["From"] = self.config.smtp_from
            msg["To"] = self.config.smtp_to
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain", "utf-8"))

            # SMTP送信
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_pass)
                server.send_message(msg)

            logger.info("Email sent successfully", to=self.config.smtp_to, subject=subject)

            return {
                "status": "success",
                "to": self.config.smtp_to,
                "message": "Email sent successfully"
            }

        except Exception as e:
            logger.error("Failed to send email", error=str(e))
            return {
                "status": "error",
                "message": str(e)
            }

    async def _send_slack(self, subject: str, body: str) -> Dict[str, Any]:
        """Slack送信"""
        try:
            if not self.config.slack_webhook_url:
                return {
                    "status": "error",
                    "message": "SLACK_WEBHOOK_URL not configured"
                }

            # Slack webhook ペイロード
            payload = {
                "text": f"*{subject}*\n\n{body}"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.slack_webhook_url,
                    json=payload,
                    timeout=10.0
                )

                if response.status_code == 200:
                    logger.info("Slack notification sent successfully", subject=subject)
                    return {
                        "status": "success",
                        "message": "Slack notification sent successfully"
                    }
                else:
                    logger.error(
                        "Slack notification failed",
                        status_code=response.status_code,
                        response=response.text
                    )
                    return {
                        "status": "error",
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }

        except Exception as e:
            logger.error("Failed to send Slack notification", error=str(e))
            return {
                "status": "error",
                "message": str(e)
            }


# デフォルトNotifierインスタンス
default_notifier = Notifier()


async def send_notification(subject: str, body: str, **kwargs) -> Dict[str, Any]:
    """
    通知を送信（ヘルパー関数）

    Args:
        subject: 件名
        body: 本文
        **kwargs: 追加情報

    Returns:
        送信結果
    """
    return await default_notifier.send(subject, body, **kwargs)
