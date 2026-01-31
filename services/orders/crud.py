from datetime import datetime
from sqlalchemy.orm import Session
from .models import Order

def create_order(
    db: Session, 
    user_email: str, 
    description: str, 
    file_path: str | None = None, 
    color: str | None = None, 
    size: str | None = None, 
    price: float | None = None,
    width: float | None = None,
    length: float | None = None,
    height: float | None = None,
    material: str | None = None,
    infill: float | None = None,
    real_weight: float | None = None
):
    order = Order(
        user_email=user_email, 
        description=description, 
        file_path=file_path, 
        color=color, 
        size=size, 
        price=price,
        width=width,
        length=length,
        height=height,
        material=material,
        infill=infill,
        real_weight=real_weight,
        created_at=datetime.utcnow()
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

def get_orders_by_user(db: Session, user_email: str):
    return db.query(Order).filter(Order.user_email == user_email).order_by(Order.created_at.desc()).all()

def delete_order(db: Session, order_id: int, user_email: str):
    order = db.query(Order).filter(Order.id == order_id, Order.user_email == user_email).first()
    if order:
        db.delete(order)
        db.commit()
        return True
    return False
