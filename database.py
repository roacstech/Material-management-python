import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

APP_ENV = os.getenv("APP_ENV", "development")

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

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()