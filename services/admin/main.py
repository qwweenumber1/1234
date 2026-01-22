from fastapi import FastAPI, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from services.orders.database import SessionLocal, Base, engine
from .crud import get_all_orders, update_order_status, delete_order
from services.orders.models import Order

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/admin")
def admin_panel(email: str = "", db: Session = Depends(get_db)):
    orders = get_all_orders(db, email)
    return {
        "orders": [
            {
                "id": o.id,
                "user_email": o.user_email,
                "description": o.description,
                "status": o.status,
                "file_path": o.file_path,
                "color": o.color,
                "size": o.size,
                "created_at": o.created_at.isoformat() if o.created_at else None
            }
            for o in orders
        ]
    }

@app.post("/update_status/{order_id}")
def update_status(order_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    update_order_status(db, order_id, status)
    return {"message": "Status updated"}

@app.delete("/delete_order/{order_id}")
def delete(order_id: int, db: Session = Depends(get_db)):
    delete_order(db, order_id)
    return {"message": "Order deleted"}
