from fastapi import FastAPI
from app.routes.forecast_routes import router as forecast_router

app = FastAPI(
    title="Restaurant ERP Forecast API"
)

@app.get("/")
def root():
    return {
        "message": "Forecast API is running",
        "forecast_url": "/api/forecast",
        "docs": "/docs",
    }

app.include_router(
    forecast_router,
    prefix="/api/forecast",
    tags=["Forecast"]
)