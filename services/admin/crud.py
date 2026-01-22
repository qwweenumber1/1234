from sqlalchemy.orm import Session
from services.orders.models import Order

def get_all_orders(db: Session, email_filter: str = None):
    query = db.query(Order)
    if email_filter:
        query = query.filter(Order.user_email.like(f"%{email_filter}%"))
    return query.order_by(Order.created_at.desc()).all()

def update_order_status(db: Session, order_id: int, status: str):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = status
        db.commit()
    return order

def delete_order(db: Session, order_id: int):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        db.delete(order)
        db.commit()
    return order
