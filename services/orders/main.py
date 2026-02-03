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
    width: float | None = Form(None),
    length: float | None = Form(None),
    height: float | None = Form(None),
    material: str | None = Form(None),
    infill: str | None = Form(None),
    real_weight: str | None = Form(None),
    user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Convert to floats if possible
    width = float(width) if width else None
    length = float(length) if length else None
    height = float(height) if height else None
    infill = float(infill) if infill else None
    real_weight = float(real_weight) if real_weight else None
    file_path = None
    if file:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    
    # Validation
    if any(dim is not None and (dim < 1 or dim > 500) for dim in [width, length, height]):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Габарити повинні бути від 1 до 500 мм")
    if real_weight is not None and (real_weight < 0 or real_weight > 10000):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Вага повинна бути від 0 до 10000 г")
    if infill is not None and (infill < 0 or infill > 100):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Заповнення повинно бути від 0 до 100%")

    from .pricing import calculate_order_price
    result = calculate_order_price(
        width=width, length=length, height=height,
        material=material, infill=infill, real_weight=real_weight
    )
    price = result["price"]

    order = crud.create_order(
        db, user_email, description, file_path, color, size, price,
        width, length, height, material, infill, real_weight
    )
    return {
        "message": "Order created", 
        "order_id": order.id, 
        "file_path": file_path,
        "price": order.price,
        "currency": "UAH"
    }

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
            "price": o.price,
            "material": o.material,
            "width": o.width,
            "length": o.length,
            "height": o.height,
            "infill": o.infill,
            "real_weight": o.real_weight,
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

@app.get("/calculate_price")
def calculate_price(
    width: float | None = None,
    length: float | None = None,
    height: float | None = None,
    material: str | None = None,
    infill: str | None = None,
    real_weight: str | None = None
):
    # Convert to floats if possible
    width = float(width) if width else None
    length = float(length) if length else None
    height = float(height) if height else None
    infill = float(infill) if infill else None
    real_weight = float(real_weight) if real_weight else None
    from .pricing import calculate_order_price
    return calculate_order_price(
        width=width, length=length, height=height,
        material=material, infill=infill, real_weight=real_weight
    )
