import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


from dotenv import load_dotenv

# Load root .env
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

class DashboardSettings(BaseSettings):
    APP_NAME: str = "SnapHelp Ticket Dashboard"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "snaphelp-super-secret-key-2026"
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_FILE: Path = BASE_DIR / "app" / "storage" / "data.json"
    
    # PostgreSQL Async connection string
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgrespassword@localhost:5437/snaphelp_db"
    )

    # Discord OAuth2
    DISCORD_CLIENT_ID: str = os.getenv("CLIENT_ID", "")
    DISCORD_CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "")
    DISCORD_REDIRECT_URI: str = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    model_config = SettingsConfigDict(
        env_prefix="DASHBOARD_",
        extra="ignore"
    )


settings = DashboardSettings()
