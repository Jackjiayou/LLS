from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from app.core.auth import get_current_user
from app.db.database import SessionLocal
from app.models.practice import PracticeRecord
from app.schemas.practice import PracticeStatsResponse

router = APIRouter()


@router.get("/stats", response_model=PracticeStatsResponse)
async def get_practice_stats(
        token: dict = Depends(get_current_user)
):
    """获取用户的练习统计信息"""
    try:
        with SessionLocal() as db:
            user_id = token["sub"]

            # 获取练习次数
            practice_count = db.query(func.count(PracticeRecord.practice_id)) \
                .filter(PracticeRecord.user_id == user_id) \
                .scalar()

            # 获取练习时长（已完成练习的总时长，单位：分钟）
            total_duration = db.query(
                func.sum(
                    func.extract('epoch', PracticeRecord.ended_at - PracticeRecord.started_at) / 3600
                )
            ).filter(
                PracticeRecord.user_id == user_id,
                PracticeRecord.status == 'completed',
                PracticeRecord.ended_at.isnot(None)
            ).scalar() or 0

            # 获取练习场景数（去重）
            scenario_count = db.query(func.count(func.distinct(PracticeRecord.scenario_id))) \
                .filter(PracticeRecord.user_id == user_id) \
                .scalar()

            return {
                "practice_count": practice_count,
                "total_duration": round(total_duration, 2),  # 保留一位小数
                "scenario_count": scenario_count
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))