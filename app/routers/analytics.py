from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..analytics import status_chart_png, summary
from ..database import get_db
from ..deps import get_current_user
from ..models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return summary(db)


@router.get("/status-chart")
def get_status_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    png = status_chart_png(db)
    return Response(content=png, media_type="image/png")
