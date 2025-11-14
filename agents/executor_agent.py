"""
Executor Agent - タスクの実行とワークフロー管理を担当

機能:
- タスクの実行
- ワークフローの調整
- 外部APIの呼び出し
- 結果の検証と報告
"""

from typing import Dict, List, Optional, Any, Callable
import structlog
from datetime import datetime
import asyncio
from core import get_llm_router

logger = structlog.get_logger()


class ExecutorAgent:
    """タスクを実行し、結果を管理するエージェント"""

    def __init__(self, llm_client=None, memory_store=None, tools=None):
        # LLM Router を使用（デフォルト）
        self.llm = llm_client or get_llm_router()
        self.memory = memory_store
        self.tools = tools or {}
        self.execution_history = []
        self.running_tasks = {}
        logger.info("ExecutorAgent initialized", llm_router_enabled=True)

    async def execute_task(
        self,
        task: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        タスクを実行する

        Args:
            task: 実行するタスク
            context: 実行コンテキスト

        Returns:
            実行結果
        """
        task_id = task.get("task_id", f"task_{datetime.now().timestamp()}")
        task_type = task.get("task_type", "generic")

        logger.info("Executing task", task_id=task_id, type=task_type)

        start_time = datetime.now()

        try:
            # タスクを実行中リストに追加
            self.running_tasks[task_id] = {
                "task": task,
                "start_time": start_time,
                "status": "running"
            }

            # タスクタイプに応じた実行
            if task_type == "api_call":
                result = await self._execute_api_call(task, context)
            elif task_type == "workflow":
                result = await self._execute_workflow(task, context)
            elif task_type == "data_processing":
                result = await self._execute_data_processing(task, context)
            else:
                result = await self._execute_generic(task, context)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            execution_result = {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration
            }

            # 実行履歴に追加
            self.execution_history.append(execution_result)

            # メモリに保存
            if self.memory:
                await self.memory.store(f"execution:{task_id}", execution_result)

            # 実行中リストから削除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

            logger.info("Task completed", task_id=task_id, duration=duration)

            return execution_result

        except Exception as e:
            logger.error("Task execution failed", task_id=task_id, error=str(e))

            execution_result = {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }

            self.execution_history.append(execution_result)

            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

            return execution_result

    async def _execute_api_call(
        self,
        task: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """API呼び出しを実行"""
        api_config = task.get("api_config", {})
        method = api_config.get("method", "GET")
        url = api_config.get("url")

        if not url:
            raise ValueError("API URL is required")

        # 実際の実装ではhttpxなどを使用
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.request(method, url, **api_config.get("params", {}))
        #     return response.json()

        return {
            "message": f"API call to {url} completed",
            "method": method,
            "simulated": True
        }

    async def _execute_workflow(
        self,
        task: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """ワークフローを実行"""
        workflow_steps = task.get("workflow_steps", [])

        results = []
        workflow_context = context or {}

        for step in workflow_steps:
            step_result = await self.execute_task(step, workflow_context)
            results.append(step_result)

            # 前のステップの結果を次のステップのコンテキストに追加
            if step_result["status"] == "completed":
                workflow_context.update(step_result.get("result", {}))
            else:
                # ステップが失敗した場合、ワークフローを中断
                break

        return {
            "workflow_completed": all(r["status"] == "completed" for r in results),
            "steps_executed": len(results),
            "step_results": results
        }

    async def _execute_data_processing(
        self,
        task: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """データ処理を実行"""
        data = task.get("data", [])
        operation = task.get("operation", "transform")

        processed_data = []

        for item in data:
            # データ処理ロジック
            processed_item = self._process_item(item, operation)
            processed_data.append(processed_item)

        return {
            "processed_count": len(processed_data),
            "data": processed_data,
            "operation": operation
        }

    async def _execute_generic(
        self,
        task: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """汎用タスクを実行"""
        action = task.get("action")
        params = task.get("params", {})

        # ツールが登録されていれば使用
        if action and action in self.tools:
            tool = self.tools[action]
            return await tool(params)

        return {
            "message": f"Generic task executed: {action}",
            "params": params
        }

    def _process_item(self, item: Any, operation: str) -> Any:
        """個別のアイテムを処理"""
        if operation == "transform":
            # 変換処理
            return {"original": item, "transformed": True}
        elif operation == "validate":
            # 検証処理
            return {"item": item, "valid": True}
        else:
            return item

    async def execute_parallel(
        self,
        tasks: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """複数のタスクを並列実行"""
        logger.info("Executing tasks in parallel", count=len(tasks))

        # asyncio.gatherで並列実行
        results = await asyncio.gather(
            *[self.execute_task(task, context) for task in tasks],
            return_exceptions=True
        )

        # 例外をエラー結果に変換
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "task_id": tasks[i].get("task_id", f"task_{i}"),
                    "status": "failed",
                    "error": str(result)
                })
            else:
                processed_results.append(result)

        return processed_results

    async def register_tool(
        self,
        tool_name: str,
        tool_function: Callable
    ) -> None:
        """ツールを登録"""
        self.tools[tool_name] = tool_function
        logger.info("Tool registered", tool=tool_name)

    async def get_execution_stats(self) -> Dict[str, Any]:
        """実行統計を取得"""
        total_executions = len(self.execution_history)
        completed = sum(
            1 for e in self.execution_history
            if e["status"] == "completed"
        )
        failed = sum(
            1 for e in self.execution_history
            if e["status"] == "failed"
        )

        avg_duration = 0
        if completed > 0:
            durations = [
                e.get("duration_seconds", 0)
                for e in self.execution_history
                if e["status"] == "completed"
            ]
            avg_duration = sum(durations) / len(durations)

        return {
            "total_executions": total_executions,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total_executions if total_executions > 0 else 0,
            "average_duration_seconds": avg_duration,
            "currently_running": len(self.running_tasks)
        }

    async def cancel_task(self, task_id: str) -> bool:
        """実行中のタスクをキャンセル"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id]["status"] = "cancelled"
            logger.info("Task cancelled", task_id=task_id)
            return True
        return False

    async def validate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """LLMを使ってタスクの妥当性をチェック"""
        try:
            task_id = task.get("task_id", "unknown")
            task_type = task.get("task_type", "unknown")
            task_params = task.get("params", {})

            prompt = f"""Validate the following task before execution:

Task ID: {task_id}
Task Type: {task_type}
Parameters: {task_params}

Check for:
1. Missing required parameters
2. Invalid parameter values
3. Potential security risks
4. Resource requirements
5. Expected execution time

Provide:
- validation_status: PASS or FAIL
- issues: list of any problems found
- recommendations: suggested fixes or improvements"""

            # LLM Router経由で妥当性チェック（DRY_RUNモードではモック応答）
            result = await self.llm.generate(
                prompt=prompt,
                max_tokens=512,
                temperature=0.3,  # より保守的な応答
                task_type="execute"
            )

            if result["status"] == "success":
                return {
                    "validated": True,
                    "task_id": task_id,
                    "analysis": result["result"],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "validated": False,
                    "task_id": task_id,
                    "error": result.get("error"),
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error("Task validation failed", error=str(e))
            return {
                "validated": False,
                "task_id": task.get("task_id", "unknown"),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
