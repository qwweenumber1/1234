from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, relationship
from .database import Base



class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user")  # user | admin
    is_verified = Column(Integer, default=0)    # 0 for False, 1 for True (SQLite compatible)
    verification_token = Column(String(255), nullable=True)
