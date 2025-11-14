"""
API Server - FastAPIベースのRESTful APIサーバー

エンドポイント:
- /tasks - タスク管理
- /agents - エージェント情報
- /workflows - ワークフロー実行
- /apps - アプリケーション機能
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import structlog
from datetime import datetime
import uvicorn

# Import routes
from .routes import tasks, agents, workflows, apps

logger = structlog.get_logger()

# FastAPIアプリケーション
app = FastAPI(
    title="AI Multi-Agent Starter Kit API",
    description="Multi-agent AI system for business automation",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバル状態（実際にはDIコンテナを使用）
system_state = {
    "agents": {},
    "workflow": None,
    "memory": None,
    "task_router": None,
    "apps": {},
    "runner": None
}


@app.on_event("startup")
async def startup_event():
    """起動時の初期化"""
    logger.info("Starting AI Multi-Agent API Server")

    # エージェントとコアコンポーネントを初期化
    await initialize_system()

    logger.info("API Server ready")


@app.on_event("shutdown")
async def shutdown_event():
    """シャットダウン時のクリーンアップ"""
    logger.info("Shutting down AI Multi-Agent API Server")


async def initialize_system():
    """システムを初期化"""
    from agents import (
        SchedulerAgent,
        AnalyzerAgent,
        GeneratorAgent,
        ComplianceAgent,
        ExecutorAgent,
        SearchAgent
    )
    from core import AgentWorkflow, MemoryStore, TaskRouter, ToolRegistry

    # メモリストアを初期化
    memory = MemoryStore(backend="in_memory")
    system_state["memory"] = memory

    # エージェントを初期化
    agents = {
        "scheduler": SchedulerAgent(memory_store=memory),
        "analyzer": AnalyzerAgent(memory_store=memory),
        "generator": GeneratorAgent(memory_store=memory),
        "compliance": ComplianceAgent(memory_store=memory),
        "executor": ExecutorAgent(memory_store=memory),
        "search": SearchAgent(memory_store=memory)
    }
    system_state["agents"] = agents

    # タスクルーターを初期化
    task_router = TaskRouter(agents)
    system_state["task_router"] = task_router

    # ワークフローを初期化
    workflow = AgentWorkflow(agents, memory, task_router)
    system_state["workflow"] = workflow

    # アプリケーションを初期化
    from apps.care_scheduler import CareSchedulerApp
    from apps.sns_auto import SnsAutoApp
    from apps.hr_matching import HrMatchingApp

    apps = {
        "care_scheduler": CareSchedulerApp(agents, workflow, memory),
        "sns_auto": SnsAutoApp(agents, workflow, memory),
        "hr_matching": HrMatchingApp(agents, workflow, memory)
    }
    system_state["apps"] = apps

    logger.info("System initialized", agents=list(agents.keys()), apps=list(apps.keys()))


# ルーターを登録
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
app.include_router(apps.router, prefix="/api/v1", tags=["apps"])


# ルートエンドポイント
@app.get("/")
async def root():
    """APIルート"""
    return {
        "name": "AI Multi-Agent Starter Kit API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "agents": list(system_state["agents"].keys()),
        "apps": list(system_state["apps"].keys()),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/runner/status")
async def get_runner_status():
    """
    Runnerのステータスを取得

    Returns:
        dict: Runnerの現在の状態と統計情報
    """
    runner = system_state.get("runner")

    if runner is None:
        # Runnerが起動していない場合
        return {
            "enabled": False,
            "running": False,
            "message": "Runner is not initialized (RUNNER_ENABLED=false)",
            "timestamp": datetime.now().isoformat()
        }

    status = runner.get_status()
    status["enabled"] = True
    status["timestamp"] = datetime.now().isoformat()

    return status


@app.post("/runner/run-now")
async def trigger_runner_jobs(background_tasks: BackgroundTasks):
    """
    即座にすべてのジョブを実行

    DRY_RUNモードでのテスト用エンドポイント
    バックグラウンドタスクとして実行

    Returns:
        dict: 実行結果の概要
    """
    runner = system_state.get("runner")

    if runner is None:
        raise HTTPException(
            status_code=503,
            detail="Runner is not initialized (RUNNER_ENABLED=false)"
        )

    if not runner.running:
        raise HTTPException(
            status_code=503,
            detail="Runner is not running"
        )

    # すべてのジョブを強制実行
    jobs = runner.registry.list()

    async def run_all_jobs():
        """すべてのジョブを実行"""
        results = []
        for job in jobs:
            try:
                result = await job.run()
                results.append(result)
                logger.info("Manual job execution", job=job.name, status=result.get("status"))
            except Exception as e:
                logger.error("Manual job execution failed", job=job.name, error=str(e))
                results.append({
                    "status": "error",
                    "job": job.name,
                    "error": str(e)
                })
        return results

    # バックグラウンドで実行
    background_tasks.add_task(run_all_jobs)

    return {
        "status": "triggered",
        "jobs_count": len(jobs),
        "jobs": [j.name for j in jobs],
        "message": "All jobs triggered for execution",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/system/stats")
async def get_system_stats():
    """システム統計情報"""
    stats = {
        "agents_count": len(system_state["agents"]),
        "apps_count": len(system_state["apps"]),
        "timestamp": datetime.now().isoformat()
    }

    # メモリ統計
    if system_state.get("memory"):
        memory_stats = await system_state["memory"].get_stats()
        stats["memory"] = memory_stats

    # タスクルーター統計
    if system_state.get("task_router"):
        router_stats = await system_state["task_router"].get_routing_stats()
        stats["routing"] = router_stats

    return stats


def get_system_state():
    """システム状態を取得（ルーターで使用）"""
    return system_state


if __name__ == "__main__":
    # サーバーを起動
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
