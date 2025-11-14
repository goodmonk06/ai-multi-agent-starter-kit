# AI Multi-Agent Starter Kit

多エージェントAIシステムのための基盤フレームワーク - 福祉DX、SNS自動化、採用、経営分析など、あらゆる業務自動化に対応できる"基礎OS"

## 概要

AI Multi-Agent Starter Kitは、LangGraphをベースにした多エージェントシステムの構築を高速化するフレームワークです。複数の専門エージェントが協調して動作し、複雑なビジネスプロセスを自動化します。

### 主な特徴

- **クラウドファースト開発**: GitHub Codespaces でローカル環境不要
- **完全自動セットアップ**: API キーは GitHub Secrets から自動注入
- **モジュラーアーキテクチャ**: apps/配下に新しいアプリケーションを簡単に追加可能
- **LangGraphベース**: 強力なワークフローエンジン
- **共有メモリ**: エージェント間でデータを共有
- **インテリジェントルーティング**: タスクを最適なエージェントに自動振り分け
- **自動スケーリング**: Docker/Kubernetesで簡単にデプロイ
- **CI/CD対応**: GitHub Actionsで自動テスト・デプロイ

## プロジェクト構造

```
ai-multi-agent-starter-kit/
├── .devcontainer/          # Codespaces 開発環境
│   ├── devcontainer.json   # Dev Container 設定
│   └── setup.sh            # 自動セットアップスクリプト
│
├── agents/                 # 専門エージェント
│   ├── scheduler_agent.py  # タスクスケジューリング
│   ├── analyzer_agent.py   # データ分析
│   ├── generator_agent.py  # コンテンツ生成
│   ├── compliance_agent.py # コンプライアンスチェック
│   ├── executor_agent.py   # タスク実行
│   └── search_agent.py     # Web検索（Perplexity）
│
├── core/                   # コアインフラ
│   ├── workflow.py         # LangGraphワークフロー
│   ├── memory.py           # 共有メモリストア
│   ├── task_router.py      # タスクルーター
│   ├── tools.py            # 共通ツール
│   ├── demo_search.py      # SearchAgent デモスクリプト
│   └── tools/
│       └── perplexity_search.py  # Perplexity API統合
│
├── apps/                   # ビジネスアプリケーション
│   ├── care_scheduler/     # 福祉DX
│   ├── sns_auto/           # SNS自動化
│   └── hr_matching/        # 採用マッチング
│
├── api/                    # REST API
│   ├── server.py           # FastAPIサーバー
│   └── routes/             # APIルート
│
├── docker/                 # Docker設定
│   ├── Dockerfile
│   ├── docker-compose.yml  # 本番環境用
│   └── compose.dev.yml     # 開発環境用（Codespaces）
│
└── .github/workflows/      # CI/CD
    ├── auto-merge.yml      # 自動マージ（claude/* ブランチ）
    ├── codespaces-test.yml # Codespaces テスト
    ├── nightly-run.yml     # 夜間自動実行
    ├── codegen.yml         # コード自動生成
    └── deploy.yml          # 自動デプロイ
```

## クイックスタート

### 推奨: GitHub Codespaces で始める（ローカル環境不要）

**最も簡単な方法** - ローカルに何もインストールせず、クラウド上で即座に開発を開始できます。

#### 1. GitHub Secrets を設定

リポジトリの Settings → Secrets and variables → Codespaces で以下のシークレットを追加：

```
# API Keys
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GEMINI_API_KEY=your-gemini-api-key
PERPLEXITY_API_KEY=your-perplexity-api-key

# LLM設定
OPENAI_ENABLED=false  # デフォルトで無効
LLM_PRIORITY=anthropic,gemini,perplexity  # 優先順位

# オプション: Perplexity制限設定
PERPLEXITY_MAX_REQUESTS_PER_DAY=50
PERPLEXITY_MAX_DOLLARS_PER_MONTH=5

# データベース設定
REDIS_URL=redis://redis:6379
DATABASE_URL=postgresql://postgres:postgres@db:5432/ai_agents
```

#### 2. Codespaces を起動

1. GitHubリポジトリページで **Code** → **Codespaces** → **Create codespace on main** をクリック
2. 自動的に開発環境がセットアップされます（約2-3分）
3. セットアップが完了すると、`.env` ファイルが自動生成され、全てのサービスが起動可能な状態になります

#### 3. サービスを起動

Codespaces のターミナルで：

```bash
# 全サービスを起動（API、Redis、PostgreSQL）
docker compose -f docker/compose.dev.yml up -d

# ヘルスチェック
curl http://localhost:8000/health

# Swagger UIで動作確認
# ポート転送されたURLにアクセス（Codespacesが自動的に通知）
```

#### 4. 開発を開始

