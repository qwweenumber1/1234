from sqlalchemy import Column, Integer, String, DateTime, Float
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
    price = Column(Float, nullable=True)  # Price in UAH
    width = Column(Float, nullable=True)  # X (mm)
    length = Column(Float, nullable=True) # Y (mm)
    height = Column(Float, nullable=True) # Z (mm)
    material = Column(String, nullable=True)
    infill = Column(Float, nullable=True) # %
    real_weight = Column(Float, nullable=True) # W (g)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
