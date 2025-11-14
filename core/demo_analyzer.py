"""
Analyzer Agent Demo - DRY_RUNモードでの動作確認

使い方:
    python -m core.demo_analyzer

DRY_RUNモードでは、実際のLLM APIを呼ばずにモックレスポンスを返します。
コストゼロで動作確認が可能です。
"""

import asyncio
import structlog
from agents.analyzer_agent import AnalyzerAgent

logger = structlog.get_logger()


async def demo_general_analysis():
    """一般的なデータ分析のデモ"""
    print("\n" + "="*60)
    print("📊 Analyzer Agent Demo - General Analysis")
    print("="*60 + "\n")

    agent = AnalyzerAgent()

    # サンプルデータ
    data = [
        {"date": "2024-01-01", "requests": 120, "cost": 0.50, "provider": "anthropic"},
        {"date": "2024-01-02", "requests": 150, "cost": 0.60, "provider": "anthropic"},
        {"date": "2024-01-03", "requests": 95, "cost": 0.40, "provider": "gemini"},
        {"date": "2024-01-04", "requests": 180, "cost": 0.70, "provider": "anthropic"},
        {"date": "2024-01-05", "requests": 140, "cost": 0.55, "provider": "gemini"},
    ]

    print("📝 Analyzing data...")
    print(f"Records: {len(data)}")
    print(f"Sample: {data[0]}\n")

    result = await agent.analyze_data(data, analysis_type="general")

    print("✅ Analysis Results:")
    print(f"  Record Count: {result['record_count']}")
    print(f"  Columns: {result['columns']}")
    print(f"  Timestamp: {result['timestamp']}")

    if "insights" in result and result["insights"]:
        print(f"\n  💡 Insights:")
        for i, insight in enumerate(result["insights"][:5], 1):
            print(f"    {i}. {insight}")


async def demo_trend_analysis():
    """トレンド分析のデモ"""
    print("\n" + "="*60)
    print("📈 Analyzer Agent Demo - Trend Analysis")
    print("="*60 + "\n")

    agent = AnalyzerAgent()

    # 時系列データ
    data = [
        {"timestamp": "2024-01-01T00:00:00", "value": 100},
        {"timestamp": "2024-01-01T06:00:00", "value": 120},
        {"timestamp": "2024-01-01T12:00:00", "value": 150},
        {"timestamp": "2024-01-01T18:00:00", "value": 130},
        {"timestamp": "2024-01-02T00:00:00", "value": 140},
    ]

    print("📝 Analyzing trends...")
    print(f"Records: {len(data)}\n")

    result = await agent.analyze_data(data, analysis_type="trend")

    print("✅ Trend Analysis Results:")
    print(f"  Trend Type: {result['trend_type']}")
    print(f"  Patterns Detected: {len(result['patterns'])}")

    if result['patterns']:
        for pattern in result['patterns']:
            print(f"    - {pattern['type']}: {pattern['description']}")

    print(f"  Timestamp: {result['timestamp']}")


async def demo_anomaly_detection():
    """異常検知のデモ"""
    print("\n" + "="*60)
    print("🔍 Analyzer Agent Demo - Anomaly Detection")
    print("="*60 + "\n")

    agent = AnalyzerAgent()

    # 外れ値を含むデータ
    data = [
        {"id": 1, "value": 100, "status": "normal"},
        {"id": 2, "value": 105, "status": "normal"},
        {"id": 3, "value": 98, "status": "normal"},
        {"id": 4, "value": 500, "status": "anomaly"},  # 外れ値
        {"id": 5, "value": 102, "status": "normal"},
        {"id": 6, "value": -50, "status": "anomaly"},  # 外れ値
    ]

    print("📝 Detecting anomalies...")
    print(f"Records: {len(data)}\n")

    result = await agent.analyze_data(data, analysis_type="anomaly")

    print("✅ Anomaly Detection Results:")
    print(f"  Severity: {result['severity']}")
    print(f"  Anomalies Detected: {len(result['anomalies_detected'])}")

    if result['anomalies_detected']:
        for anomaly in result['anomalies_detected']:
            print(f"    - Column: {anomaly['column']}")
            print(f"      Count: {anomaly['count']}")
            print(f"      Values: {anomaly['values'][:3]}")

    print(f"  Timestamp: {result['timestamp']}")


async def demo_predictive_analysis():
    """予測分析のデモ"""
    print("\n" + "="*60)
    print("🔮 Analyzer Agent Demo - Predictive Analysis")
    print("="*60 + "\n")

    agent = AnalyzerAgent()

    # 予測用データ
    data = [
        {"date": "2024-01-01", "value": 100},
        {"date": "2024-01-02", "value": 110},
        {"date": "2024-01-03", "value": 115},
        {"date": "2024-01-04", "value": 120},
        {"date": "2024-01-05", "value": 125},
    ]

    print("📝 Performing predictive analysis...")
    print(f"Records: {len(data)}\n")

    result = await agent.analyze_data(data, analysis_type="predictive")

    print("✅ Predictive Analysis Results:")
    print(f"  Model: {result['model']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Predictions: {len(result['predictions'])}")

    if result['predictions']:
        for pred in result['predictions']:
            print(f"    - Next Value: {pred.get('next_value', 'N/A')}")
            print(f"      Method: {pred.get('method', 'N/A')}")

    print(f"  Timestamp: {result['timestamp']}")


async def main():
    """すべてのデモを実行"""
    print("\n" + "="*60)
    print("🎯 Analyzer Agent - Comprehensive Demo")
    print("   DRY_RUN Mode: All LLM calls are mocked ($0.00 cost)")
    print("="*60)

    try:
        await demo_general_analysis()
        await demo_trend_analysis()
        await demo_anomaly_detection()
        await demo_predictive_analysis()

        print("\n" + "="*60)
        print("✅ All demos completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        logger.error("Demo failed", error=str(e))
        print(f"\n❌ Demo failed: {str(e)}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
