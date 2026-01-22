import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'auth.db')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    is_verified = Column(Integer, default=0)
    verification_token = Column(String(255), nullable=True)

def promote():
    db = SessionLocal()
    email = "maksimnigmatov@gmail.com"
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.role = "admin"
        db.commit()
        print(f"Successfully promoted {email} to admin.")
    else:
        print(f"Failed to find user {email}. Please ensure they are registered.")
    db.close()

if __name__ == "__main__":
    promote()
