from datetime import datetime, timedelta
import re
import uuid
from fastapi import FastAPI, Form, Depends, HTTPException, Cookie
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from .models import Base, User
from .crud import get_user_by_email, create_user
from .security import verify_password, hash_password, create_access_token, decode_access_token, create_refresh_token, decode_refresh_token

# ... Инициализация ---
def run_migrations():
    import sqlite3
    from .database import DB_PATH
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        columns = [
            ("verification_token_expires_at", "DATETIME"),
            ("last_verification_request_at", "DATETIME"),
            ("verification_request_count", "INTEGER DEFAULT 0"),
            ("is_blocked", "INTEGER DEFAULT 0"),
            ("blocked_until", "DATETIME")
        ]
        for col_name, col_type in columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")

run_migrations()
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Auth Service")

@app.get("/health")
def health():
    return {"status": "ok", "service": "auth"}

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
        raise HTTPException(status_code=400, detail="Цей Email вже зареєстрований")

    # Minimum length validation
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Пароль має містити щонайменше 6 символів")

    # English-only password validation
    if not re.match(r"^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]+$", password):
        raise HTTPException(status_code=400, detail="Пароль має містити лише англійські літери та символи")

    hashed = hash_password(password)
    verification_token = str(uuid.uuid4())
    user = create_user(db, email, hashed, verification_token=verification_token)

    # создаём токены сразу после регистрации
    access_token = create_access_token({"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.email})

    return JSONResponse(
        content={
            "message": "Registration successful. Please verify your email.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "verification_token": verification_token,
            "user": {"email": user.email, "role": user.role, "is_verified": user.is_verified}
        }
    )

@app.post("/resend-verification")
def resend_verification(email: str = Form(...), db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User is already verified")

    now = datetime.utcnow()

    # Check if blocked
    if user.is_blocked:
        if user.blocked_until and user.blocked_until > now:
            remaining = int((user.blocked_until - now).total_seconds() / 60)
            raise HTTPException(status_code=429, detail=f"Too many attempts. Blocked for {remaining} more minutes.")
        else:
            # Block expired
            user.is_blocked = 0
            user.verification_request_count = 0
            user.blocked_until = None

    # Check cooldown (3 min)
    if user.last_verification_request_at:
        diff = now - user.last_verification_request_at
        if diff < timedelta(minutes=3):
            remaining = 180 - int(diff.total_seconds())
            raise HTTPException(status_code=429, detail=f"Please wait {remaining} seconds before requesting again.")

    # Increment count
    user.verification_request_count += 1
    
    # Block if reached limit (3)
    if user.verification_request_count >= 4: # 1st on reg + 3 resends? Or total 3?
        # Let's say total 3 requests (1 on reg + 2 resends)
        # User said "после третьего раза блокируеться" - after 3rd time.
        # So 1st (reg), 2nd (resend), 3rd (resend) -> block.
        user.is_blocked = 1
        user.blocked_until = now + timedelta(minutes=10)
        db.commit()
        raise HTTPException(status_code=429, detail="Maximum attempts reached. Blocked for 10 minutes.")

    # Generate new token
    new_token = str(uuid.uuid4())
    user.verification_token = new_token
    user.verification_token_expires_at = now + timedelta(minutes=3)
    user.last_verification_request_at = now
    
    db.commit()
    
    return {
        "message": "New verification link sent.",
        "verification_token": new_token,
        "email": user.email
    }

@app.get("/verify/{token}")
def verify(token: str, db: Session = Depends(get_db)):
    from .crud import verify_user
    if verify_user(db, token):
        return {"message": "Email verified successfully"}
    raise HTTPException(status_code=400, detail="Invalid or expired token")


# --- Логин ---
@app.post("/login")
def login(email: str = Form(None), username: str = Form(None), password: str = Form(...), db: Session = Depends(get_db)):
    login_id = email or username
    if not login_id:
        raise HTTPException(status_code=422, detail="Email or username is required")
    
    user = get_user_by_email(db, login_id)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.email})

    return JSONResponse(
        content={
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
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


@app.post("/refresh")
def refresh(refresh_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = get_user_by_email(db, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = create_access_token({"sub": user.email, "role": user.role})
    new_refresh_token = create_refresh_token({"sub": user.email})

    return JSONResponse(
        content={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }
    )


@app.post("/logout")
def logout():
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


