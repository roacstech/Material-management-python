import os
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = (
    f"mysql+pymysql://"
    f"{os.getenv('DEV_DB_USER', 'root')}:"
    f"{os.getenv('DEV_DB_PASS', '')}@"
    f"{os.getenv('DEV_DB_HOST', '127.0.0.1')}:"
    f"{os.getenv('DEV_DB_PORT', '3306')}/"
    f"{os.getenv('DEV_DB_NAME', 'material')}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()