```bash
# 検索エージェントのデモを実行
python -m core.demo_search "AI エージェントの最新動向"

# APIサーバーを起動（ホットリロード付き）
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

**環境の特徴:**
- ✅ API キーは GitHub Secrets から自動注入（手動設定不要）
- ✅ Python、Docker、Git、GitHub CLI がプリインストール済み
- ✅ VS Code 拡張機能（Python、Docker、Copilot、GitLens）が自動インストール
- ✅ ポート転送が自動設定（8000、3000、5432、6379）
- ✅ `.env` ファイルは起動時に自動生成

---

### オプション: ローカル環境でセットアップ

ローカルで開発したい場合は以下の手順で：

#### 1. 環境セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/ai-multi-agent-starter-kit.git
cd ai-multi-agent-starter-kit

# 環境変数を設定
cp .env.example .env
# .envファイルを編集してAPI キーを設定

# 依存関係をインストール
pip install -r requirements.txt
```

#### 2. Dockerで起動

```bash
# Docker Composeで全サービスを起動
docker compose -f docker/compose.dev.yml up -d

# ヘルスチェック
curl http://localhost:8000/health
```

#### 3. APIサーバーを起動（開発モード）

```bash
# APIサーバーを起動
python -m uvicorn api.server:app --reload

# ブラウザで確認
# http://localhost:8000/docs (Swagger UI)
```

## 使用例

### タスクを作成

```python
import asyncio
from core import MemoryStore, TaskRouter, AgentWorkflow
from agents import SchedulerAgent, AnalyzerAgent, GeneratorAgent

async def main():
    # システムを初期化
    memory = MemoryStore()
    agents = {
        "scheduler": SchedulerAgent(memory),
        "analyzer": AnalyzerAgent(memory),
        "generator": GeneratorAgent(memory),
    }

    router = TaskRouter(agents)
    workflow = AgentWorkflow(agents, memory, router)

    # タスクを作成
    task = {
        "task_type": "sns_post",
        "description": "Create a social media post about AI",
        "data": {
            "topic": "AI Multi-Agent Systems",
            "platform": "twitter"
        }
    }

    # タスクをルーティング
    result = await router.route_task(task)
    print(f"Task routed to: {result['primary_agent']}")

asyncio.run(main())
```

### REST APIを使用

```bash
# タスクを作成
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sns_post",
    "description": "Create a post",
    "priority": 8,
    "data": {"topic": "AI"}
  }'

# エージェントリストを取得
curl http://localhost:8000/api/v1/agents

# SNS投稿を作成
curl -X POST http://localhost:8000/api/v1/apps/sns_auto/posts \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "twitter",
    "topic": "AI is transforming healthcare",
    "style": "professional"
  }'
```

## アプリケーション

### 1. Care Scheduler（福祉DX）

介護・福祉施設のスケジューリングと管理を自動化

```python
from apps.care_scheduler import CareSchedulerApp

app = CareSchedulerApp(agents, workflow, memory)

# シフトスケジュールを作成
schedule = await app.create_shift_schedule(
    facility_id="facility_001",
    date_range={"start": "2024-01-01", "end": "2024-01-31"},
    staff_list=[...],
    requirements={...}
)
```

### 2. SNS Auto（SNS自動化）

ソーシャルメディアの投稿、分析、エンゲージメント管理

```python
from apps.sns_auto import SnsAutoApp

app = SnsAutoApp(agents, workflow, memory)

# 投稿を作成
post = await app.create_post(
    platform="twitter",
    topic="AI Multi-Agent Systems",
    style="professional",
    hashtags=["AI", "Automation"]
)
```

### 3. HR Matching（採用マッチング）

求人と候補者のマッチング、採用プロセスの自動化

```python
from apps.hr_matching import HrMatchingApp

app = HrMatchingApp(agents, workflow, memory)

# 候補者をマッチング
matches = await app.match_candidates(
    job_posting={...},
    candidates=[...],
    matching_criteria={...}
)
```

## エージェント

### Scheduler Agent
- タスクの優先順位付け
- リソース配分の最適化
- デッドライン管理

### Analyzer Agent
- データパターンの検出
- 予測分析
- 異常検知
- レポート生成

### Generator Agent
- テキスト生成
- SNS投稿の作成
- メール/メッセージの自動生成

### Compliance Agent
- コンテンツの適合性チェック
- 個人情報保護の確認
- 規制要件の検証

### Executor Agent
- タスクの実行
- ワークフローの調整
- 外部APIの呼び出し

### Search Agent
- Perplexity APIを使った高品質なWeb検索
- リアルタイム情報の取得
- 検索結果の要約と構造化
- 1日のリクエスト数・月額利用額の制限管理

## Search Agent の使い方

