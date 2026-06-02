import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL

# Load .env
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Environment
APP_ENV = os.getenv("APP_ENV", "development")

# =========================
# DATABASE CONFIG
# =========================
if APP_ENV == "production":
    DB_USER = os.getenv("PROD_DB_USER")
    DB_PASS = os.getenv("PROD_DB_PASS")
    DB_HOST = os.getenv("PROD_DB_HOST")
    DB_PORT = os.getenv("PROD_DB_PORT", "3306")
    DB_NAME = os.getenv("PROD_DB_NAME")
else:
    DB_USER = os.getenv("DEV_DB_USER", "root")
    DB_PASS = os.getenv("DEV_DB_PASS", "")
    DB_HOST = os.getenv("DEV_DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DEV_DB_PORT", "3306")
    DB_NAME = os.getenv("DEV_DB_NAME", "material")

# =========================
# SAFE PASSWORD ENCODING
# =========================
DB_PASS_ENCODED = quote_plus(DB_PASS)

# =========================
# DATABASE URL
# =========================
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS_ENCODED}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Debug (safe)
print(
    f"Connecting to DB => "
    f"mysql+pymysql://{DB_USER}:****@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# =========================
# SQLALCHEMY ENGINE
# =========================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# =========================
# SESSION
# =========================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# =========================
# BASE MODEL
# =========================
Base = declarative_base()

# =========================
# DATABASE DEPENDENCY
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()