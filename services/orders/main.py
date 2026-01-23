import os, shutil
from fastapi import FastAPI, Form, UploadFile, File, Depends
from sqlalchemy.orm import Session
from .database import get_db, Base, engine
from . import crud
from .security import get_current_user

app = FastAPI(title="Orders Service")

@app.get("/health")
def health():
    return {"status": "ok", "service": "orders"}
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Run migrations
from .database import check_and_migrate
check_and_migrate()

Base.metadata.create_all(bind=engine)

@app.post("/create_order")
async def create_order(
    description: str = Form(...),
    file: UploadFile | None = File(None),
    color: str | None = Form(None),
    size: str | None = Form(None),
    user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_path = None
    if file:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

    order = crud.create_order(db, user_email, description, file_path, color, size)
    return {"message": "Order created", "order_id": order.id, "file_path": file_path}

@app.get("/orders")
def get_orders(user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = crud.get_orders_by_user(db, user_email)
    return {"orders": [
        {
            "id": o.id, 
            "description": o.description, 
            "status": o.status,
            "file_path": o.file_path, 
            "color": o.color, 
            "size": o.size, 
            "created_at": o.created_at.isoformat() if o.created_at else None
        } 
        for o in orders
    ]}

@app.delete("/orders/{order_id}")
def delete_order(order_id: int, user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    success = crud.delete_order(db, order_id, user_email)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found or not owned by user")
    return {"message": "Order deleted"}