### デモスクリプトを実行

```bash
# シンプルな検索
python -m core.demo_search "介護DXの最新トレンド"

# 最大トークン数を指定
python -m core.demo_search "AI エージェント 活用事例" --max-tokens 1024

# 複数検索デモ
python -m core.demo_search --mode multi

# トピック検索デモ
python -m core.demo_search "福祉DX" --mode topic

# ワークフロー統合デモ
python -m core.demo_search "介護業界の課題" --mode workflow
```

### Pythonコードで使用

```python
import asyncio
from agents import SearchAgent
from core import MemoryStore

async def main():
    memory = MemoryStore()
    search_agent = SearchAgent(memory_store=memory)

    # 検索を実行
    result = await search_agent.search(
        query="介護DXの最新トレンド",
        max_tokens=512
    )

    print(result["result"])

    # 使用統計を確認
    stats = await search_agent.get_usage_stats()
    print(f"Daily requests: {stats['perplexity_usage']['daily_requests']}")
    print(f"Monthly cost: ${stats['perplexity_usage']['monthly_cost']:.4f}")

asyncio.run(main())
```

### 環境変数の設定

```bash
# .envファイルに以下を設定
PERPLEXITY_API_KEY=your-actual-api-key
PERPLEXITY_MAX_REQUESTS_PER_DAY=50
PERPLEXITY_MAX_DOLLARS_PER_MONTH=5
```

## エージェントのLLM Router統合

すべてのエージェント（Generator, Analyzer, Compliance, Scheduler, Executor）がLLM Routerと統合されました。
**DRY_RUNモード（デフォルト）では、すべてのLLM呼び出しがモック化され、コストゼロで動作確認が可能です。**

### 統合されたエージェント

#### 1. Generator Agent
**LLM機能**: コンテンツ生成（SNS投稿、メール、レポート）

```python
from agents.generator_agent import GeneratorAgent

agent = GeneratorAgent()  # 自動的にLLM Routerを使用

# SNS投稿を生成
result = await agent.generate_content(
    content_type="sns_post",
    context={"topic": "AI Automation"},
    style="professional"
)
print(result["content"])  # DRY_RUNモードではモック応答
```

**デモスクリプト**:
```bash
python -m core.demo_generator  # コストゼロで動作確認
```

#### 2. Analyzer Agent
**LLM機能**: データ分析結果からのインサイト生成

```python
from agents.analyzer_agent import AnalyzerAgent

agent = AnalyzerAgent()  # 自動的にLLM Routerを使用

# データを分析
data = [{"date": "2024-01-01", "value": 100}, ...]
result = await agent.analyze_data(data, analysis_type="general")

print(result["insights"])  # LLMが生成したインサイト
```

**デモスクリプト**:
```bash
python -m core.demo_analyzer  # コストゼロで動作確認
```

#### 3. Compliance Agent
**LLM機能**: 有害コンテンツの高度な分析

```python
from agents.compliance_agent import ComplianceAgent

agent = ComplianceAgent()  # 自動的にLLM Routerを使用

# コンプライアンスチェック
result = await agent.check_compliance(
    content="Your content here",
    compliance_type="content_policy"
)

# LLMによる詳細分析が含まれる
if result["violations"]:
    for v in result["violations"]:
        print(v.get("llm_analysis", ""))
```

**デモスクリプト**:
```bash
python -m core.demo_compliance  # コストゼロで動作確認
```

#### 4. Scheduler Agent
**LLM機能**: タスクスケジュールの最適化提案

```python
from agents.scheduler_agent import SchedulerAgent

agent = SchedulerAgent()  # 自動的にLLM Routerを使用

# タスクをスケジュール
await agent.schedule_task(task_id="task_001", task_type="sns_post", priority=8)

# LLMを使ってスケジュールを最適化
optimization = await agent.optimize_schedule()
print(optimization["recommendations"])  # 最適化提案
```

**デモスクリプト**:
```bash
python -m core.demo_scheduler  # コストゼロで動作確認
```

#### 5. Executor Agent
**LLM機能**: タスク実行前の妥当性チェック

```python
from agents.executor_agent import ExecutorAgent

agent = ExecutorAgent()  # 自動的にLLM Routerを使用

task = {
    "task_id": "exec_001",
    "task_type": "api_call",
    "params": {"url": "https://api.example.com"}
}

# LLMでタスクを検証
validation = await agent.validate_task(task)
print(validation["analysis"])  # 妥当性分析

# タスクを実行
if validation["validated"]:
    result = await agent.execute_task(task)
```

**デモスクリプト**:
```bash
python -m core.demo_executor  # コストゼロで動作確認
```

### すべてのデモを一括実行

