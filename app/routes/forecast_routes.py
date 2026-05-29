from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.forecast_service import ForecastService

router = APIRouter()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_stock_forecast(
    type: str = Query("weekly", regex="^(daily|weekly|monthly|custom)$"),
    months: int = Query(1, ge=1),
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    - type: daily | weekly | monthly | custom
    - months: forecast horizon in months (used for monthly forecasts)
    - startDate / endDate: required when type=custom (ISO date YYYY-MM-DD)
    """

    return ForecastService.get_forecast(
        db=db,
        forecast_type=type,
        months=months,
        start_date=startDate,
        end_date=endDate,
    )