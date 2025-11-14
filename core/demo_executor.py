"""
Executor Agent Demo - DRY_RUNモードでの動作確認

使い方:
    python -m core.demo_executor

DRY_RUNモードでは、実際のLLM APIを呼ばずにモックレスポンスを返します。
コストゼロで動作確認が可能です。
"""

import asyncio
import structlog
from agents.executor_agent import ExecutorAgent

logger = structlog.get_logger()


async def demo_simple_execution():
    """シンプルなタスク実行のデモ"""
    print("\n" + "="*60)
    print("⚡ Executor Agent Demo - Simple Task Execution")
    print("="*60 + "\n")

    agent = ExecutorAgent()

    task = {
        "task_id": "exec_001",
        "task_type": "generic",
        "action": "process_data",
        "params": {"input": "test_data", "operation": "transform"}
    }

    print("📝 Executing task...")
    print(f"Task ID: {task['task_id']}")
    print(f"Task Type: {task['task_type']}\n")

    result = await agent.execute_task(task)

    print("✅ Execution Result:")
    print(f"  Task ID: {result['task_id']}")
    print(f"  Status: {result['status']}")
    print(f"  Duration: {result.get('duration_seconds', 0):.3f}s")
    print(f"  Start Time: {result['start_time']}")
    print(f"  End Time: {result['end_time']}")


async def demo_api_call_execution():
    """API呼び出しタスクのデモ"""
    print("\n" + "="*60)
    print("🌐 Executor Agent Demo - API Call Execution")
    print("="*60 + "\n")

    agent = ExecutorAgent()

    task = {
        "task_id": "api_call_001",
        "task_type": "api_call",
        "api_config": {
            "method": "GET",
            "url": "https://api.example.com/data",
            "params": {"limit": 100}
        }
    }

    print("📝 Executing API call task...")
    print(f"URL: {task['api_config']['url']}")
    print(f"Method: {task['api_config']['method']}\n")

    result = await agent.execute_task(task)

    print("✅ Execution Result:")
    print(f"  Status: {result['status']}")
    print(f"  Result: {result.get('result', {})}")
    print(f"  Duration: {result.get('duration_seconds', 0):.3f}s")


async def demo_workflow_execution():
    """ワークフロー実行のデモ"""
    print("\n" + "="*60)
    print("🔄 Executor Agent Demo - Workflow Execution")
    print("="*60 + "\n")

    agent = ExecutorAgent()

    workflow_task = {
        "task_id": "workflow_001",
        "task_type": "workflow",
        "workflow_steps": [
            {
                "task_id": "step_1",
                "task_type": "data_processing",
                "operation": "transform",
                "data": [{"id": 1}, {"id": 2}]
            },
            {
                "task_id": "step_2",
                "task_type": "data_processing",
                "operation": "validate",
                "data": [{"id": 1}, {"id": 2}]
            }
        ]
    }

    print("📝 Executing workflow...")
    print(f"Workflow ID: {workflow_task['task_id']}")
    print(f"Steps: {len(workflow_task['workflow_steps'])}\n")

    result = await agent.execute_task(workflow_task)

    print("✅ Workflow Result:")
    print(f"  Status: {result['status']}")

    if result['status'] == 'completed':
        workflow_result = result.get('result', {})
        print(f"  Workflow Completed: {workflow_result.get('workflow_completed', False)}")
        print(f"  Steps Executed: {workflow_result.get('steps_executed', 0)}")
        print(f"  Duration: {result.get('duration_seconds', 0):.3f}s")


async def demo_data_processing():
    """データ処理タスクのデモ"""
    print("\n" + "="*60)
    print("📊 Executor Agent Demo - Data Processing")
    print("="*60 + "\n")

    agent = ExecutorAgent()

    task = {
        "task_id": "data_proc_001",
        "task_type": "data_processing",
        "operation": "transform",
        "data": [
            {"id": 1, "name": "item_1", "value": 100},
            {"id": 2, "name": "item_2", "value": 200},
            {"id": 3, "name": "item_3", "value": 150},
        ]
    }

    print("📝 Processing data...")
    print(f"Records: {len(task['data'])}")
    print(f"Operation: {task['operation']}\n")

    result = await agent.execute_task(task)

    print("✅ Processing Result:")
    print(f"  Status: {result['status']}")

    if result['status'] == 'completed':
        proc_result = result.get('result', {})
        print(f"  Processed Count: {proc_result.get('processed_count', 0)}")
        print(f"  Duration: {result.get('duration_seconds', 0):.3f}s")


