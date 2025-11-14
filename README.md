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
