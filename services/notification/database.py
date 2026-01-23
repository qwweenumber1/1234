from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = "sqlite:///c:/ggg/data/notifications.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Папка для логов (по желанию)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