async def demo_parallel_execution():
    """並列実行のデモ"""
    print("\n" + "="*60)
    print("⚡ Executor Agent Demo - Parallel Execution")
    print("="*60 + "\n")

    agent = ExecutorAgent()

    tasks = [
        {
            "task_id": f"parallel_task_{i}",
            "task_type": "generic",
            "action": "process",
            "params": {"item_id": i}
        }
        for i in range(5)
    ]

    print(f"📝 Executing {len(tasks)} tasks in parallel...\n")

    results = await agent.execute_parallel(tasks)

    print("✅ Parallel Execution Results:")
    print(f"  Total Tasks: {len(results)}")

    completed = sum(1 for r in results if r.get('status') == 'completed')
    failed = sum(1 for r in results if r.get('status') == 'failed')

    print(f"  Completed: {completed}")
    print(f"  Failed: {failed}")

    total_duration = sum(r.get('duration_seconds', 0) for r in results if 'duration_seconds' in r)
    print(f"  Total Duration: {total_duration:.3f}s")


async def demo_task_validation():
    """タスク妥当性チェックのデモ"""
    print("\n" + "="*60)
    print("✅ Executor Agent Demo - Task Validation")
    print("="*60 + "\n")

    agent = ExecutorAgent()

    task = {
        "task_id": "validation_test_001",
        "task_type": "api_call",
        "params": {
            "url": "https://api.example.com/data",
            "method": "POST",
            "timeout": 30
        }
    }

    print("📝 Validating task before execution...")
    print(f"Task ID: {task['task_id']}")
    print(f"Task Type: {task['task_type']}\n")

    validation_result = await agent.validate_task(task)

    print("✅ Validation Result:")
    print(f"  Validated: {validation_result['validated']}")
    print(f"  Task ID: {validation_result['task_id']}")

    if validation_result['validated']:
        print(f"\n  💡 Analysis:")
        analysis = validation_result.get('analysis', '')
        print(f"  {analysis[:300]}...")

    print(f"\n  Timestamp: {validation_result['timestamp']}")


async def demo_execution_stats():
    """実行統計のデモ"""
    print("\n" + "="*60)
    print("📊 Executor Agent Demo - Execution Statistics")
    print("="*60 + "\n")

    agent = ExecutorAgent()

    # いくつかのタスクを実行
    print("📝 Executing sample tasks...\n")

    tasks = [
        {"task_id": f"stats_task_{i}", "task_type": "generic", "action": "test"}
        for i in range(10)
    ]

    for task in tasks[:5]:
        await agent.execute_task(task)

    # 統計を取得
    stats = await agent.get_execution_stats()

    print("✅ Execution Statistics:")
    print(f"  Total Executions: {stats['total_executions']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success Rate: {stats['success_rate']*100:.1f}%")
    print(f"  Average Duration: {stats['average_duration_seconds']:.3f}s")
    print(f"  Currently Running: {stats['currently_running']}")


async def main():
    """すべてのデモを実行"""
    print("\n" + "="*60)
    print("🎯 Executor Agent - Comprehensive Demo")
    print("   DRY_RUN Mode: All LLM calls are mocked ($0.00 cost)")
    print("="*60)

    try:
        await demo_simple_execution()
        await demo_api_call_execution()
        await demo_workflow_execution()
        await demo_data_processing()
        await demo_parallel_execution()
        await demo_task_validation()
        await demo_execution_stats()

        print("\n" + "="*60)
        print("✅ All demos completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        logger.error("Demo failed", error=str(e))
        print(f"\n❌ Demo failed: {str(e)}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
