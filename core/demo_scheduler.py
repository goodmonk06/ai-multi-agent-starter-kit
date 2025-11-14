"""
Scheduler Agent Demo - DRY_RUNモードでの動作確認

使い方:
    python -m core.demo_scheduler

DRY_RUNモードでは、実際のLLM APIを呼ばずにモックレスポンスを返します。
コストゼロで動作確認が可能です。
"""

import asyncio
import structlog
from datetime import datetime, timedelta
from agents.scheduler_agent import SchedulerAgent

logger = structlog.get_logger()


async def demo_task_scheduling():
    """タスクスケジューリングのデモ"""
    print("\n" + "="*60)
    print("📅 Scheduler Agent Demo - Task Scheduling")
    print("="*60 + "\n")

    agent = SchedulerAgent()

    # 複数のタスクをスケジュール
    tasks = [
        {
            "task_id": "task_001",
            "task_type": "sns_post",
            "priority": 8,
            "deadline": datetime.now() + timedelta(hours=2),
            "metadata": {"platform": "twitter"}
        },
        {
            "task_id": "task_002",
            "task_type": "data_analysis",
            "priority": 5,
            "deadline": datetime.now() + timedelta(days=1),
            "metadata": {"dataset": "user_metrics"}
        },
        {
            "task_id": "task_003",
            "task_type": "compliance_check",
            "priority": 9,
            "deadline": datetime.now() + timedelta(hours=1),
            "metadata": {"content_type": "email"}
        },
    ]

    print("📝 Scheduling tasks...")
    for task in tasks:
        result = await agent.schedule_task(**task)
        print(f"  ✅ Scheduled: {result['task_id']} (Priority: {result['priority']})")

    print(f"\n  Total tasks scheduled: {len(tasks)}")


async def demo_task_retrieval():
    """タスク取得のデモ"""
    print("\n" + "="*60)
    print("📥 Scheduler Agent Demo - Task Retrieval")
    print("="*60 + "\n")

    agent = SchedulerAgent()

    # タスクをスケジュール
    await agent.schedule_task(
        task_id="task_high_priority",
        task_type="report_generation",
        priority=10,
        deadline=datetime.now() + timedelta(minutes=30)
    )

    await agent.schedule_task(
        task_id="task_low_priority",
        task_type="email_send",
        priority=3,
        deadline=datetime.now() + timedelta(days=2)
    )

    print("📝 Retrieving next task...")
    next_task = await agent.get_next_task()

    if next_task:
        print(f"\n  ✅ Next Task:")
        print(f"    ID: {next_task['task_id']}")
        print(f"    Type: {next_task['task_type']}")
        print(f"    Priority: {next_task['priority']}")
        print(f"    Status: {next_task['status']}")
        print(f"    Deadline: {next_task['deadline']}")


async def demo_task_status_update():
    """タスクステータス更新のデモ"""
    print("\n" + "="*60)
    print("🔄 Scheduler Agent Demo - Task Status Update")
    print("="*60 + "\n")

    agent = SchedulerAgent()

    task_id = "task_status_test"

    # タスクをスケジュール
    await agent.schedule_task(
        task_id=task_id,
        task_type="data_processing",
        priority=7
    )

    print(f"📝 Updating task status for: {task_id}")

    # ステータスを更新
    await agent.update_task_status(
        task_id=task_id,
        status="completed",
        result={"processed_records": 150, "duration": 45.3}
    )

    print(f"  ✅ Status updated to: completed")
    print(f"  Result: {{processed_records: 150, duration: 45.3s}}")


async def demo_schedule_optimization():
    """スケジュール最適化のデモ"""
    print("\n" + "="*60)
    print("🎯 Scheduler Agent Demo - Schedule Optimization")
    print("="*60 + "\n")

    agent = SchedulerAgent()

    # 複数のタスクをスケジュール
    tasks_to_schedule = [
        ("opt_task_001", "sns_post", 7, 2),
        ("opt_task_002", "data_analysis", 5, 24),
        ("opt_task_003", "compliance_check", 9, 1),
        ("opt_task_004", "report_generation", 6, 12),
        ("opt_task_005", "email_send", 4, 48),
    ]

    print("📝 Scheduling multiple tasks...")
    for task_id, task_type, priority, hours_until_deadline in tasks_to_schedule:
        await agent.schedule_task(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            deadline=datetime.now() + timedelta(hours=hours_until_deadline)
        )
        print(f"  • {task_id}: Priority={priority}, Deadline in {hours_until_deadline}h")

    print(f"\n  Total tasks in queue: {len(agent.task_queue)}")

    print("\n📝 Optimizing schedule with LLM...")
    optimization_result = await agent.optimize_schedule()

    print(f"\n  ✅ Optimization Results:")
    print(f"    Optimized: {optimization_result['optimized']}")
    print(f"    Task Count: {optimization_result['task_count']}")

    if optimization_result['optimized']:
        print(f"\n    💡 Recommendations:")
        recommendations = optimization_result['recommendations']
        print(f"    {recommendations[:300]}...")


async def demo_task_stats():
    """タスク統計のデモ"""
    print("\n" + "="*60)
    print("📊 Scheduler Agent Demo - Task Statistics")
    print("="*60 + "\n")

    agent = SchedulerAgent()

    # いくつかのタスクをスケジュールして完了
    for i in range(5):
        await agent.schedule_task(
            task_id=f"stats_task_{i}",
            task_type="test_task",
            priority=5 + i
        )

    # 一部を完了としてマーク
    await agent.update_task_status("stats_task_0", "completed")
    await agent.update_task_status("stats_task_1", "completed")
    await agent.update_task_status("stats_task_2", "failed")

    print("📝 Retrieving task statistics...")
    stats = await agent.get_task_stats()

    print(f"\n  ✅ Task Statistics:")
    print(f"    Total Tasks: {stats['total_tasks']}")
    print(f"    Queued: {stats['queued_tasks']}")
    print(f"    Completed: {stats['completed_tasks']}")
    print(f"    Failed: {stats['failed_tasks']}")

    completion_rate = (stats['completed_tasks'] / stats['total_tasks'] * 100) if stats['total_tasks'] > 0 else 0
    print(f"    Completion Rate: {completion_rate:.1f}%")


async def main():
    """すべてのデモを実行"""
    print("\n" + "="*60)
    print("🎯 Scheduler Agent - Comprehensive Demo")
    print("   DRY_RUN Mode: All LLM calls are mocked ($0.00 cost)")
    print("="*60)

    try:
        await demo_task_scheduling()
        await demo_task_retrieval()
        await demo_task_status_update()
        await demo_schedule_optimization()
        await demo_task_stats()

        print("\n" + "="*60)
        print("✅ All demos completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        logger.error("Demo failed", error=str(e))
        print(f"\n❌ Demo failed: {str(e)}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
