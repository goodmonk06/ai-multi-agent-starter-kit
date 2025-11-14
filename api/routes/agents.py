"""
Agents Router - エージェント管理エンドポイント
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

router = APIRouter()


@router.get("/agents")
async def list_agents():
    """利用可能なエージェントのリストを取得"""
    from api.server import get_system_state

    state = get_system_state()
    agents = state.get("agents", {})

    agent_info = []
    for name, agent in agents.items():
        info = {
            "name": name,
            "type": agent.__class__.__name__,
            "status": "active"
        }

        # エージェント固有の統計情報
        if hasattr(agent, "get_task_stats"):
            stats = await agent.get_task_stats()
            info["stats"] = stats
        elif hasattr(agent, "get_execution_stats"):
            stats = await agent.get_execution_stats()
            info["stats"] = stats

        agent_info.append(info)

    return {
        "agents": agent_info,
        "count": len(agent_info)
    }


@router.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    """特定のエージェントの情報を取得"""
    from api.server import get_system_state

    state = get_system_state()
    agents = state.get("agents", {})

    if agent_name not in agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    agent = agents[agent_name]

    info = {
        "name": agent_name,
        "type": agent.__class__.__name__,
        "status": "active"
    }

    # エージェント固有の統計情報
    if hasattr(agent, "get_task_stats"):
        info["stats"] = await agent.get_task_stats()
    elif hasattr(agent, "get_execution_stats"):
        info["stats"] = await agent.get_execution_stats()

    return info


@router.get("/agents/{agent_name}/load")
async def get_agent_load(agent_name: str):
    """エージェントの負荷情報を取得"""
    from api.server import get_system_state

    state = get_system_state()
    router = state.get("task_router")

    if not router:
        raise HTTPException(status_code=500, detail="Task router not initialized")

    load = await router.get_agent_load()

    if agent_name not in load:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    return {
        "agent": agent_name,
        "current_load": load[agent_name],
        "timestamp": datetime.now().isoformat()
    }


from datetime import datetime
