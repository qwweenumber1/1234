from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "orders.db").replace("\\", "/")
DATABASE_URL = f"sqlite:///{DB_PATH}"

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Dependency для FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_and_migrate():
    # Simple migration logic for SQLite
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check/Add color
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN color VARCHAR")
        except sqlite3.OperationalError:
            pass # Already exists
            
        # Check/Add size
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN size VARCHAR")
        except sqlite3.OperationalError:
            pass # Already exists

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")
