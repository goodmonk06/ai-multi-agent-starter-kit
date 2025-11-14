"""
Scheduler Agent - タスクのスケジューリングと管理を担当

機能:
- タスクの優先順位付け
- リソース配分の最適化
- デッドライン管理
- タスク間の依存関係の解決
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class SchedulerAgent:
    """タスクをスケジュールし、適切なエージェントに振り分けるエージェント"""

    def __init__(self, memory_store=None):
        self.memory = memory_store
        self.task_queue = []
        self.scheduled_tasks = {}
        logger.info("SchedulerAgent initialized")

    async def schedule_task(
        self,
        task_id: str,
        task_type: str,
        priority: int = 5,
        deadline: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        タスクをスケジュールする

        Args:
            task_id: タスクID
            task_type: タスクタイプ (care_schedule, sns_post, hr_match, etc.)
            priority: 優先度 (1-10, 10が最高)
            deadline: デッドライン
            metadata: 追加メタデータ

        Returns:
            スケジュール結果
        """
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "priority": priority,
            "deadline": deadline,
            "created_at": datetime.now(),
            "status": "scheduled",
            "metadata": metadata or {}
        }

        self.scheduled_tasks[task_id] = task
        self._add_to_queue(task)

        logger.info("Task scheduled", task_id=task_id, priority=priority)

        if self.memory:
            await self.memory.store(f"task:{task_id}", task)

        return task

    def _add_to_queue(self, task: Dict[str, Any]) -> None:
        """優先度順にタスクをキューに追加"""
        self.task_queue.append(task)
        # 優先度とデッドラインでソート
        self.task_queue.sort(
            key=lambda x: (
                -x["priority"],
                x["deadline"] if x["deadline"] else datetime.max
            )
        )

    async def get_next_task(self) -> Optional[Dict[str, Any]]:
        """次に実行すべきタスクを取得"""
        if not self.task_queue:
            return None

        task = self.task_queue.pop(0)
        task["status"] = "assigned"

        logger.info("Task assigned", task_id=task["task_id"])
        return task

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """タスクのステータスを更新"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id]["status"] = status
            self.scheduled_tasks[task_id]["updated_at"] = datetime.now()

            if result:
                self.scheduled_tasks[task_id]["result"] = result

            if self.memory:
                await self.memory.store(
                    f"task:{task_id}",
                    self.scheduled_tasks[task_id]
                )

            logger.info("Task status updated", task_id=task_id, status=status)

    async def get_task_stats(self) -> Dict[str, Any]:
        """タスク統計を取得"""
        stats = {
            "total_tasks": len(self.scheduled_tasks),
            "queued_tasks": len(self.task_queue),
            "completed_tasks": sum(
                1 for t in self.scheduled_tasks.values()
                if t["status"] == "completed"
            ),
            "failed_tasks": sum(
                1 for t in self.scheduled_tasks.values()
                if t["status"] == "failed"
            ),
        }
        return stats
