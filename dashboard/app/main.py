import sys
from pathlib import Path

# Add dashboard root directory to sys.path
dashboard_root = Path(__file__).resolve().parent.parent
if str(dashboard_root) not in sys.path:
    sys.path.insert(0, str(dashboard_root))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routers import web_router, auth

app = FastAPI(
    title=settings.APP_NAME,
    description="Управление тикетами и настройками Discord бота SnapHelp",
    version="1.0.0"
)

# Static files mount
static_path = dashboard_root / "static"
if not static_path.exists():
    static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(web_router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