```bash
# 全エージェントのデモを実行（DRY_RUNモード、コスト$0.00）
python -m core.demo_generator
python -m core.demo_analyzer
python -m core.demo_compliance
python -m core.demo_scheduler
python -m core.demo_executor
```

### テストの実行

```bash
# LLM Router統合テスト（DRY_RUNモード）
pytest tests/test_agents_llm_integration.py -v

# 詳細出力付き
pytest tests/test_agents_llm_integration.py -v -s

# 特定のエージェントのみ
pytest tests/test_agents_llm_integration.py::TestGeneratorAgentIntegration -v
```

### LLM Router統合の利点

1. **ゼロコスト開発**: DRY_RUNモードでモック応答を使用
2. **統一されたインターフェース**: すべてのエージェントが同じLLM Routerを使用
3. **自動フォールバック**: プライマリプロバイダーが失敗時に自動切り替え
4. **予算管理**: 日次コスト上限の設定
5. **サーキットブレーカー**: 連続失敗時の自動停止
6. **レート制限**: プロバイダー別のリクエスト数制限

### 実API使用への切り替え

開発完了後、実際のLLM APIを使用する場合:

```bash
# .env
DRY_RUN=false                   # 実API使用
LLM_DAILY_MAX_COST_USD=10.0     # 日次予算を設定
```

## 24時間稼働 Runner

AI Multi-Agent Starter Kitには、継続的なタスク実行を管理する24時間稼働Runnerが組み込まれています。

### 特徴

- **DRY_RUNモード**: デフォルトでゼロコスト稼働
- **JSONL形式ログ**: `storage/runs/*.jsonl` に実行イベントを記録
- **自動レポート生成**: GitHub Actionsで毎日レポートを作成
- **REST API**: `/runner/status`, `/runner/run-now` エンドポイント
- **3種類のビルトインジョブ**:
  - **heartbeat**: 30秒ごとに生存確認
  - **cleanup**: 10分ごとに古いログを削除
  - **demo**: 5分ごとにデモタスクを実行

### クイックスタート

```bash
# 1. Runnerを有効化（デフォルトは無効）
export RUNNER_ENABLED=true
export DRY_RUN=true  # ゼロコスト稼働

# 2. Runnerを起動
python -m runner.main
```

### 環境変数

```bash
# .env
RUNNER_ENABLED=false              # Runnerの有効化
DRY_RUN=true                      # ゼロコストモード（推奨）

# ジョブ実行間隔（秒）
RUNNER_LOOP_INTERVAL=60           # メインループ
RUNNER_HEARTBEAT_SECONDS=30       # Heartbeat間隔
RUNNER_CLEANUP_SECONDS=600        # Cleanup間隔

# 並列実行とエラーハンドリング
RUNNER_MAX_CONCURRENCY=4          # 同時実行数
RUNNER_MAX_ERRORS=5               # 連続エラー上限
BACKOFF_BASE_SECONDS=2            # バックオフ基準（秒）
RUNNER_MAX_BACKOFF=300            # 最大バックオフ（秒）

# ウォッチドッグ
RUNNER_WATCHDOG_ENABLED=true      # ウォッチドッグ有効化
RUNNER_WATCHDOG_TIMEOUT=600       # タイムアウト（秒）

# レート制限
RUNNER_MAX_JOBS_PER_MINUTE=10     # 分間実行数上限
RUNNER_MAX_JOBS_PER_HOUR=100      # 時間実行数上限

# ストレージとログ
RUNNER_LOG_DIR=storage/runs       # ログディレクトリ
RUNNER_LOG_ROTATION_DAYS=30       # ログ保持期間（日）
RUNNER_SHUTDOWN_TIMEOUT=30        # シャットダウンタイムアウト（秒）
```

### REST API

#### GET /runner/status

Runnerのステータスを取得:

```bash
curl http://localhost:8000/runner/status
```

レスポンス例:
```json
{
  "enabled": true,
  "running": true,
  "consecutive_errors": 0,
  "jobs_executed_last_hour": 42,
  "registry_stats": {
    "total_jobs": 3,
    "enabled_jobs": 3,
    "jobs": [
      {
        "name": "heartbeat",
        "enabled": true,
        "run_count": 120,
        "error_count": 0
      }
    ]
  }
}
```

#### POST /runner/run-now

すべてのジョブを即座に実行:

```bash
curl -X POST http://localhost:8000/runner/run-now
```

### 朝のレポート生成

24時間分の実行イベントを集計してレポートを生成:

```bash
# 手動実行
python scripts/morning_report.py

# 出力
# - storage/reports/YYYY-MM-DD.md   (Markdownレポート)
# - storage/reports/YYYY-MM-DD.csv  (CSVデータ)
```

