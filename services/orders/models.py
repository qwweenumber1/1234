from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .database import Base  # только Base, не get_db!

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    color = Column(String, nullable=True)
    size = Column(String, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
