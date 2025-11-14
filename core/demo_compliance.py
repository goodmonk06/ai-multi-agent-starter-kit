"""
Compliance Agent Demo - DRY_RUNモードでの動作確認

使い方:
    python -m core.demo_compliance

DRY_RUNモードでは、実際のLLM APIを呼ばずにモックレスポンスを返します。
コストゼロで動作確認が可能です。
"""

import asyncio
import structlog
from agents.compliance_agent import ComplianceAgent

logger = structlog.get_logger()


async def demo_text_compliance():
    """テキストコンプライアンスチェックのデモ"""
    print("\n" + "="*60)
    print("🔒 Compliance Agent Demo - Text Compliance Check")
    print("="*60 + "\n")

    agent = ComplianceAgent()

    # 正常なテキスト
    safe_content = "This is a professional message about AI technology and automation."

    print("📝 Checking safe content...")
    print(f"Content: {safe_content}\n")

    result = await agent.check_compliance(safe_content, compliance_type="content_policy")

    print("✅ Compliance Check Results:")
    print(f"  Passed: {result['passed']}")
    print(f"  Violations: {len(result['violations'])}")
    print(f"  Warnings: {len(result['warnings'])}")
    print(f"  Timestamp: {result['timestamp']}")


async def demo_pii_detection():
    """PII（個人情報）検出のデモ"""
    print("\n" + "="*60)
    print("🛡️ Compliance Agent Demo - PII Detection")
    print("="*60 + "\n")

    agent = ComplianceAgent()

    # PIIを含むテキスト（テスト用）
    pii_content = "Contact us at: test-email@example.com or call 123-45-6789"

    print("📝 Checking content for PII...")
    print(f"Content: {pii_content}\n")

    result = await agent.check_compliance(pii_content, compliance_type="gdpr")

    print("✅ PII Detection Results:")
    print(f"  Passed: {result['passed']}")
    print(f"  Violations Found: {len(result['violations'])}")

    if result['violations']:
        for violation in result['violations']:
            print(f"\n    ⚠️  {violation['type']}")
            print(f"        Severity: {violation['severity']}")
            print(f"        Message: {violation['message']}")

    print(f"\n  Timestamp: {result['timestamp']}")


async def demo_harmful_content():
    """有害コンテンツチェックのデモ"""
    print("\n" + "="*60)
    print("⚠️ Compliance Agent Demo - Harmful Content Check")
    print("="*60 + "\n")

    agent = ComplianceAgent()

    # 有害なキーワードを含むテキスト（テスト用）
    harmful_content = "This message contains keywords related to violence and hate."

    print("📝 Checking for harmful content...")
    print(f"Content: {harmful_content}\n")

    result = await agent.check_compliance(harmful_content, compliance_type="content_policy")

    print("✅ Harmful Content Check Results:")
    print(f"  Passed: {result['passed']}")
    print(f"  Violations Found: {len(result['violations'])}")

    if result['violations']:
        for violation in result['violations']:
            print(f"\n    ⚠️  {violation['type']}")
            print(f"        Keyword: {violation.get('keyword', 'N/A')}")
            print(f"        Severity: {violation['severity']}")

            if 'llm_analysis' in violation:
                print(f"        LLM Analysis: {violation['llm_analysis'][:100]}...")

    print(f"\n  Timestamp: {result['timestamp']}")


async def demo_data_compliance():
    """データコンプライアンスチェックのデモ"""
    print("\n" + "="*60)
    print("📋 Compliance Agent Demo - Data Compliance Check")
    print("="*60 + "\n")

    agent = ComplianceAgent()

    # GDPRデータ（不完全）
    data = {
        "user_id": "user_123",
        "name": "Test User",
        # "consent": True,  # 必須フィールドが欠落
        # "data_subject_id": "ds_456"  # 必須フィールドが欠落
    }

    print("📝 Checking data compliance...")
    print(f"Data: {data}\n")

    result = await agent.check_compliance(data, compliance_type="gdpr")

    print("✅ Data Compliance Results:")
    print(f"  Passed: {result['passed']}")
    print(f"  Violations: {len(result['violations'])}")

    if result['violations']:
        for violation in result['violations']:
            print(f"\n    ⚠️  {violation['type']}")
            if 'fields' in violation:
                print(f"        Missing Fields: {violation['fields']}")
            print(f"        Severity: {violation['severity']}")

    if result['warnings']:
        print(f"\n  Warnings: {len(result['warnings'])}")
        for warning in result['warnings']:
            print(f"    - {warning['type']}: {warning.get('message', 'N/A')}")

    print(f"\n  Timestamp: {result['timestamp']}")


async def main():
    """すべてのデモを実行"""
    print("\n" + "="*60)
    print("🎯 Compliance Agent - Comprehensive Demo")
    print("   DRY_RUN Mode: All LLM calls are mocked ($0.00 cost)")
    print("="*60)

    try:
        await demo_text_compliance()
        await demo_pii_detection()
        await demo_harmful_content()
        await demo_data_compliance()

        print("\n" + "="*60)
        print("✅ All demos completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        logger.error("Demo failed", error=str(e))
        print(f"\n❌ Demo failed: {str(e)}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
