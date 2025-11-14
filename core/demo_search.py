#!/usr/bin/env python
"""
Demo Search - SearchAgentのデモスクリプト

使用方法:
    python -m core.demo_search "介護DXの最新トレンド"
    python -m core.demo_search "AI エージェント 活用事例" --max-tokens 1024
"""

import asyncio
import sys
from typing import Optional
import structlog
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# ロギング設定
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger()


async def demo_simple_search(query: str, max_tokens: int = 512):
    """シンプルな検索デモ"""
    from agents.search_agent import SearchAgent
    from core import MemoryStore

    print("=" * 80)
    print("🔍 Perplexity Search Agent - Simple Search Demo")
    print("=" * 80)
    print(f"\nQuery: {query}")
    print(f"Max Tokens: {max_tokens}\n")

    # メモリとエージェントを初期化
    memory = MemoryStore()
    search_agent = SearchAgent(memory_store=memory)

    # 検索を実行
    print("⏳ Searching...")
    result = await search_agent.search(query, max_tokens=max_tokens)

    # 結果を表示
    print("\n" + "=" * 80)
    print("📊 Search Result")
    print("=" * 80)

    if result["status"] == "success":
        print(f"\n✅ Status: {result['status']}")
        print(f"🆔 Search ID: {result['search_id']}")
        print(f"📅 Timestamp: {result['timestamp']}\n")
        print("📝 Result:\n")
        print(result["result"])
    else:
        print(f"\n❌ Status: {result['status']}")
        print(f"🆔 Search ID: {result['search_id']}")
        print(f"📅 Timestamp: {result['timestamp']}\n")
        print(f"Error: {result.get('error', 'Unknown error')}\n")
        print(result["result"])

    # 使用統計を表示
    print("\n" + "=" * 80)
    print("📈 Usage Statistics")
    print("=" * 80)
    stats = await search_agent.get_usage_stats()
    print(f"\nTotal Searches: {stats['total_searches']}")
    print(f"Successful: {stats['successful_searches']}")
    print(f"Failed: {stats['failed_searches']}\n")

    perplexity_usage = stats['perplexity_usage']
    print(f"Daily Requests: {perplexity_usage['daily_requests']} / {perplexity_usage['max_requests_per_day']}")
    print(f"Requests Remaining Today: {perplexity_usage['requests_remaining_today']}")
    print(f"Monthly Cost: ${perplexity_usage['monthly_cost']:.4f} / ${perplexity_usage['max_dollars_per_month']:.2f}")
    print(f"Budget Remaining: ${perplexity_usage['budget_remaining']:.4f}\n")


async def demo_multi_search(queries: list[str], max_tokens: int = 512):
    """複数検索のデモ"""
    from agents.search_agent import SearchAgent
    from core import MemoryStore

    print("=" * 80)
    print("🔍 Perplexity Search Agent - Multi Search Demo")
    print("=" * 80)
    print(f"\nQueries: {len(queries)}")
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")
    print()

    # メモリとエージェントを初期化
    memory = MemoryStore()
    search_agent = SearchAgent(memory_store=memory)

    # 検索を実行
    print("⏳ Searching...")
    results = await search_agent.multi_search(queries, max_tokens=max_tokens)

    # 結果を表示
    for i, result in enumerate(results, 1):
        print("\n" + "=" * 80)
        print(f"📊 Search Result {i}/{len(results)}")
        print("=" * 80)

        if result["status"] == "success":
            print(f"\n✅ Query: {result['query']}")
            print(f"📝 Result:\n")
            print(result["result"][:500])  # 最初の500文字のみ表示
            if len(result["result"]) > 500:
                print("\n... (truncated)")
        else:
            print(f"\n❌ Query: {result['query']}")
            print(f"Error: {result.get('error', 'Unknown error')}")


async def demo_topic_search(topic: str):
    """トピック検索のデモ"""
    from agents.search_agent import SearchAgent
    from core import MemoryStore

    print("=" * 80)
    print("🔍 Perplexity Search Agent - Topic Search Demo")
    print("=" * 80)
    print(f"\nTopic: {topic}\n")

    # メモリとエージェントを初期化
    memory = MemoryStore()
    search_agent = SearchAgent(memory_store=memory)

    # トピック検索を実行
    aspects = ["最新動向", "メリット", "課題"]
    print(f"⏳ Searching topic from {len(aspects)} aspects...")
    print(f"Aspects: {', '.join(aspects)}\n")

    result = await search_agent.search_for_topic(topic, aspects=aspects)

    # 結果を表示
    print("\n" + "=" * 80)
    print("📊 Topic Search Result")
    print("=" * 80)

    print(f"\n📝 Integrated Summary:\n")
    print(result["summary"])


async def demo_workflow_integration(query: str):
    """ワークフロー統合のデモ"""
    from agents.search_agent import SearchAgent
    from agents import AnalyzerAgent, GeneratorAgent
    from core import MemoryStore, AgentWorkflow

    print("=" * 80)
    print("🔍 Perplexity Search Agent - Workflow Integration Demo")
    print("=" * 80)
    print(f"\nQuery: {query}\n")

    # メモリとエージェントを初期化
    memory = MemoryStore()
    agents = {
        "search": SearchAgent(memory_store=memory),
        "analyzer": AnalyzerAgent(memory_store=memory),
        "generator": GeneratorAgent(memory_store=memory)
    }

    # ワークフローを初期化
    workflow = AgentWorkflow(agents, memory, None)

    # ワークフローを定義
    workflow.define_workflow(
        "search_analyze_generate",
        [
            {
                "name": "search",
                "agent": "search",
                "action": "search",
                "params": {"query": query, "max_tokens": 512},
                "output_key": "search_result"
            },
            {
                "name": "analyze",
                "agent": "analyzer",
                "action": "analyze_data",
                "params": {
                    "data": ["$context.search_result.result"],
                    "analysis_type": "general"
                },
                "output_key": "analysis_result"
            }
        ]
    )

    # ワークフローを実行
    print("⏳ Running workflow: search → analyze...")
    workflow_result = await workflow.run_workflow("search_analyze_generate", {})

    # 結果を表示
    print("\n" + "=" * 80)
    print("📊 Workflow Result")
    print("=" * 80)

    print(f"\nStatus: {workflow_result['status']}")
    print(f"Steps Completed: {len(workflow_result['results'])}")

    for step_result in workflow_result['results']:
        print(f"\n--- {step_result['step']} ---")
        if step_result['result']['status'] == 'success':
            print("✅ Success")
        else:
            print(f"❌ Error: {step_result['result'].get('error', 'Unknown')}")


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Perplexity Search Agent Demo"
    )
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        default="介護DXの最新トレンド",
        help="Search query"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Maximum tokens for response"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["simple", "multi", "topic", "workflow"],
        default="simple",
        help="Demo mode"
    )

    args = parser.parse_args()

    try:
        if args.mode == "simple":
            asyncio.run(demo_simple_search(args.query, args.max_tokens))

        elif args.mode == "multi":
            queries = [
                "介護DXの最新トレンド",
                "AIエージェントの活用事例",
                "業務自動化のベストプラクティス"
            ]
            asyncio.run(demo_multi_search(queries, args.max_tokens))

        elif args.mode == "topic":
            asyncio.run(demo_topic_search(args.query))

        elif args.mode == "workflow":
            asyncio.run(demo_workflow_integration(args.query))

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        logger.error("Demo failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