生成されるレポート内容:
- **サマリー**: 総イベント数、成功/エラー数、総実行時間
- **ジョブ別統計**: 実行回数、成功率、平均実行時間
- **エラー詳細**: エラーが発生した場合の詳細情報

### GitHub Actions自動レポート

毎日 9:00 JST に自動的にレポートを生成:

```yaml
# .github/workflows/runner-dry.yml
# - DRY_RUNモードで1分間Runnerを実行
# - レポート生成
# - GitHubリポジトリにコミット
# - Issueにサマリーを投稿
```

手動実行:
```bash
# GitHub ActionsからWorkflowを手動実行
Actions → Runner DRY Mode - Morning Report → Run workflow
```

### テストの実行

```bash
# Runnerのテスト（DRY_RUNモード）
pytest tests/test_runner_dry.py -v

# 特定のテストクラスのみ
pytest tests/test_runner_dry.py::TestRunner -v

# 統合テスト
pytest tests/test_runner_dry.py::TestIntegration -v
```

### ログファイル形式

すべてのジョブ実行イベントは `storage/runs/YYYY-MM-DD.jsonl` に記録:

```jsonl
{"timestamp": "2024-01-01T12:00:00", "job": "heartbeat", "status": "success", "duration_ms": 50, "dry_run": true, "result": {"status": "alive"}}
{"timestamp": "2024-01-01T12:05:00", "job": "demo", "status": "success", "duration_ms": 120, "dry_run": true, "result": {"task_id": "demo_task_20240101_120500"}}
```

### カスタムジョブの追加

新しいジョブを追加する方法:

```python
# runner/jobs.py に追加

async def my_custom_job() -> Dict[str, Any]:
    """カスタムジョブの実装"""
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if dry_run:
        # DRY_RUNモードの処理
        return {
            "status": "completed",
            "mode": "DRY_RUN",
            "cost": "$0.00",
            "message": "Custom job completed (DRY_RUN)"
        }
    else:
        # 実モードの処理
        return {
            "status": "completed",
            "mode": "REAL",
            "message": "Custom job completed"
        }

# ジョブを登録
default_registry.register(
    name="my_custom_job",
    func=my_custom_job,
    interval=3600,  # 1時間ごと
    enabled=True,
    description="My custom job"
)
```

### 実稼働への移行

DRY_RUNモードから実稼働に移行する場合:

```bash
# .env
DRY_RUN=false                     # 実API使用
RUNNER_ENABLED=true               # Runner有効化
LLM_DAILY_MAX_COST_USD=10.0       # 日次予算を設定

# Runnerを起動
python -m runner.main
```

**注意**: 実稼働モードでは実際のLLM APIが呼ばれるため、コストが発生します。予算設定を必ず確認してください。

---

## ダッシュボード & 通知

### Web Dashboard

ブラウザでRunnerの状態を可視化・操作できます。

```bash
# APIサーバーを起動
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000

# ブラウザでアクセス
# Local:      http://localhost:8000/dashboard
# Codespaces: https://{codespace-name}-8000.app.github.dev/dashboard
```

#### ダッシュボード機能

- **Runner Status**: 有効/実行中/エラー数を表示
- **Job Statistics**: 直近1時間の実行数、総ジョブ数
- **Recent Runs**: 最新20件の実行ログ（タイムスタンプ、ジョブ名、ステータス、実行時間）
- **Run Demo Now**: ボタンで全ジョブを手動実行
- **Auto-Refresh**: 30秒ごとに自動リロード

#### 使用例

```bash
# 1. Runnerを起動
export RUNNER_ENABLED=true
export DRY_RUN=true
python -m runner.main &

# 2. APIサーバーを起動
uvicorn api.server:app --reload &

# 3. ブラウザで http://localhost:8000/dashboard を開く

# 4. "Run Demo Now"ボタンをクリックして手動実行
```

### 通知システム

Morning Reportやアラートをメール/Slackに送信できます。

#### DRY_RUNモード（デフォルト）

外部に送信せず、`storage/notifications.jsonl`に記録のみ:

```bash
# テスト通知を送信
python scripts/send_test_notification.py

# 確認
cat storage/notifications.jsonl | jq .
```

#### 実運用モード

実際にメール/Slackに送信:

```bash
# .env
DRY_RUN=false
NOTIFY_CHANNELS=email,slack

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=your-email@gmail.com
SMTP_TO=recipient@example.com

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### Gmail App Passwordの取得

1. Googleアカウントにログイン
2. セキュリティ → 2段階認証を有効化
3. 「アプリパスワード」を生成
4. 生成されたパスワードを `SMTP_PASS` に設定

#### Slack Webhook URLの取得

1. https://api.slack.com/apps にアクセス
2. 「Create New App」→「From scratch」
3. 「Incoming Webhooks」を有効化
4. 「Add New Webhook to Workspace」でチャンネルを選択
5. 生成されたURLを `SLACK_WEBHOOK_URL` に設定

#### Morning Reportでの自動通知

`scripts/morning_report.py`は自動的に通知を送信:

```bash
# 手動実行
python scripts/morning_report.py

