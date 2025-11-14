"""
Care Scheduler Application - メインアプリケーション

機能:
- スタッフシフト管理
- 利用者スケジュール最適化
- リソース配分
- 緊急対応
"""

from typing import Dict, List, Optional, Any
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()


class CareSchedulerApp:
    """介護スケジューリングアプリケーション"""

    def __init__(self, agents: Dict[str, Any], workflow, memory):
        self.agents = agents
        self.workflow = workflow
        self.memory = memory
        self.schedules = {}
        logger.info("CareSchedulerApp initialized")

    async def create_shift_schedule(
        self,
        facility_id: str,
        date_range: Dict[str, str],
        staff_list: List[Dict[str, Any]],
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        シフトスケジュールを作成

        Args:
            facility_id: 施設ID
            date_range: 日付範囲 {"start": "2024-01-01", "end": "2024-01-31"}
            staff_list: スタッフリスト
            requirements: 要件（最小人数、スキル要件など）

        Returns:
            作成されたスケジュール
        """
        logger.info(
            "Creating shift schedule",
            facility=facility_id,
            range=date_range
        )

        # Schedulerエージェントを使用
        scheduler = self.agents.get("scheduler")
        analyzer = self.agents.get("analyzer")

        # 既存データを分析
        if analyzer:
            historical_data = await self._get_historical_data(facility_id)
            analysis = await analyzer.analyze_data(
                historical_data,
                analysis_type="trend"
            )

        # スケジュール生成
        schedule_task = {
            "task_id": f"shift_{facility_id}_{datetime.now().timestamp()}",
            "task_type": "care_schedule",
            "facility_id": facility_id,
            "date_range": date_range,
            "staff_list": staff_list,
            "requirements": requirements,
            "metadata": {
                "created_by": "CareSchedulerApp",
                "created_at": datetime.now().isoformat()
            }
        }

        if scheduler:
            result = await scheduler.schedule_task(**schedule_task)

            # スケジュールを保存
            schedule_id = result.get("task_id")
            self.schedules[schedule_id] = result

            if self.memory:
                await self.memory.store(f"schedule:{schedule_id}", result)

            return result

        return {"error": "Scheduler agent not available"}

    async def optimize_care_plan(
        self,
        user_id: str,
        care_needs: Dict[str, Any],
        available_resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        ケアプランを最適化

        Args:
            user_id: 利用者ID
            care_needs: ケアニーズ
            available_resources: 利用可能なリソース

        Returns:
            最適化されたケアプラン
        """
        logger.info("Optimizing care plan", user_id=user_id)

        analyzer = self.agents.get("analyzer")

        # ケアニーズを分析
        analysis_data = [{
            "user_id": user_id,
            "needs": care_needs,
            "resources": available_resources
        }]

        if analyzer:
            analysis = await analyzer.analyze_data(
                analysis_data,
                analysis_type="general"
            )

            care_plan = {
                "user_id": user_id,
                "plan_id": f"plan_{user_id}_{datetime.now().timestamp()}",
                "care_needs": care_needs,
                "allocated_resources": self._allocate_resources(
                    care_needs,
                    available_resources
                ),
                "schedule": self._generate_care_schedule(care_needs),
                "analysis": analysis,
                "created_at": datetime.now().isoformat()
            }

            # メモリに保存
            if self.memory:
                await self.memory.store(
                    f"care_plan:{user_id}",
                    care_plan
                )

            return care_plan

        return {"error": "Analyzer agent not available"}

    async def handle_emergency(
        self,
        emergency_type: str,
        location: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        緊急事態に対応

        Args:
            emergency_type: 緊急タイプ
            location: 場所
            details: 詳細情報

        Returns:
            対応結果
        """
        logger.warning(
            "Handling emergency",
            type=emergency_type,
            location=location
        )

        executor = self.agents.get("executor")
        generator = self.agents.get("generator")

        # 緊急対応タスクを作成
        emergency_task = {
            "task_id": f"emergency_{datetime.now().timestamp()}",
            "task_type": "emergency_response",
            "emergency_type": emergency_type,
            "location": location,
            "details": details,
            "priority": 10  # 最高優先度
        }

        # 通知を生成
        if generator:
            notification = await generator.generate_content(
                content_type="message",
                context={
                    "purpose": "emergency_alert",
                    "emergency_type": emergency_type,
                    "location": location,
                    "details": details
                },
                style="urgent"
            )

            emergency_task["notification"] = notification

        # タスクを実行
        if executor:
            result = await executor.execute_task(emergency_task)
            return result

        return {"error": "Executor agent not available"}

    def _allocate_resources(
        self,
        care_needs: Dict[str, Any],
        available_resources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """リソースを配分"""
        allocated = []

        # 簡易的なマッチングロジック
        for need_type, need_value in care_needs.items():
            for resource in available_resources:
                if resource.get("type") == need_type:
                    allocated.append({
                        "need": need_type,
                        "resource": resource,
                        "allocated_at": datetime.now().isoformat()
                    })
                    break

        return allocated

    def _generate_care_schedule(
        self,
        care_needs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """ケアスケジュールを生成"""
        schedule = []
        base_time = datetime.now().replace(hour=8, minute=0, second=0)

        for i, (need_type, frequency) in enumerate(care_needs.items()):
            schedule.append({
                "time": (base_time + timedelta(hours=i*2)).isoformat(),
                "activity": need_type,
                "duration_minutes": 30,
                "frequency": frequency
            })

        return schedule

    async def _get_historical_data(
        self,
        facility_id: str
    ) -> List[Dict[str, Any]]:
        """過去のデータを取得"""
        if self.memory:
            # メモリから過去のスケジュールを取得
            historical = await self.memory.search(
                f"schedule:{facility_id}",
                limit=100
            )
            return historical

        return []

    async def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """スケジュールを取得"""
        if schedule_id in self.schedules:
            return self.schedules[schedule_id]

        if self.memory:
            return await self.memory.retrieve(f"schedule:{schedule_id}")

        return None
