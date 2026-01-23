from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///c:/ggg/data/orders.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # для SQLite
)

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
        conn = sqlite3.connect("c:/ggg/data/orders.db")
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
