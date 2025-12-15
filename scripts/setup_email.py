#!/usr/bin/env python3
"""
Email通知セットアップ - hilia10@ezweb.ne.jp に通知を送る設定

このスクリプトを実行すると、.envファイルのEmail設定を対話的に設定できます。
"""

import os
from pathlib import Path


def main():
    print("=" * 60)
    print("📧 Email通知セットアップ")
    print("=" * 60)
    print()
    print("送信先: hilia10@ezweb.ne.jp")
    print()
    print("📝 送信元のGmailアカウントが必要です")
    print()

    # 現在の.envファイルを読み込む
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env ファイルが見つかりません")
        print("   以下のコマンドで作成してください:")
        print("   cp .env.example .env")
        return

    # ユーザーにGmail情報を入力してもらう
    print("以下の情報を入力してください:")
    print()

    smtp_user = input("送信元Gmailアドレス: ").strip()
    if not smtp_user:
        print("❌ メールアドレスが入力されていません")
        return

    print()
    print("📌 Gmailアプリパスワードの取得方法:")
    print("   1. https://myaccount.google.com/ を開く")
    print("   2. セキュリティ → 2段階認証プロセスを有効化")
    print("   3. 「アプリパスワード」を検索")
    print("   4. アプリ: メール、デバイス: その他（AI Agent）")
    print("   5. 生成された16文字のパスワードをコピー")
    print()

    smtp_pass = input("Gmailアプリパスワード（16文字）: ").strip()
    if not smtp_pass:
        print("❌ パスワードが入力されていません")
        return

    # .envファイルを更新
    with open(env_file, "r") as f:
        lines = f.readlines()

    updated_lines = []
    for line in lines:
        if line.startswith("SMTP_USER="):
            updated_lines.append(f"SMTP_USER={smtp_user}\n")
        elif line.startswith("SMTP_PASS="):
            updated_lines.append(f"SMTP_PASS={smtp_pass}\n")
        elif line.startswith("SMTP_FROM="):
            updated_lines.append(f"SMTP_FROM={smtp_user}\n")
        else:
            updated_lines.append(line)

    with open(env_file, "w") as f:
        f.writelines(updated_lines)

    print()
    print("=" * 60)
    print("✅ Email設定が完了しました！")
    print("=" * 60)
    print()
    print("📧 送信元:", smtp_user)
    print("📧 送信先: hilia10@ezweb.ne.jp")
    print()
    print("💡 次のステップ:")
    print("   1. テスト送信:")
    print("      python scripts/test_notification.py")
    print()
    print("   2. 夜間実行を試す:")
    print("      python scripts/nightly_tasks.py")
    print()
    print("   3. GitHub Actionsでも動作させる場合:")
    print("      リポジトリ Settings → Secrets → Actions で設定:")
    print(f"      - SMTP_USER: {smtp_user}")
    print(f"      - SMTP_PASS: {smtp_pass}")
    print("      - SMTP_TO: hilia10@ezweb.ne.jp")
    print()


if __name__ == "__main__":
    main()
