from fastapi import FastAPI, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import httpx
import os
from services.orders.database import get_db
from . import crud

app = FastAPI(title="Admin Service")

@app.get("/health")
def health():
    return {"status": "ok", "service": "admin"}

@app.get("/")
def admin_panel(email: str = "", db: Session = Depends(get_db)):
    orders = crud.get_all_orders(db, email)
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
async def update_status(background_tasks: BackgroundTasks, order_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    print(f"DEBUG: Updating order {order_id} to status {status}")
    order = crud.update_order_status(db, order_id, status)
    if order:
        print(f"DEBUG: Order {order_id} found and updated")
    else:
        print(f"DEBUG: Order {order_id} NOT FOUND")
    if order and order.user_email:
        # Trigger notification via Notification Service
        NOTIFICATION_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://127.0.0.1:8004") + "/send-status-update"
        
        async def notify():
            try:
                base_url = "http://127.0.0.1:8000" 
                async with httpx.AsyncClient() as client:
                    await client.post(NOTIFICATION_URL, data={
                        "email": order.user_email,
                        "order_id": order_id,
                        "new_status": status,
                        "base_url": base_url
                    })
            except Exception as e:
                print(f"Error triggering status notification: {e}")
        
        background_tasks.add_task(notify)
        
    return {"message": "Status updated"}

@app.delete("/delete_order/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.delete_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted"}
