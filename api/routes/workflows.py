"""
Workflows Router - ワークフロー管理エンドポイント
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

router = APIRouter()


class WorkflowCreate(BaseModel):
    workflow_name: str
    initial_data: Dict[str, Any]


@router.get("/workflows")
async def list_workflows():
    """利用可能なワークフローのリストを取得"""
    from api.server import get_system_state

    state = get_system_state()
    workflow = state.get("workflow")

    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow engine not initialized")

    workflows = workflow.list_workflows()

    return {
        "workflows": workflows,
        "count": len(workflows)
    }


@router.post("/workflows/run")
async def run_workflow(request: WorkflowCreate):
    """ワークフローを実行"""
    from api.server import get_system_state

    state = get_system_state()
    workflow = state.get("workflow")

    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow engine not initialized")

    try:
        result = await workflow.run_workflow(
            request.workflow_name,
            request.initial_data
        )

        return {
            "workflow_name": request.workflow_name,
            "status": result["status"],
            "task_id": result["task_id"],
            "results": result.get("results", []),
            "errors": result.get("errors", [])
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """ワークフローの状態を取得"""
    from api.server import get_system_state

    state = get_system_state()
    workflow = state.get("workflow")

    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow engine not initialized")

    status = await workflow.get_workflow_status(workflow_id)

    if not status:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return status


@router.get("/workflows/active")
async def get_active_workflows():
    """実行中のワークフローを取得"""
    from api.server import get_system_state

    state = get_system_state()
    workflow = state.get("workflow")

    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow engine not initialized")

    active = workflow.get_active_workflows()

    return {
        "active_workflows": active,
        "count": len(active)
    }
