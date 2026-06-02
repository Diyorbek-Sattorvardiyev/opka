from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.analysis import Analysis
from models.user import User


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def ok(message: str, data):
    return {"success": True, "message": message, "data": data}


@router.get("/stats")
def stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = datetime.now(timezone.utc).date()
    period_start_day = today - timedelta(days=days - 1)
    period_start = datetime.combine(period_start_day, datetime.min.time(), tzinfo=timezone.utc)

    base = (
        select(Analysis)
        .where(Analysis.user_id == current_user.id, Analysis.created_at >= period_start)
        .subquery()
    )

    total_scans = db.scalar(select(func.count()).select_from(base)) or 0
    pneumonia_count = db.scalar(select(func.count()).select_from(base).where(base.c.pneumonia_detected.is_(True))) or 0
    normal_count = max(total_scans - pneumonia_count, 0)
    average_confidence = db.scalar(select(func.avg(base.c.confidence)).select_from(base)) or 0.0

    distribution = {"NORMAL": 0, "RISK": 0, "CRITICAL": 0}
    rows = db.execute(select(base.c.risk_level, func.count()).select_from(base).group_by(base.c.risk_level)).all()
    for risk_level, count in rows:
        if risk_level in distribution:
            distribution[risk_level] = count

    chart = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        count = db.scalar(
            select(func.count())
            .select_from(Analysis)
            .where(Analysis.user_id == current_user.id, Analysis.created_at >= start, Analysis.created_at < end)
        ) or 0
        chart.append({"date": day.isoformat(), "count": count})

    data = {
        "days": days,
        "total_scans": total_scans,
        "pneumonia_detected_count": pneumonia_count,
        "normal_count": normal_count,
        "average_confidence": round(float(average_confidence), 2),
        "last_7_days_chart": chart,
        "chart": chart,
        "risk_distribution": distribution,
    }
    return ok("Dashboard statistikasi", data)
