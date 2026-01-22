# services/auth/main.py
from fastapi import FastAPI, Form, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from .models import Base, User
from .crud import get_user_by_email, create_user
from .security import verify_password, hash_password, create_access_token, decode_access_token
from .database import engine, SessionLocal

import uuid
import re

# ... Инициализация ---
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Auth Service")


# --- DB зависимость ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Регистрация ---
@app.post("/register")
def register(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already exists")

    # English-only password validation
    if not re.match(r"^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]+$", password):
        raise HTTPException(status_code=400, detail="Password must contain only English characters and symbols")

    hashed = hash_password(password)
    verification_token = str(uuid.uuid4())
    user = create_user(db, email, hashed, verification_token=verification_token)

    # создаём токен сразу после регистрации
    token = create_access_token({"sub": user.email, "role": user.role})

    return JSONResponse(
        content={
            "message": "Registration successful. Please verify your email.",
            "access_token": token,
            "token_type": "bearer",
            "verification_token": verification_token,
            "user": {"email": user.email, "role": user.role, "is_verified": user.is_verified}
        }
    )

@app.get("/verify/{token}")
def verify(token: str, db: Session = Depends(get_db)):
    from .crud import verify_user
    if verify_user(db, token):
        return {"message": "Email verified successfully"}
    raise HTTPException(status_code=400, detail="Invalid or expired token")


# --- Логин ---
@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email, "role": user.role})

    return JSONResponse(
        content={
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "user": {"email": user.email, "role": user.role, "is_verified": user.is_verified}
        }
    )


# --- /me для проверки токена ---
@app.get("/me")
def me(access_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    payload = decode_access_token(access_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_email(db, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {"email": user.email, "role": user.role, "is_verified": user.is_verified}


@app.post("/logout")
def logout(response: JSONResponse):
    content = {"message": "Logged out successfully"}
    response = JSONResponse(content=content)
    response.delete_cookie("access_token")
    return response
