# 🚀 超簡単クイックスタートガイド

このガイドは**完全初心者向け**です。コピペだけで動かせます！

---

## 📱 STEP 1: スマホに通知を送る設定（5分）

### A. Slackで通知を受け取る場合（おすすめ！）

#### 1. Slack Webhook URLを取得

1. ブラウザで https://api.slack.com/apps にアクセス
2. **Create New App** → **From scratch** をクリック
3. アプリ名: `AI Agent Notifier`、ワークスペースを選択
4. 左メニューの **Incoming Webhooks** をクリック
5. **Activate Incoming Webhooks** をONにする
6. **Add New Webhook to Workspace** をクリック
7. 通知を送りたいチャンネルを選択（例: #general）
8. **Webhook URL** をコピー（`https://hooks.slack.com/services/...` という形式）

#### 2. GitHub Secretsに設定

1. GitHubのリポジトリページを開く
2. **Settings** → **Secrets and variables** → **Actions** をクリック
3. **New repository secret** をクリック
4. 以下を追加:
   - Name: `SLACK_WEBHOOK_URL`
   - Secret: さっきコピーしたWebhook URL
5. **Add secret** をクリック

#### 3. 環境変数ファイルを編集

`.env` ファイルに以下をコピペして追加:

```bash
# 通知設定
NOTIFY_CHANNELS=slack
DRY_RUN=false
```

**これだけ！** 毎晩の実行結果がSlackに届きます 🎉

---

### B. Gmailで通知を受け取る場合

#### 1. Gmailアプリパスワードを取得

1. Googleアカウント設定ページ https://myaccount.google.com/ を開く
2. **セキュリティ** → **2段階認証プロセス** を有効化（まだの場合）
3. **アプリパスワード** を検索して開く
4. アプリを選択: **メール**
5. デバイスを選択: **その他（カスタム名）** → 「AI Agent」と入力
6. **生成** をクリック
7. 表示された16文字のパスワードをコピー

#### 2. GitHub Secretsに設定

1. GitHubのリポジトリページ → **Settings** → **Secrets and variables** → **Actions**
2. 以下を追加:
   - Name: `SMTP_USER`、Secret: あなたのGmailアドレス
   - Name: `SMTP_PASS`、Secret: さっきコピーしたアプリパスワード
   - Name: `SMTP_TO`、Secret: 通知を受け取りたいメールアドレス

#### 3. 環境変数ファイルを編集

`.env` ファイルに以下をコピペして追加:

```bash
# Email通知設定
NOTIFY_CHANNELS=email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_TO=notification-recipient@example.com
DRY_RUN=false
```

**重要:** `SMTP_USER`、`SMTP_PASS`、`SMTP_TO` を実際の値に置き換えてください！

---

## 🖥️ STEP 2: スマホからダッシュボードを見る（3分）

### Codespacesを使っている場合

1. Codespacesのターミナルで以下をコピペして実行:

```bash
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

2. VS Codeの下部に「ポート」タブが表示されます
3. `8000` のポートの「地球儀アイコン」をクリック
4. 表示されたURLをスマホのブラウザで開く
5. `/dashboard` を追加してアクセス

例: `https://xxxxx-8000.app.github.dev/dashboard`

---

## 🎯 STEP 3: よくある使い方（コピペOK）

### 毎朝7時に業界ニュースを通知

`scripts/` フォルダに以下のファイルを作成します（後で自動作成します）

### 毎週月曜にレポート生成

### SNS投稿を予約

すべて後で自動的に作成します！

---

## ⚡ すぐ試せるコマンド

Codespacesまたはローカルのターミナルで以下をコピペして実行:

### 1. ヘルスチェック実行

```bash
python scripts/nightly_tasks.py
```

### 2. APIサーバー起動

```bash
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

ブラウザで開く:
- ダッシュボード: http://localhost:8000/dashboard
- API仕様書: http://localhost:8000/docs

### 3. 通知テスト

```bash
python scripts/send_test_notification.py
```

---

## 📊 夜間自動実行の確認方法

### 方法1: GitHubで確認

1. GitHubリポジトリページを開く
2. **Actions** タブをクリック
3. **Nightly Run** をクリック
4. 最新の実行結果を確認

### 方法2: ダッシュボードで確認

```
http://your-url:8000/dashboard
```

スマホのブラウザでも見やすい！

### 方法3: ログファイルで確認

```bash
# 最新のログを表示
cat storage/runs/*.jsonl | tail -20

# レポートを表示
cat storage/reports/*.md
```

---

## 🆘 困ったときは

### Q. 通知が届かない
A. 以下を確認:
1. `.env` の `DRY_RUN=false` になっているか
2. `NOTIFY_CHANNELS` が設定されているか
3. Slack/Email の認証情報が正しいか

### Q. エラーが出る
A. 依存関係をインストール:
```bash
pip install -r requirements.txt
```

### Q. スマホから見れない
A. Codespacesのポート転送を確認:
1. VS Codeの「ポート」タブ
2. 8000番ポートが「Public」になっているか確認

---

## 🎉 次のステップ

1. `examples/` フォルダのサンプルを試す（後で作成します）
2. 自分のビジネスに合わせてカスタマイズ
3. 新しいエージェントを追加

**すべてコピペでOKです！**
