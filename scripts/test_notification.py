#!/usr/bin/env python3
"""
通知テスト - Slack/Email通知が正しく設定されているかテスト

使い方:
    python scripts/test_notification.py

これを実行すると、設定した通知先にテストメッセージが届きます。
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.notifier import send_notification
from datetime import datetime


async def main():
    print("=" * 60)
    print("📧 通知テスト")
    print("=" * 60)
    print()

    subject = f"テスト通知 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    body = """
🎉 AI Multi-Agent Starter Kit からのテスト通知

このメッセージが届いていれば、通知設定は正しく動作しています！

設定内容:
- 通知システムが正常に動作中
- スケジュールされたタスクが実行可能
- レポートが自動送信されます

次のステップ:
1. ダッシュボードで実行状況を確認
2. 夜間自動実行の結果を待つ
3. カスタムタスクを追加

---
AI Multi-Agent Starter Kit
Generated at: {}
""".format(datetime.now().isoformat())

    print("📤 通知を送信中...")
    print()

    try:
        result = await send_notification(
            subject=subject,
            body=body,
            test=True
        )

        if result.get("dry_run"):
            print("🔵 DRY_RUNモード:")
            print(f"   通知は送信されませんでしたが、記録されました")
            print(f"   ファイル: storage/notifications.jsonl")
            print()
            print("💡 実際に送信するには:")
            print("   .env ファイルで DRY_RUN=false に設定してください")
        else:
            print("✅ 通知が送信されました！")
            print()
            results = result.get("results", {})

            if "email" in results:
                email_result = results["email"]
                if email_result.get("status") == "success":
                    print(f"   📧 Email: {email_result.get('to')} に送信成功")
                else:
                    print(f"   ❌ Email: 送信失敗 - {email_result.get('message')}")

            if "slack" in results:
                slack_result = results["slack"]
                if slack_result.get("status") == "success":
                    print(f"   💬 Slack: 送信成功")
                else:
                    print(f"   ❌ Slack: 送信失敗 - {slack_result.get('message')}")

        print()
        print("=" * 60)
        print("✅ テスト完了")
        print("=" * 60)

    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        print()
        print("💡 トラブルシューティング:")
        print("   1. .env ファイルが存在するか確認")
        print("   2. 通知チャネル (NOTIFY_CHANNELS) が設定されているか確認")
        print("   3. 認証情報が正しいか確認")
        print()
        raise


if __name__ == "__main__":
    asyncio.run(main())
