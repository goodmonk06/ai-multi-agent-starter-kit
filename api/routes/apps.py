"""
Apps Router - アプリケーション機能エンドポイント
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

router = APIRouter()


# Care Scheduler
class ShiftScheduleRequest(BaseModel):
    facility_id: str
    date_range: Dict[str, str]
    staff_list: List[Dict[str, Any]]
    requirements: Dict[str, Any]


@router.post("/apps/care_scheduler/shifts")
async def create_shift_schedule(request: ShiftScheduleRequest):
    """シフトスケジュールを作成"""
    from api.server import get_system_state

    state = get_system_state()
    app = state["apps"].get("care_scheduler")

    if not app:
        raise HTTPException(status_code=500, detail="Care scheduler app not available")

    result = await app.create_shift_schedule(
        request.facility_id,
        request.date_range,
        request.staff_list,
        request.requirements
    )

    return result


# SNS Auto
class SnsPostRequest(BaseModel):
    platform: str
    topic: str
    style: str = "professional"
    hashtags: Optional[List[str]] = None
    schedule_time: Optional[str] = None


@router.post("/apps/sns_auto/posts")
async def create_sns_post(request: SnsPostRequest):
    """SNS投稿を作成"""
    from api.server import get_system_state

    state = get_system_state()
    app = state["apps"].get("sns_auto")

    if not app:
        raise HTTPException(status_code=500, detail="SNS auto app not available")

    schedule_time = None
    if request.schedule_time:
        schedule_time = datetime.fromisoformat(request.schedule_time)

    result = await app.create_post(
        request.platform,
        request.topic,
        request.style,
        request.hashtags,
        schedule_time
    )

    return result


class EngagementAnalysisRequest(BaseModel):
    platform: str
    time_range: Dict[str, str]


@router.post("/apps/sns_auto/analyze")
async def analyze_engagement(request: EngagementAnalysisRequest):
    """エンゲージメントを分析"""
    from api.server import get_system_state

    state = get_system_state()
    app = state["apps"].get("sns_auto")

    if not app:
        raise HTTPException(status_code=500, detail="SNS auto app not available")

    result = await app.analyze_engagement(
        request.platform,
        request.time_range
    )

    return result


# HR Matching
class CandidateMatchRequest(BaseModel):
    job_posting: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    matching_criteria: Optional[Dict[str, Any]] = None


@router.post("/apps/hr_matching/match")
async def match_candidates(request: CandidateMatchRequest):
    """候補者と求人をマッチング"""
    from api.server import get_system_state

    state = get_system_state()
    app = state["apps"].get("hr_matching")

    if not app:
        raise HTTPException(status_code=500, detail="HR matching app not available")

    result = await app.match_candidates(
        request.job_posting,
        request.candidates,
        request.matching_criteria
    )

    return {
        "matches": result,
        "count": len(result)
    }


class ResumeAnalysisRequest(BaseModel):
    resume_data: Dict[str, Any]


@router.post("/apps/hr_matching/analyze_resume")
async def analyze_resume(request: ResumeAnalysisRequest):
    """履歴書を分析"""
    from api.server import get_system_state

    state = get_system_state()
    app = state["apps"].get("hr_matching")

    if not app:
        raise HTTPException(status_code=500, detail="HR matching app not available")

    result = await app.analyze_resume(request.resume_data)

    return result


@router.get("/apps")
async def list_apps():
    """利用可能なアプリケーションのリストを取得"""
    from api.server import get_system_state

    state = get_system_state()
    apps = state.get("apps", {})

    app_info = [
        {
            "name": name,
            "type": app.__class__.__name__,
            "status": "active"
        }
        for name, app in apps.items()
    ]

    return {
        "apps": app_info,
        "count": len(app_info)
    }
