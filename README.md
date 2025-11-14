# AI Multi-Agent Starter Kit

多エージェントAIシステムのための基盤フレームワーク - 福祉DX、SNS自動化、採用、経営分析など、あらゆる業務自動化に対応できる"基礎OS"

## 概要

AI Multi-Agent Starter Kitは、LangGraphをベースにした多エージェントシステムの構築を高速化するフレームワークです。複数の専門エージェントが協調して動作し、複雑なビジネスプロセスを自動化します。

### 主な特徴

- **モジュラーアーキテクチャ**: apps/配下に新しいアプリケーションを簡単に追加可能
- **LangGraphベース**: 強力なワークフローエンジン
- **共有メモリ**: エージェント間でデータを共有
- **インテリジェントルーティング**: タスクを最適なエージェントに自動振り分け
- **自動スケーリング**: Docker/Kubernetesで簡単にデプロイ
- **CI/CD対応**: GitHub Actionsで自動テスト・デプロイ

## プロジェクト構造

```
ai-multi-agent-starter-kit/
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
│   └── docker-compose.yml
│
└── .github/workflows/      # CI/CD
    ├── nightly-run.yml     # 夜間自動実行
    ├── codegen.yml         # コード自動生成
    └── deploy.yml          # 自動デプロイ
```

## クイックスタート

### 1. 環境セットアップ

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

### 2. Dockerで起動

```bash
# Docker Composeで全サービスを起動
cd docker
docker-compose up -d

# ヘルスチェック
curl http://localhost:8000/health
```

### 3. APIサーバーを起動（開発モード）

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

### 自動テスト

プルリクエストやプッシュ時に自動的にテストが実行されます。

### 夜間自動実行

毎晩午前2時（UTC）に定期タスクが自動実行されます。

### 自動デプロイ

mainブランチへのマージ時に自動的に本番環境にデプロイされます。

## 設定

### 環境変数

`.env`ファイルで以下の環境変数を設定：

```bash
# API Keys
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key

# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Applications
CARE_SCHEDULER_ENABLED=true
SNS_AUTO_ENABLED=true
HR_MATCHING_ENABLED=true
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
