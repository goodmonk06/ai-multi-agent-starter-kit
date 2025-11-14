"""
Task Router - タスクを適切なエージェントにルーティング

機能:
- タスク分類
- エージェント選択
- 負荷分散
- 優先度管理
"""

from typing import Dict, List, Optional, Any
import structlog
from datetime import datetime

logger = structlog.get_logger()


class TaskRouter:
    """タスクを適切なエージェントにルーティングするルーター"""

    def __init__(self, agents: Dict[str, Any], llm_client=None):
        self.agents = agents
        self.llm = llm_client
        self.routing_rules = self._load_default_rules()
        self.routing_history = []
        logger.info("TaskRouter initialized", agents=list(agents.keys()))

    def _load_default_rules(self) -> Dict[str, Any]:
        """デフォルトのルーティングルールを読み込む"""
        return {
            "care_schedule": {
                "primary_agent": "scheduler",
                "support_agents": ["analyzer", "compliance"],
                "workflow": "care_scheduling_workflow"
            },
            "sns_post": {
                "primary_agent": "generator",
                "support_agents": ["compliance", "analyzer"],
                "workflow": "sns_posting_workflow"
            },
            "hr_matching": {
                "primary_agent": "analyzer",
                "support_agents": ["scheduler", "generator"],
                "workflow": "hr_matching_workflow"
            },
            "data_analysis": {
                "primary_agent": "analyzer",
                "support_agents": [],
                "workflow": "analysis_workflow"
            },
            "content_generation": {
                "primary_agent": "generator",
                "support_agents": ["compliance"],
                "workflow": "content_workflow"
            },
            "compliance_check": {
                "primary_agent": "compliance",
                "support_agents": [],
                "workflow": "compliance_workflow"
            },
            "task_execution": {
                "primary_agent": "executor",
                "support_agents": ["scheduler"],
                "workflow": "execution_workflow"
            }
        }

    async def route_task(
        self,
        task: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        タスクを適切なエージェントにルーティング

        Args:
            task: ルーティングするタスク
            context: 追加コンテキスト

        Returns:
            ルーティング結果
        """
        task_type = task.get("task_type", "unknown")
        task_id = task.get("task_id", f"task_{datetime.now().timestamp()}")

        logger.info("Routing task", task_id=task_id, type=task_type)

        # タスクタイプに基づいてルーティング
        if task_type in self.routing_rules:
            routing_info = self.routing_rules[task_type]
        else:
            # LLMを使ってタスクタイプを推定
            routing_info = await self._classify_task(task, context)

        primary_agent_name = routing_info.get("primary_agent")
        support_agents = routing_info.get("support_agents", [])
        workflow = routing_info.get("workflow")

        # エージェントが存在するか確認
        if primary_agent_name not in self.agents:
            logger.error(
                "Primary agent not found",
                agent=primary_agent_name,
                task_id=task_id
            )
            return {
                "status": "error",
                "error": f"Agent '{primary_agent_name}' not found",
                "task_id": task_id
            }

        routing_result = {
            "task_id": task_id,
            "task_type": task_type,
            "primary_agent": primary_agent_name,
            "support_agents": support_agents,
            "workflow": workflow,
            "routed_at": datetime.now().isoformat(),
            "status": "routed"
        }

        # ルーティング履歴を記録
        self.routing_history.append(routing_result)

        logger.info(
            "Task routed",
            task_id=task_id,
            agent=primary_agent_name,
            workflow=workflow
        )

        return routing_result

    async def _classify_task(
        self,
        task: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """LLMを使ってタスクを分類"""
        # タスクの内容を分析
        task_description = task.get("description", "")
        task_data = task.get("data", {})

        # キーワードベースの簡易分類
        keywords_map = {
            "schedule": "scheduler",
            "analyze": "analyzer",
            "generate": "generator",
            "create": "generator",
            "check": "compliance",
            "execute": "executor",
            "run": "executor"
        }

        description_lower = task_description.lower()

        for keyword, agent in keywords_map.items():
            if keyword in description_lower:
                return {
                    "primary_agent": agent,
                    "support_agents": [],
                    "workflow": f"{agent}_workflow",
                    "confidence": 0.7
                }

        # LLMを使った高度な分類
        if self.llm:
            # LLM呼び出しのプレースホルダー
            # classification = await self.llm.classify(task_description)
            pass

        # デフォルト
        return {
            "primary_agent": "executor",
            "support_agents": [],
            "workflow": "generic_workflow",
            "confidence": 0.3
        }

    async def add_routing_rule(
        self,
        task_type: str,
        primary_agent: str,
        support_agents: Optional[List[str]] = None,
        workflow: Optional[str] = None
    ) -> None:
        """カスタムルーティングルールを追加"""
        self.routing_rules[task_type] = {
            "primary_agent": primary_agent,
            "support_agents": support_agents or [],
            "workflow": workflow or f"{primary_agent}_workflow"
        }

        logger.info("Routing rule added", task_type=task_type, agent=primary_agent)

    async def get_agent_load(self) -> Dict[str, int]:
        """各エージェントの負荷を取得"""
        load = {agent_name: 0 for agent_name in self.agents.keys()}

        # 過去1分間のルーティング履歴を集計
        recent_time = datetime.now().timestamp() - 60

        for entry in self.routing_history:
            routed_at = datetime.fromisoformat(entry["routed_at"]).timestamp()
            if routed_at > recent_time:
                agent = entry["primary_agent"]
                if agent in load:
                    load[agent] += 1

        return load

    async def get_routing_stats(self) -> Dict[str, Any]:
        """ルーティング統計を取得"""
        total_routes = len(self.routing_history)

        if total_routes == 0:
            return {
                "total_routes": 0,
                "routes_by_agent": {},
                "routes_by_type": {},
                "average_load": 0
            }

        # エージェント別集計
        routes_by_agent = {}
        for entry in self.routing_history:
            agent = entry["primary_agent"]
            routes_by_agent[agent] = routes_by_agent.get(agent, 0) + 1

        # タスクタイプ別集計
        routes_by_type = {}
        for entry in self.routing_history:
            task_type = entry["task_type"]
            routes_by_type[task_type] = routes_by_type.get(task_type, 0) + 1

        return {
            "total_routes": total_routes,
            "routes_by_agent": routes_by_agent,
            "routes_by_type": routes_by_type,
            "average_load": total_routes / len(self.agents) if self.agents else 0
        }

    async def suggest_agent(
        self,
        task_description: str
    ) -> Dict[str, Any]:
        """
        タスク説明から最適なエージェントを提案

        Args:
            task_description: タスクの説明

        Returns:
            提案されたエージェント情報
        """
        task = {
            "task_type": "unknown",
            "description": task_description
        }

        classification = await self._classify_task(task, None)

        return {
            "suggested_agent": classification["primary_agent"],
            "confidence": classification.get("confidence", 0.5),
            "reasoning": f"Based on task description: '{task_description[:50]}...'",
            "alternative_agents": classification.get("support_agents", [])
        }

    def list_routing_rules(self) -> Dict[str, Any]:
        """定義されているルーティングルールを取得"""
        return self.routing_rules.copy()
