from fastapi import FastAPI, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, Payment
from random import choice

# --- Настройка базы данных ---
DATABASE_URL = "sqlite:///c:/ggg/data/payments.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# --- Создание таблиц ---
Base.metadata.create_all(bind=engine)

# --- Инициализация FastAPI ---
app = FastAPI(title="Payment Service")

# --- Dependency для сессии ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Тестовый маршрут ---
@app.get("/")
def root():
    return {"message": "Payment service is running"}

# --- Эндпоинт для оплаты ---
@app.post("/pay")
def pay(
    user_email: str = Form(...),
    order_id: int = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    """
    Симуляция платежа.
    В реальном мире здесь будет подключение к Stripe/PayPal.
    """
    status = choice(["success", "failed"])

    # Создаём запись в базе
    payment = Payment(user_email=user_email, order_id=order_id, amount=amount, status=status)
    db.add(payment)
    db.commit()
    db.refresh(payment)

    if status == "failed":
        raise HTTPException(status_code=400, detail="Payment failed")

    return {"status": status, "message": "Payment successful", "payment_id": payment.id}
