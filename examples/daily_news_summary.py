#!/usr/bin/env python3
"""
毎日のニュース要約 - 指定したトピックの最新ニュースを要約してSlack/Emailで送信

使い方:
    # デフォルトトピック（AI関連）で実行
    python examples/daily_news_summary.py

    # カスタムトピックで実行
    python examples/daily_news_summary.py --topic "介護DX"

GitHub Actionsで毎朝7時に自動実行する設定も可能です。
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import SearchAgent, AnalyzerAgent
from core import MemoryStore
from core.notifier import send_notification


async def main(topic: str = "AI エージェント 最新動向"):
    print("=" * 60)
    print("📰 毎日のニュース要約")
    print("=" * 60)
    print(f"トピック: {topic}")
    print()

    # エージェントを初期化
    memory = MemoryStore()
    search_agent = SearchAgent(memory_store=memory)
    analyzer_agent = AnalyzerAgent(memory_store=memory)

    try:
        # 1. ニュースを検索
        print("🔍 最新ニュースを検索中...")
        search_result = await search_agent.search(
            query=f"{topic} 最新ニュース {datetime.now().strftime('%Y年%m月')}",
            max_tokens=1024
        )

        if search_result["status"] != "success":
            print(f"❌ 検索失敗: {search_result.get('message')}")
            return

        news_content = search_result["result"]
        print(f"✓ ニュース取得完了（{len(news_content)} 文字）")
        print()

        # 2. 要約を生成
        print("📊 ニュースを分析・要約中...")
        analysis_result = await analyzer_agent.analyze_data(
            data=[{
                "content": news_content,
                "topic": topic,
                "date": datetime.now().isoformat()
            }],
            analysis_type="summary"
        )

        summary = analysis_result.get("analysis", {}).get("summary", "要約を生成できませんでした")
        print("✓ 要約完成")
        print()

        # 3. 通知を作成して送信
        subject = f"📰 {topic} - 本日のニュース要約"

        body = f"""
{topic} の最新ニュース要約

{summary}

---
詳細情報:
{news_content[:500]}...

---
生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
AI Multi-Agent Starter Kit
"""

        print("📤 通知を送信中...")
        notification_result = await send_notification(
            subject=subject,
            body=body,
            topic=topic
        )

        if notification_result.get("dry_run"):
            print("🔵 DRY_RUNモード: 通知を記録しました")
            print()
            print("📄 要約プレビュー:")
            print("-" * 60)
            print(summary)
            print("-" * 60)
        else:
            print("✅ 通知を送信しました！")

        print()
        print("=" * 60)
        print("✅ 完了")
        print("=" * 60)

    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="毎日のニュース要約")
    parser.add_argument(
        "--topic",
        type=str,
        default="AI エージェント 最新動向",
        help="検索するトピック（デフォルト: AI エージェント 最新動向）"
    )

    args = parser.parse_args()
    asyncio.run(main(args.topic))