# GitHub Actionsで毎日 9:00 JST に自動実行
# .github/workflows/runner-dry.yml
```

通知内容:
- **件名**: `Daily Report - YYYY-MM-DD`
- **本文**: 総イベント数、成功/エラー数、レポートファイルパス

#### 環境変数

```bash
# .env
NOTIFY_CHANNELS=email,slack          # 通知チャネル（カンマ区切り）

# Email
SMTP_HOST=smtp.gmail.com             # SMTPサーバー
SMTP_PORT=587                        # SMTPポート
SMTP_USER=your-email@gmail.com       # SMTPユーザー
SMTP_PASS=your-app-password          # SMTPパスワード
SMTP_FROM=your-email@gmail.com       # 送信元アドレス
SMTP_TO=recipient@example.com        # 送信先アドレス

# Slack
SLACK_WEBHOOK_URL=https://...        # Slack Webhook URL

# Storage
NOTIFICATIONS_FILE=storage/notifications.jsonl  # DRY_RUN時の記録先
```

#### テストの実行

```bash
# ダッシュボードとNotifierのテスト
pytest tests/test_ui_notify.py -v

# 特定のテストのみ
pytest tests/test_ui_notify.py::TestDashboard -v
pytest tests/test_ui_notify.py::TestNotifier -v
```

### DRY → 実運用への切り替え

```bash
# 1. DRY_RUNモードで動作確認
export DRY_RUN=true
python scripts/send_test_notification.py

# 2. notifications.jsonlに記録されていることを確認
cat storage/notifications.jsonl | jq .

# 3. 通知設定を追加
# .envファイルに NOTIFY_CHANNELS, SMTP_*, SLACK_WEBHOOK_URL を設定

# 4. 実運用モードに切り替え
export DRY_RUN=false

# 5. テスト通知を送信（実際に送信される）
python scripts/send_test_notification.py
```

---

## 開発ガイド

### 新しいアプリケーションを追加

```bash
# 新しいアプリディレクトリを作成
mkdir -p apps/my_new_app

# __init__.pyとmain.pyを作成
touch apps/my_new_app/__init__.py
touch apps/my_new_app/main.py
```

```python
# apps/my_new_app/main.py
class MyNewApp:
    def __init__(self, agents, workflow, memory):
        self.agents = agents
        self.workflow = workflow
        self.memory = memory

    async def do_something(self, params):
        # アプリケーションロジック
        pass
```

### 新しいエージェントを追加

```python
# agents/my_agent.py
class MyAgent:
    def __init__(self, memory_store=None):
        self.memory = memory_store

    async def my_action(self, params):
        # エージェントロジック
        pass
```

### テストを追加

```bash
# テストファイルを作成
mkdir -p tests
touch tests/test_my_feature.py
```

```python
# tests/test_my_feature.py
import pytest

@pytest.mark.asyncio
async def test_my_feature():
    # テストコード
    assert True
