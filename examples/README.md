# 📚 サンプルスクリプト集

このフォルダには、AI Multi-Agent Starter Kitをすぐに使い始められるサンプルが入っています。

**すべてコピペで動きます！**

---

## 🚀 サンプル一覧

### 1. 📰 毎日のニュース要約 (`daily_news_summary.py`)

指定したトピックの最新ニュースを自動で検索・要約してSlack/Emailで送信

**使い方:**
```bash
# AI関連のニュース（デフォルト）
python examples/daily_news_summary.py

# カスタムトピック
python examples/daily_news_summary.py --topic "介護DX"
python examples/daily_news_summary.py --topic "スタートアップ投資"
```

**自動実行設定（毎朝7時）:**
`.github/workflows/morning_news.yml` を作成（後述）

---

### 2. 📱 SNS投稿スケジューラー (`schedule_sns_posts.py`)

1週間分のSNS投稿を自動生成してスケジュール

**使い方:**
```bash
# Twitter向けに7日分生成
python examples/schedule_sns_posts.py --topic "AI技術" --platform twitter

# Instagram向けに3日分生成
python examples/schedule_sns_posts.py --topic "ビジネス" --platform instagram --days 3
```

**対応プラットフォーム:**
- `twitter` - 280文字
- `facebook` - 5000文字
- `instagram` - 2200文字
- `linkedin` - 3000文字

---

## ⚙️ GitHub Actionsで自動実行

### 毎朝7時にニュース要約を送信

`.github/workflows/morning_news.yml` を作成:

```yaml
name: Morning News Summary

on:
  schedule:
    # 毎日午前7時（JST）= 前日22時（UTC）
    - cron: '0 22 * * *'
  workflow_dispatch:  # 手動実行も可能

jobs:
  news-summary:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run news summary
        env:
          PERPLEXITY_API_KEY: ${{ secrets.PERPLEXITY_API_KEY }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          NOTIFY_CHANNELS: slack
          DRY_RUN: false
        run: |
          python examples/daily_news_summary.py --topic "AI エージェント"
```

**設定方法:**
1. 上記の内容をコピー
2. `.github/workflows/morning_news.yml` として保存
3. GitHubにプッシュ
4. **Settings** → **Secrets** で API キーを設定

---

## 📊 よくある使い方

### 週次レポートを自動送信

```bash
# 毎週月曜9時に前週のサマリーを送信
python examples/weekly_report.py
```

### 在庫アラート

```bash
# 在庫が少なくなったら通知
python examples/inventory_alert.py --threshold 10
```

### カスタマーサポート

```bash
# FAQの自動返信
python examples/auto_reply.py --mode faq
```

---

## 💡 カスタマイズ方法

### 1. トピックを変更

```python
# daily_news_summary.py の中で
topic = "あなたの業界キーワード"
```

### 2. 通知先を変更

`.env` ファイルで:
```bash
NOTIFY_CHANNELS=slack,email  # 両方に送信
SLACK_WEBHOOK_URL=your-webhook-url
SMTP_TO=your-email@example.com
```

### 3. 実行頻度を変更

GitHub Actionsのcron設定:
```yaml
# 毎時実行
- cron: '0 * * * *'

# 毎日正午
- cron: '0 3 * * *'  # UTC 3時 = JST 12時

# 毎週月曜9時
- cron: '0 0 * * 1'  # UTC 月曜0時 = JST 月曜9時
```

---

## 🆘 トラブルシューティング

### エラー: `ModuleNotFoundError`

```bash
pip install -r requirements.txt
```

### エラー: API Key が無効

`.env` ファイルを確認:
```bash
cat .env | grep API_KEY
```

### 通知が届かない

1. `DRY_RUN=false` になっているか確認
2. `NOTIFY_CHANNELS` が設定されているか確認
3. テスト実行:
```bash
python scripts/test_notification.py
```

---

## 📖 詳細ガイド

- 初心者向け: `QUICKSTART.md`
- 全機能: `README.md`
- API仕様: http://localhost:8000/docs

---

**質問・要望はGitHub Issuesへ！**
