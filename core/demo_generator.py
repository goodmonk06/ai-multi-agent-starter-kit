"""
Generator Agent Demo - DRY_RUNモードでの動作確認

使い方:
    python -m core.demo_generator

DRY_RUNモードでは、実際のLLM APIを呼ばずにモックレスポンスを返します。
コストゼロで動作確認が可能です。
"""

import asyncio
import structlog
from agents.generator_agent import GeneratorAgent

logger = structlog.get_logger()


async def demo_sns_post():
    """SNS投稿生成のデモ"""
    print("\n" + "="*60)
    print("🚀 Generator Agent Demo - SNS Post Generation")
    print("="*60 + "\n")

    agent = GeneratorAgent()

    context = {
        "topic": "AI Multi-Agent Systems",
        "platform": "twitter",
        "audience": "tech professionals",
        "tone": "informative and engaging",
        "key_points": [
            "Multi-agent systems enable complex task automation",
            "LLM routers provide intelligent provider selection",
            "DRY_RUN mode allows zero-cost development"
        ]
    }

    print("📝 Generating SNS post...")
    print(f"Context: {context}\n")

    result = await agent.generate_content(
        content_type="sns_post",
        context=context,
        style="professional",
        max_length=280
    )

    print("✅ Generated Content:")
    print(f"  Type: {result['type']}")
    print(f"  Style: {result['style']}")
    print(f"  Length: {result['character_count']} characters")
    print(f"\n  Content:\n  {result['content'][:500]}\n")

    if "hashtags" in result:
        print(f"  Hashtags: {result['hashtags']}")

    print(f"  Timestamp: {result['timestamp']}")


async def demo_email():
    """メール生成のデモ"""
    print("\n" + "="*60)
    print("📧 Generator Agent Demo - Email Generation")
    print("="*60 + "\n")

    agent = GeneratorAgent()

    context = {
        "subject": "Project Update - AI Agent Integration",
        "recipient": "team@example.com",
        "key_points": [
            "Successfully integrated LLM Router with all agents",
            "DRY_RUN mode is now operational",
            "Ready for Phase 2 implementation"
        ]
    }

    print("📝 Generating email...")
    print(f"Subject: {context['subject']}")
    print(f"Recipient: {context['recipient']}\n")

    result = await agent.generate_content(
        content_type="email",
        context=context,
        style="professional"
    )

    print("✅ Generated Email:")
    print(f"  Subject: {result['subject']}")
    print(f"  Body:\n  {result['body'][:500]}\n")
    print(f"  Timestamp: {result['timestamp']}")


async def demo_report():
    """レポート生成のデモ"""
    print("\n" + "="*60)
    print("📊 Generator Agent Demo - Report Generation")
    print("="*60 + "\n")

    agent = GeneratorAgent()

    context = {
        "title": "Phase 1 Implementation Report",
        "data": {
            "agents_integrated": 5,
            "demo_scripts_created": 5,
            "dry_run_mode": "enabled",
            "api_cost": "$0.00"
        }
    }

    print("📝 Generating report...")
    print(f"Title: {context['title']}\n")

    result = await agent.generate_content(
        content_type="report",
        context=context
    )

    print("✅ Generated Report:")
    print(f"  Title: {result['title']}")
    print(f"  Content:\n  {result['content'][:500]}...")
    print(f"\n  Sections: {len(result.get('sections', []))}")
    print(f"  Timestamp: {result['timestamp']}")


async def main():
    """すべてのデモを実行"""
    print("\n" + "="*60)
    print("🎯 Generator Agent - Comprehensive Demo")
    print("   DRY_RUN Mode: All LLM calls are mocked ($0.00 cost)")
    print("="*60)

    try:
        await demo_sns_post()
        await demo_email()
        await demo_report()

        print("\n" + "="*60)
        print("✅ All demos completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        logger.error("Demo failed", error=str(e))
        print(f"\n❌ Demo failed: {str(e)}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
