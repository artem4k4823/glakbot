from dotenv import load_dotenv
from pathlib import Path
import os
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy.orm import sessionmaker



env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgrespassword@localhost:5437/snaphelp_db"
)

# Создаем движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
