"""
Tasks Router - タスク管理エンドポイント
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

router = APIRouter()


class TaskCreate(BaseModel):
    task_type: str
    description: Optional[str] = None
    priority: int = 5
    data: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    created_at: str
    result: Optional[Dict[str, Any]] = None


@router.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    """新しいタスクを作成"""
    from api.server import get_system_state

    state = get_system_state()
    router = state.get("task_router")

    if not router:
        raise HTTPException(status_code=500, detail="Task router not initialized")

    task_data = {
        "task_id": f"task_{datetime.now().timestamp()}",
        "task_type": task.task_type,
        "description": task.description,
        "priority": task.priority,
        "data": task.data or {}
    }

    # タスクをルーティング
    routing_result = await router.route_task(task_data)

    # エージェントにタスクを割り当て
    primary_agent_name = routing_result.get("primary_agent")
    if primary_agent_name in state["agents"]:
        agent = state["agents"][primary_agent_name]

        # Executorエージェントを使ってタスクを実行
        executor = state["agents"].get("executor")
        if executor:
            result = await executor.execute_task(task_data)

            return TaskResponse(
                task_id=result["task_id"],
                task_type=task.task_type,
                status=result["status"],
                created_at=result["start_time"],
                result=result.get("result")
            )

    raise HTTPException(status_code=500, detail="Task execution failed")


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """タスクの状態を取得"""
    from api.server import get_system_state

    state = get_system_state()
    memory = state.get("memory")

    if not memory:
        raise HTTPException(status_code=500, detail="Memory store not initialized")

    task_data = await memory.retrieve(f"execution:{task_id}")

    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(
        task_id=task_data["task_id"],
        task_type=task_data.get("task_type", "unknown"),
        status=task_data["status"],
        created_at=task_data["start_time"],
        result=task_data.get("result")
    )


@router.get("/tasks")
async def list_tasks(limit: int = 10):
    """タスクリストを取得"""
    from api.server import get_system_state

    state = get_system_state()
    memory = state.get("memory")

    if not memory:
        raise HTTPException(status_code=500, detail="Memory store not initialized")

    tasks = await memory.search("execution:", limit=limit)

    return {
        "tasks": tasks,
        "count": len(tasks)
    }
