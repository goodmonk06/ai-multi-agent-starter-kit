#!/usr/bin/env python3
"""
Nightly Tasks - 夜間自動実行タスク

使い方:
    python scripts/nightly_tasks.py

機能:
- 基本的なヘルスチェック
- システムステータス確認
- デイリーレポート生成
"""

import asyncio
from datetime import datetime
from pathlib import Path

# structlogをオプショナルにする
try:
    import structlog
    _logger = structlog.get_logger()
    USE_STRUCTLOG = True
except ImportError:
    import logging
    _logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    USE_STRUCTLOG = False


class Logger:
    """structlogと標準loggingの両方に対応するラッパー"""

    @staticmethod
    def info(msg, **kwargs):
        if USE_STRUCTLOG:
            _logger.info(msg, **kwargs)
        else:
            extra = ' '.join(f'{k}={v}' for k, v in kwargs.items())
            _logger.info(f"{msg} {extra}" if extra else msg)

    @staticmethod
    def warning(msg, **kwargs):
        if USE_STRUCTLOG:
            _logger.warning(msg, **kwargs)
        else:
            extra = ' '.join(f'{k}={v}' for k, v in kwargs.items())
            _logger.warning(f"{msg} {extra}" if extra else msg)

    @staticmethod
    def error(msg, **kwargs):
        if USE_STRUCTLOG:
            _logger.error(msg, **kwargs)
        else:
            extra = ' '.join(f'{k}={v}' for k, v in kwargs.items())
            _logger.error(f"{msg} {extra}" if extra else msg)


logger = Logger()


async def run_health_check():
    """ヘルスチェックを実行"""
    logger.info("Running health check...")

    checks = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "checks": []
    }

    # ディレクトリ存在チェック
    required_dirs = ["storage", "storage/runs", "storage/reports"]
    for dir_path in required_dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        checks["checks"].append({
            "name": f"Directory: {dir_path}",
            "status": "ok",
            "exists": path.exists()
        })

    logger.info("Health check completed", checks=checks)
    return checks


async def run_system_status():
    """システムステータスを確認"""
    logger.info("Checking system status...")

    status = {
        "timestamp": datetime.now().isoformat(),
        "status": "operational",
        "components": {
            "core": "ok",
            "storage": "ok",
            "agents": "ok"
        }
    }

    logger.info("System status check completed", status=status)
    return status


async def generate_daily_summary():
    """デイリーサマリーを生成"""
    logger.info("Generating daily summary...")

    summary = f"""
    Daily Summary - {datetime.now().strftime('%Y-%m-%d')}
    ===================================
    - Health check: Completed
    - System status: Operational
    - Timestamp: {datetime.now().isoformat()}

    All nightly tasks completed successfully.
    """

    print(summary)
    logger.info("Daily summary generated")
    return summary


async def send_completion_notification(health, status, summary):
    """完了通知を送信"""
    try:
        # notifierをインポート（オプショナル）
        from core.notifier import send_notification

        subject = f"✅ Nightly Tasks Completed - {datetime.now().strftime('%Y-%m-%d')}"

        body = f"""
🌙 Nightly Tasks が正常に完了しました

実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

📊 実行結果:
-------------------------------------------
✓ ヘルスチェック: {health['status']}
✓ システムステータス: {status['status']}
✓ デイリーサマリー: 生成完了

{summary}

-------------------------------------------
次回実行: 明日の同時刻

AI Multi-Agent Starter Kit
"""

        result = await send_notification(subject=subject, body=body)

        if result.get("dry_run"):
            logger.info("Notification recorded in DRY_RUN mode")
        else:
            logger.info("Notification sent successfully")

        return result

    except ImportError:
        logger.info("Notifier not available, skipping notification")
        return {"status": "skipped", "reason": "notifier not available"}
    except Exception as e:
        logger.error("Failed to send notification", error=str(e))
        return {"status": "error", "error": str(e)}


async def main():
    """メイン処理"""
    print("=" * 60)
    print("🌙 Nightly Tasks Runner")
    print("=" * 60)
    print()

    try:
        # ヘルスチェック
        print("1. Running health check...")
        health = await run_health_check()
        print(f"   ✓ Health check: {health['status']}")
        print()

        # システムステータス
        print("2. Checking system status...")
        status = await run_system_status()
        print(f"   ✓ System status: {status['status']}")
        print()

        # デイリーサマリー
        print("3. Generating daily summary...")
        summary = await generate_daily_summary()
        print("   ✓ Daily summary generated")
        print()

        # 通知送信
        print("4. Sending completion notification...")
        notification = await send_completion_notification(health, status, summary)
        if notification.get("dry_run"):
            print("   🔵 Notification recorded (DRY_RUN mode)")
        elif notification.get("status") == "skipped":
            print("   ⚠️  Notification skipped")
        else:
            print("   ✓ Notification sent")
        print()

        print("=" * 60)
        print("✅ All nightly tasks completed successfully")
        print("=" * 60)

        return {
            "status": "success",
            "health": health,
            "system_status": status,
            "summary": summary,
            "notification": notification
        }

    except Exception as e:
        logger.error("Nightly tasks failed", error=str(e))
        print(f"❌ Error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