```

## CI/CD

### 自動テスト（Codespaces Test）

プルリクエストやプッシュ時に自動的にテストが実行されます。

**`.github/workflows/codespaces-test.yml`** が以下をチェック：
- Python 構文チェック
- モジュールインポートテスト
- エージェント初期化テスト
- API サーバー起動テスト
- Docker Compose 設定検証

### 自動マージ（Claude PR用）

**`.github/workflows/auto-merge.yml`** が `claude/*` ブランチのPRを自動処理：
1. 基本的な検証テストを実行
2. PRを自動承認
3. Auto-merge を有効化（squash merge）
4. コメントを追加

**対象**: `claude/` で始まるブランチ名のPRのみ

### 夜間自動実行

毎晩午前2時（UTC）に定期タスクが自動実行されます。

### 自動デプロイ

mainブランチへのマージ時に自動的に本番環境にデプロイされます。

## 設定

### 環境変数

#### Codespaces の場合（推奨）

**自動生成**: GitHub Secrets から `.env` ファイルが自動生成されます。

リポジトリの **Settings → Secrets and variables → Codespaces** で設定：
- `OPENAI_API_KEY` (オプション - デフォルトで無効)
- `ANTHROPIC_API_KEY` (推奨 - 優先順位1位)
- `GEMINI_API_KEY` (推奨 - 優先順位2位)
- `PERPLEXITY_API_KEY` (推奨 - 優先順位3位)
- `OPENAI_ENABLED` (デフォルト: false)
- `LLM_PRIORITY` (デフォルト: anthropic,gemini,perplexity)
- `PERPLEXITY_MAX_REQUESTS_PER_DAY` (デフォルト: 50)
- `PERPLEXITY_MAX_DOLLARS_PER_MONTH` (デフォルト: 5)

#### ローカル環境の場合

`.env`ファイルを手動で作成：

```bash
# API Keys
OPENAI_API_KEY=your-key  # オプション
ANTHROPIC_API_KEY=your-key  # 推奨
GEMINI_API_KEY=your-key  # 推奨
PERPLEXITY_API_KEY=your-key  # 推奨

# LLM Configuration
OPENAI_ENABLED=false  # OpenAIをデフォルトで無効化
LLM_PRIORITY=anthropic,gemini,perplexity  # 優先順位

# Model Selection (optional)
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
GEMINI_MODEL=gemini-1.5-pro
PERPLEXITY_MODEL=llama-3.1-sonar-large-128k-online
OPENAI_MODEL=gpt-4

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/ai_agents
REDIS_URL=redis://redis:6379

# Perplexity Usage Limits
PERPLEXITY_MAX_REQUESTS_PER_DAY=50
PERPLEXITY_MAX_DOLLARS_PER_MONTH=5

# Applications
CARE_SCHEDULER_ENABLED=true
SNS_AUTO_ENABLED=true
HR_MATCHING_ENABLED=true
```

**注意**: `.env` ファイルは `.gitignore` に含まれています。API キーは絶対にコミットしないでください。

## LLM ルーター

### 概要

AI Multi-Agent Starter Kitは、複数のLLMプロバイダーをサポートし、優先順位に基づいて自動的に最適なプロバイダーを選定します。

### サポートするLLMプロバイダー

1. **Anthropic (Claude)** - 優先順位1位（デフォルト）
2. **Google Gemini** - 優先順位2位
3. **Perplexity** - 優先順位3位（検索タスクで優先）
4. **OpenAI (GPT)** - **デフォルトで無効**

### 優先順位のカスタマイズ

環境変数で優先順位を変更できます：

```bash
# .env または GitHub Secrets
LLM_PRIORITY=anthropic,gemini,perplexity
```

### OpenAIの有効化

OpenAIを使用する場合は、明示的に有効化が必要です：

```bash
OPENAI_ENABLED=true
LLM_PRIORITY=openai,anthropic,gemini,perplexity
```

### 使用例

```python
from core import get_llm_router

# LLMルーターを取得
llm_router = get_llm_router()

# テキスト生成
result = await llm_router.generate(
    prompt="介護DXの最新トレンドについて教えてください",
    max_tokens=512,
    temperature=0.7
)

print(result["result"])
print(f"使用したプロバイダー: {result['provider']}")

# 特定のプロバイダーを指定
result = await llm_router.generate(
    prompt="最新のAI技術について調べてください",
    preferred_provider="perplexity",  # Perplexityを優先
    task_type="search"
)

# 使用統計を確認
stats = llm_router.get_usage_stats()
print(f"総リクエスト数: {stats['total_requests']}")
print(f"プロバイダー別: {stats['by_provider']}")
```

### フォールバック機能

プライマリのLLMプロバイダーが利用できない場合、自動的に次の優先順位のプロバイダーにフォールバックします。

### タスク別の最適化

- **検索タスク** (`task_type="search"`): Perplexityを優先
- **一般タスク**: 設定された優先順位に従う

### 安全機能

#### 1. DRY_RUNモード（ゼロコスト運用）

**デフォルトで有効** - すべての外部API呼び出しをモック化し、実行コストをゼロに抑えます。

```bash
# .env
DRY_RUN=true                    # モックレスポンスを返す（デフォルト）
LLM_DAILY_MAX_COST_USD=0.0      # 日次予算を0に設定
PERPLEXITY_MAX_REQUESTS_PER_DAY=0  # Perplexity無効化
RUNNER_ENABLED=false            # バックグラウンド実行を無効化
```

**DRY_RUNモードの特徴:**
- ✅ すべてのLLM API呼び出しがモック化される
- ✅ 実際のAPIキーがなくても動作する
- ✅ コストが一切発生しない
- ✅ コード生成・検証・テストに最適
- ✅ Claude Code (Web) のクレジットのみで開発可能

**実際のAPI呼び出しに切り替える場合:**

```bash
# .env
DRY_RUN=false                   # 実際のAPI呼び出しを有効化
LLM_DAILY_MAX_COST_USD=5.0      # 日次予算を設定（例: $5/日）
PERPLEXITY_MAX_REQUESTS_PER_DAY=50  # Perplexity制限
RUNNER_ENABLED=true             # 必要に応じてRunner有効化
```

#### 2. 日次予算管理

LLMの使用コストを日次で制限します：

```bash
LLM_DAILY_MAX_COST_USD=5.0  # 1日あたり$5まで
```

予算に達すると自動的にAPI呼び出しを停止し、エラーを返します。翌日0時（UTC）に自動リセットされます。

#### 3. Perplexity検索専用モード

Perplexityを検索タスク専用に制限し、誤使用を防ぎます：

```bash
PERPLEXITY_SEARCH_ONLY=true  # デフォルト: true
```

この設定により、`task_type="search"` 以外でPerplexityが使用されることを防ぎます。

#### 4. サーキットブレーカー

プロバイダーが連続して5回失敗すると、5分間そのプロバイダーを使用停止にします。自動的に他のプロバイダーにフォールバックします。

#### 5. レート制限

プロバイダー別にリクエスト数を制限：
- **Anthropic**: 50リクエスト/分
- **Gemini**: 60リクエスト/分
- **Perplexity**: 20リクエスト/分
- **OpenAI**: 60リクエスト/分

#### 6. メモリリーク対策

24時間稼働を想定し、メモリ使用量を制限：
- 使用履歴: 最大1,000件（約150KB）
- リクエストタイムスタンプ: プロバイダーあたり100件

#### 使用統計の確認

```python
from core import get_llm_router

router = get_llm_router()
stats = router.get_usage_stats()

print(f"DRY_RUNモード: {stats['dry_run']}")
print(f"日次コスト: {stats['daily_cost_used']} / {stats['daily_cost_limit']}")
print(f"残り予算: {stats['budget_remaining']}")
print(f"総リクエスト: {stats['total_requests']}")
```

## ゼロコスト運用ガイド（推奨）

このプロジェクトは、**Claude Code (Web)** のクレジットのみを使用して、外部API課金なしで開発できるように設計されています。

### 基本方針

1. **DRY_RUN=true** をデフォルトで維持
2. すべてのLLM呼び出しはモック化
3. 実際のAPI呼び出しは本番環境のみ
4. 開発・テスト・コード生成は完全無料

### セットアップ手順

#### 1. GitHub Codespaces で起動

```bash
# Codespaces が自動的に .env を生成（DRY_RUN=true がデフォルト）
```

#### 2. コード生成のみで開発

```bash
# Claude Code (Web) でコード生成・編集
# すべてのエージェント実行はモック化される
# コストゼロ
```

#### 3. 動作確認

```bash
# モックレスポンスで動作確認
python -m core.demo_search "介護DXの最新トレンド"

# API経由でも確認可能（モック）
curl http://localhost:8000/api/v1/agents
```

#### 4. 本番環境のみ実API使用

```bash
# 本番環境の .env のみ
DRY_RUN=false
LLM_DAILY_MAX_COST_USD=10.0
RUNNER_ENABLED=true
```

### ゼロコスト開発の利点

- ✅ **完全無料**: 外部API課金なし
- ✅ **高速開発**: モックレスポンスで即座に動作確認
- ✅ **安全**: 誤ってAPIを大量消費する心配なし
- ✅ **テスト**: 実際のAPIキーなしでテスト可能
- ✅ **CI/CD**: GitHub Actionsでもコストゼロ

### モックレスポンス例

```python
result = await llm_router.generate(
    prompt="介護DXについて教えてください",
    task_type="search"
)

print(result)
# {
#   "status": "success",
#   "provider": "perplexity",
#   "result": "[MOCK SEARCH RESULT]\nProvider: perplexity\n...",
#   "dry_run": true,
#   "cost": "$0.00"
# }
```

## デプロイ

### Docker

```bash
docker build -f docker/Dockerfile -t ai-multi-agent .
docker run -p 8000:8000 ai-multi-agent
```

### Docker Compose

```bash
docker-compose -f docker/docker-compose.yml up -d
```

### Kubernetes

```bash
# 設定ファイルを適用
kubectl apply -f k8s/
```

## ロードマップ

- [x] コアエージェント実装
- [x] 基本アプリケーション（Care Scheduler, SNS Auto, HR Matching）
- [x] REST API
- [x] Docker対応
- [x] CI/CD パイプライン
- [ ] UIダッシュボード（Next.js）
- [ ] ベクトルDB統合（ChromaDB/Pinecone）
- [ ] リアルタイム通知（WebSocket）
- [ ] マルチテナント対応
- [ ] プラグインシステム

## コントリビューション

プルリクエストを歓迎します！

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## ライセンス

MIT License

## サポート

- Issues: [GitHub Issues](https://github.com/yourusername/ai-multi-agent-starter-kit/issues)
- Discussion: [GitHub Discussions](https://github.com/yourusername/ai-multi-agent-starter-kit/discussions)

---

Made with by AI Multi-Agent Team
