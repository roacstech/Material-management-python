from sqlalchemy import Column, Integer, Numeric, Boolean
from app.database import Base

class StockForecastSetting(Base):
    __tablename__ = "stock_forecast_settings"

    setting_id = Column(Integer, primary_key=True)

    material_id = Column(Integer)

    safety_stock_days = Column(Numeric(5, 2))
    lead_time_days = Column(Numeric(5, 2))

    manual_avg_daily_usage = Column(Numeric(12, 3))

    lookback_days = Column(Integer)

    auto_forecast_enabled = Column(Boolean)