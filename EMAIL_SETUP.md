# 📧 hilia10@ezweb.ne.jp への通知設定

毎晩の実行結果を `hilia10@ezweb.ne.jp` に自動送信する設定です。

---

## ✅ すでに設定済みの項目

以下は自動で設定済みです：

- ✅ `.env` ファイルに送信先 `hilia10@ezweb.ne.jp` を設定
- ✅ 通知チャネルを `email` に設定
- ✅ `DRY_RUN=false` に変更（実際にメール送信）
- ✅ GitHub Actionsワークフローに環境変数を追加

---

## 🔧 あなたがやること（3ステップ、5分）

### STEP 1: Gmailアプリパスワードを取得

1. ブラウザで https://myaccount.google.com/ を開く
2. **セキュリティ** をクリック
3. **2段階認証プロセス** をONにする（まだの場合）
4. 検索窓で「**アプリパスワード**」と入力して検索
5. アプリ: **メール** を選択
6. デバイス: **その他（カスタム名）** を選択 → 「**AI Agent**」と入力
7. **生成** をクリック
8. 表示された **16文字のパスワード** をコピー（例: `abcd efgh ijkl mnop`）

---

### STEP 2: セットアップスクリプトを実行

ターミナルで以下をコピペして実行：

```bash
python scripts/setup_email.py
```

聞かれたら以下を入力：

1. **送信元Gmailアドレス**: あなたのGmailアドレス（例: `yourname@gmail.com`）
2. **Gmailアプリパスワード**: STEP 1でコピーした16文字のパスワード

---

### STEP 3: GitHub Secretsに設定（夜間自動実行用）

GitHub Actionsでも動作させるため、GitHubに認証情報を保存します。

1. GitHubでリポジトリページを開く
2. **Settings** → **Secrets and variables** → **Actions** をクリック
3. **New repository secret** をクリックして以下を追加：

**1つ目:**
- Name: `SMTP_USER`
- Secret: あなたのGmailアドレス（例: `yourname@gmail.com`）
- **Add secret** をクリック

**2つ目:**
- Name: `SMTP_PASS`
- Secret: STEP 1でコピーした16文字のパスワード
- **Add secret** をクリック

---

## 🧪 テスト送信

設定が正しいか確認します：

```bash
python scripts/test_notification.py
```

**成功メッセージが表示され、`hilia10@ezweb.ne.jp` にメールが届けば完了！** 📧

---

## 📅 自動実行スケジュール

設定完了後、以下のタイミングで自動的にメールが届きます：

- **毎日午前11時（日本時間）** に前日の実行結果を送信
  - GitHub Actionsのcron設定: `0 2 * * *`（UTC午前2時 = JST午前11時）

### 手動で今すぐ実行したい場合

```bash
python scripts/nightly_tasks.py
```

または、GitHub Actionsで：

1. リポジトリページ → **Actions** タブ
2. **Nightly Run** をクリック
3. **Run workflow** → **Run workflow** をクリック

---

## 📧 届くメールの内容

件名: **✅ Nightly Tasks Completed - 2025-12-15**

```
🌙 Nightly Tasks が正常に完了しました

実行日時: 2025年12月15日 11:00:00

📊 実行結果:
-------------------------------------------
✓ ヘルスチェック: healthy
✓ システムステータス: operational
✓ デイリーサマリー: 生成完了

    Daily Summary - 2025-12-15
    ===================================
    - Health check: Completed
    - System status: Operational
    - Timestamp: 2025-12-15T11:00:00

    All nightly tasks completed successfully.

-------------------------------------------
次回実行: 明日の同時刻

AI Multi-Agent Starter Kit
```

---

## 🆘 トラブルシューティング

### Q1. メールが届かない

**確認すること:**
1. `.env` の `SMTP_USER` と `SMTP_PASS` が正しいか
2. `.env` の `DRY_RUN=false` になっているか
3. Gmailアプリパスワードが正しいか（16文字）
4. 迷惑メールフォルダに入っていないか

**テスト実行:**
```bash
python scripts/test_notification.py
```

エラーメッセージを確認してください。

---

### Q2. GitHub Actionsでエラーが出る

**確認すること:**
1. GitHub Secrets に `SMTP_USER` と `SMTP_PASS` を設定したか
2. ワークフローファイルが最新版にプッシュされているか

**ログ確認:**
1. GitHub → **Actions** タブ
2. 失敗した実行をクリック
3. **Run nightly tasks** のログを確認

---

### Q3. ezwebメールのフィルタでブロックされる

auのezwebメールは、迷惑メール設定で拒否される場合があります。

**対処法:**
1. ezwebメールの設定ページを開く
2. 迷惑メールフィルター設定
3. 送信元Gmailアドレスを「受信許可リスト」に追加

---

### Q4. セットアップスクリプトでエラー

```bash
# .envファイルが無い場合
cp .env.example .env

# 再実行
python scripts/setup_email.py
```

---

## 💡 よくある質問

### Q. 送信時刻を変更したい

`.github/workflows/nightly-run.yml` のcron設定を変更：

```yaml
# 毎日午前9時（JST） = UTC 0時
- cron: '0 0 * * *'

# 毎日午後6時（JST） = UTC 9時
- cron: '0 9 * * *'
```

### Q. 送信元のGmailアドレスを変更したい

```bash
python scripts/setup_email.py
```

再実行して新しいGmailアドレスとパスワードを入力。

### Q. Slackにも送りたい

`.env` ファイルで：
```bash
NOTIFY_CHANNELS=email,slack
SLACK_WEBHOOK_URL=your-webhook-url
```

---

**以上で設定完了です！🎉**

質問があれば、GitHub Issuesまで！
