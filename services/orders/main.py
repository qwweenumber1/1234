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

    # PRICE = max(W, (X×Y×Z/1000)×ρ) × P × K(I)
    # ρ = 1.24
    rho = 1.24
    
    # Defaults in case fields are missing
    X = width or 0
    Y = length or 0
    Z = height or 0
    W = real_weight or 0
    I = infill or 20 # Default infill 20%
    
    # Material Pricing (P) - Average Ukraine prices per gram
    material_prices = {
        "PLA": 1.2,
        "ABS": 1.5,
        "PETG": 1.4,
        "TPU": 3.0,
        "Nylon": 4.5,
        "SLA": 10.0
    }
    P = material_prices.get(material, 1.2) # Default to PLA price
    
    # Infill Coefficient K(I)
    K_I = 0.2 + 0.8 * (I / 100)
    
    # Volumetric Weight Wv
    V_cm3 = (X * Y * Z) / 1000
    Wv = V_cm3 * rho
    
    # Base Weight Wb
    Wb = max(W, Wv)
    
    # Final Price
    calculated_price = Wb * P * K_I
    
    # Minimum price check
    # 200 UAH for PLA, ABS, PETG
    # 500 UAH for TPU, Nylon, SLA
    min_price = 200
    if material in ["TPU", "Nylon", "SLA"]:
        min_price = 500
        
    price = max(min_price, int(calculated_price))

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
    # Logic for price calculation (consistent with create_order)
    rho = 1.24
    X = width or 0
    Y = length or 0
    Z = height or 0
    W = real_weight or 0
    I = infill or 20
    
    material_prices = {
        "PLA": 1.2, "ABS": 1.5, "PETG": 1.4, "TPU": 3.0, "Nylon": 4.5, "SLA": 10.0
    }
    P = material_prices.get(material, 1.2)
    K_I = 0.2 + 0.8 * (I / 100)
    V_cm3 = (X * Y * Z) / 1000
    Wv = V_cm3 * rho
    Wb = max(W, Wv)
    calculated_price = Wb * P * K_I
    
    min_price = 200
    if material in ["TPU", "Nylon", "SLA"]:
        min_price = 500
        
    price = max(min_price, int(calculated_price))
    return {"price": price, "currency": "UAH"}
