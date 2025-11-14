"""
Workflow - LangGraphベースのワークフローエンジン

複数エージェント間の調整とタスクフローの管理を担当
"""

from typing import Dict, List, Optional, Any, Callable
from typing_extensions import TypedDict
import structlog
from datetime import datetime

logger = structlog.get_logger()


class WorkflowState(TypedDict, total=False):
    """ワークフローの状態"""
    task_id: str
    task_type: str
    current_step: str
    data: Dict[str, Any]
    context: Dict[str, Any]
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    status: str


class AgentWorkflow:
    """LangGraphベースのマルチエージェントワークフロー"""

    def __init__(
        self,
        agents: Dict[str, Any],
        memory_store=None,
        task_router=None
    ):
        self.agents = agents
        self.memory = memory_store
        self.router = task_router
        self.workflows = {}
        self.active_workflows = {}
        logger.info("AgentWorkflow initialized", agent_count=len(agents))

    def define_workflow(
        self,
        workflow_name: str,
        steps: List[Dict[str, Any]]
    ) -> None:
        """
        ワークフローを定義する

        Args:
            workflow_name: ワークフロー名
            steps: ワークフローステップのリスト
                [
                    {"agent": "scheduler", "action": "schedule", "condition": None},
                    {"agent": "analyzer", "action": "analyze", "condition": "has_data"},
                    ...
                ]
        """
        self.workflows[workflow_name] = {
            "name": workflow_name,
            "steps": steps,
            "created_at": datetime.now().isoformat()
        }
        logger.info("Workflow defined", name=workflow_name, steps=len(steps))

    async def run_workflow(
        self,
        workflow_name: str,
        initial_data: Dict[str, Any]
    ) -> WorkflowState:
        """
        ワークフローを実行する

        Args:
            workflow_name: 実行するワークフロー名
            initial_data: 初期データ

        Returns:
            最終的なワークフロー状態
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")

        workflow = self.workflows[workflow_name]
        workflow_id = f"{workflow_name}_{datetime.now().timestamp()}"

        logger.info("Starting workflow", name=workflow_name, id=workflow_id)

        # 初期状態を作成
        state: WorkflowState = {
            "task_id": workflow_id,
            "task_type": workflow_name,
            "current_step": "init",
            "data": initial_data,
            "context": {},
            "results": [],
            "errors": [],
            "status": "running"
        }

        self.active_workflows[workflow_id] = state

        try:
            # ワークフローステップを順次実行
            for step_index, step in enumerate(workflow["steps"]):
                step_name = step.get("name", f"step_{step_index}")
                state["current_step"] = step_name

                logger.info(
                    "Executing workflow step",
                    workflow=workflow_name,
                    step=step_name
                )

                # 条件チェック
                if "condition" in step and step["condition"]:
                    if not self._check_condition(step["condition"], state):
                        logger.info("Step condition not met, skipping", step=step_name)
                        continue

                # ステップを実行
                step_result = await self._execute_step(step, state)

                # 結果を状態に追加
                state["results"].append({
                    "step": step_name,
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                })

                # エラーチェック
                if step_result.get("status") == "error":
                    state["errors"].append({
                        "step": step_name,
                        "error": step_result.get("error"),
                        "timestamp": datetime.now().isoformat()
                    })

                    # エラーハンドリング設定に応じて継続または停止
                    if step.get("stop_on_error", True):
                        state["status"] = "failed"
                        break

                # 次のステップのために結果をコンテキストに追加
                if "output_key" in step:
                    state["context"][step["output_key"]] = step_result

            # 全ステップ完了
            if state["status"] == "running":
                state["status"] = "completed"

            logger.info(
                "Workflow completed",
                name=workflow_name,
                status=state["status"]
            )

        except Exception as e:
            logger.error("Workflow failed", workflow=workflow_name, error=str(e))
            state["status"] = "failed"
            state["errors"].append({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        # メモリに保存
        if self.memory:
            await self.memory.store(f"workflow:{workflow_id}", state)

        # アクティブワークフローから削除
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]

        return state

    async def _execute_step(
        self,
        step: Dict[str, Any],
        state: WorkflowState
    ) -> Dict[str, Any]:
        """ワークフローステップを実行"""
        agent_name = step.get("agent")
        action = step.get("action")
        params = step.get("params", {})

        if not agent_name or agent_name not in self.agents:
            return {
                "status": "error",
                "error": f"Agent '{agent_name}' not found"
            }

        agent = self.agents[agent_name]

        try:
            # エージェントのメソッドを呼び出す
            if hasattr(agent, action):
                method = getattr(agent, action)

                # パラメータを準備（状態からの値を含む）
                resolved_params = self._resolve_params(params, state)

                # メソッドを実行
                result = await method(**resolved_params)

                return {
                    "status": "success",
                    "data": result
                }
            else:
                return {
                    "status": "error",
                    "error": f"Action '{action}' not found on agent '{agent_name}'"
                }

        except Exception as e:
            logger.error(
                "Step execution failed",
                agent=agent_name,
                action=action,
                error=str(e)
            )
            return {
                "status": "error",
                "error": str(e)
            }

    def _resolve_params(
        self,
        params: Dict[str, Any],
        state: WorkflowState
    ) -> Dict[str, Any]:
        """パラメータを解決（状態からの値参照を含む）"""
        resolved = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                # $context.key の形式で状態から値を取得
                ref_path = value[1:].split(".")
                ref_value = state

                for part in ref_path:
                    if isinstance(ref_value, dict) and part in ref_value:
                        ref_value = ref_value[part]
                    else:
                        ref_value = None
                        break

                resolved[key] = ref_value
            else:
                resolved[key] = value

        return resolved

    def _check_condition(
        self,
        condition: str,
        state: WorkflowState
    ) -> bool:
        """条件をチェック"""
        # シンプルな条件評価
        # 例: "has_data", "status == 'completed'", etc.

        if condition == "has_data":
            return bool(state.get("data"))

        if "==" in condition:
            parts = condition.split("==")
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip().strip("'\"")

                if key in state:
                    return str(state[key]) == value

        return True

    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowState]:
        """ワークフローの状態を取得"""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]

        # メモリから取得
        if self.memory:
            return await self.memory.retrieve(f"workflow:{workflow_id}")

        return None

    def list_workflows(self) -> List[str]:
        """定義されているワークフローのリストを取得"""
        return list(self.workflows.keys())

    def get_active_workflows(self) -> Dict[str, WorkflowState]:
        """実行中のワークフローを取得"""
        return self.active_workflows.copy()
