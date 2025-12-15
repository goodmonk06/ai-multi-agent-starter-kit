#!/usr/bin/env python3
"""
SNS投稿スケジューラー - 1週間分のSNS投稿を自動生成してスケジュール

使い方:
    python examples/schedule_sns_posts.py --topic "AI技術" --platform twitter

これで1週間分の投稿が自動生成されます。
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.sns_auto import SnsAutoApp
from agents import GeneratorAgent, ComplianceAgent, SchedulerAgent
from core import MemoryStore


async def main(topic: str, platform: str, days: int):
    print("=" * 60)
    print("📱 SNS投稿スケジューラー")
    print("=" * 60)
    print(f"トピック: {topic}")
    print(f"プラットフォーム: {platform}")
    print(f"投稿数: {days}日分")
    print()

    # エージェントとアプリを初期化
    memory = MemoryStore()
    agents = {
        "generator": GeneratorAgent(memory_store=memory),
        "compliance": ComplianceAgent(memory_store=memory),
        "scheduler": SchedulerAgent(memory_store=memory)
    }

    sns_app = SnsAutoApp(agents, None, memory)

    print("📝 投稿を生成中...")
    print()

    posts = []

    for i in range(days):
        # 投稿日時を計算（毎日午前9時）
        post_time = datetime.now() + timedelta(days=i+1)
        post_time = post_time.replace(hour=9, minute=0, second=0, microsecond=0)

        # 投稿を作成
        post = await sns_app.create_post(
            platform=platform,
            topic=f"{topic} - Day {i+1}",
            style="professional",
            hashtags=[topic.replace(" ", ""), "AI", "Tech"],
            schedule_time=post_time
        )

        posts.append(post)

        # 投稿内容を表示
        status_emoji = "✅" if post.get("status") == "approved" else "⚠️"
        print(f"{status_emoji} {i+1}日目 ({post_time.strftime('%Y-%m-%d %H:%M')})")
        print(f"   {post.get('content', '(生成中...)')[:80]}...")
        print()

    # サマリーを表示
    print("=" * 60)
    print("✅ 投稿スケジュール完了")
    print("=" * 60)
    print(f"総投稿数: {len(posts)}")
    print(f"承認済み: {sum(1 for p in posts if p.get('status') == 'approved')}")
    print(f"要確認: {sum(1 for p in posts if p.get('status') == 'needs_review')}")
    print()
    print("💡 次のステップ:")
    print("   1. メモリストアに保存された投稿を確認")
    print("   2. ダッシュボードでスケジュールを確認")
    print("   3. 必要に応じて投稿内容を編集")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SNS投稿スケジューラー")
    parser.add_argument(
        "--topic",
        type=str,
        default="AI技術の最新動向",
        help="投稿トピック"
    )
    parser.add_argument(
        "--platform",
        type=str,
        default="twitter",
        choices=["twitter", "facebook", "instagram", "linkedin"],
        help="SNSプラットフォーム"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="生成する日数（デフォルト: 7日）"
    )

    args = parser.parse_args()
    asyncio.run(main(args.topic, args.platform, args.days))
