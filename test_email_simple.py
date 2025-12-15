#!/usr/bin/env python3
"""
簡単なメール送信テスト

使い方:
    python test_email_simple.py

.envファイルから設定を読み込んでメール送信をテストします。
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# .envファイルを読み込む
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenvがなくても環境変数から読み込める

# .envファイルから設定を読み込む
smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
smtp_user = os.getenv("SMTP_USER")
smtp_pass = os.getenv("SMTP_PASS")
smtp_to = os.getenv("SMTP_TO")

# 設定チェック
if not smtp_user or smtp_user == "your-email@gmail.com":
    print("❌ エラー: SMTP_USERが設定されていません")
    print()
    print("💡 設定方法:")
    print("   1. .env ファイルを確認")
    print("   2. python scripts/setup_email.py を実行")
    exit(1)

if not smtp_pass or smtp_pass == "your-app-password":
    print("❌ エラー: SMTP_PASSが設定されていません")
    print()
    print("💡 設定方法:")
    print("   1. Gmailアプリパスワードを取得")
    print("   2. python scripts/setup_email.py を実行")
    exit(1)

print("=" * 60)
print("📧 メール送信テスト")
print("=" * 60)
print()
print(f"送信元: {smtp_user}")
print(f"送信先: {smtp_to}")
print()

try:
    # メッセージを作成
    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = smtp_to
    msg["Subject"] = f"✅ テスト通知 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    body = f"""
🎉 AI Multi-Agent Starter Kit からのテスト通知

このメールが届いていれば、通知設定は正しく動作しています！

設定内容:
- 送信元: {smtp_user}
- 送信先: {smtp_to}
- 送信時刻: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

✅ 設定完了！
これで毎晩の実行結果が自動で届きます。

---
AI Multi-Agent Starter Kit
"""

    msg.attach(MIMEText(body, "plain", "utf-8"))

    # SMTP送信
    print("📤 送信中...")
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    print()
    print("=" * 60)
    print("✅ メール送信成功！")
    print("=" * 60)
    print()
    print(f"📧 {smtp_to} にメールが届いているか確認してください")
    print()
    print("💡 迷惑メールフォルダもチェック！")
    print()

except Exception as e:
    print()
    print("=" * 60)
    print("❌ エラーが発生しました")
    print("=" * 60)
    print()
    print(f"エラー内容: {str(e)}")
    print()
    print("💡 確認事項:")
    print("  1. Gmailアプリパスワードが正しいか")
    print("  2. インターネット接続があるか")
    print("  3. Gmailアカウントが有効か")
    print()
