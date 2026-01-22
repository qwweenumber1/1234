from fastapi import FastAPI, Form, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .models import Notification, Base
from .database import engine, SessionLocal

# Init DB
Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SMTP Config ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "3dsmartservices@gmail.com"
SMTP_PASSWORD = "bsky kbpc uhjq ssxv"

# --- Circuit Breaker State ---
# This is a simple in-memory circuit breaker. 
# If auth fails 3 times, we stop trying for 15 minutes.
class CircuitBreaker:
    def __init__(self):
        self.failed_attempts = 0
        self.max_failures = 3
        self.cooldown_time = 900 # 15 minutes
        self.last_failure_time = 0

    def is_open(self):
        if self.failed_attempts >= self.max_failures:
            current_time = time.time()
            if current_time - self.last_failure_time < self.cooldown_time:
                return True
            else:
                # Cooldown finished, reset
                self.failed_attempts = 0
        return False

    def record_failure(self):
        self.failed_attempts += 1
        self.last_failure_time = time.time()

    def record_success(self):
        self.failed_attempts = 0

cb = CircuitBreaker()

def send_html_email(to_email: str, subject: str, html_body: str):
    if cb.is_open():
        print("SMTP Circuit Breaker is OPEN. Skipping email to prevent ban.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        cb.record_success()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Auth Error: {e}")
        cb.record_failure()
        return False
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Создать уведомление
@app.post("/notify")
def notify(user_email: str = Form(...), message: str = Form(...), db: Session = Depends(get_db)):
    notification = Notification(user_email=user_email, message=message)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    print(f"Notification record created for {user_email}")
    return {"status": "sent", "notification_id": notification.id}

@app.post("/send-verification")
def send_verification(background_tasks: BackgroundTasks, email: str = Form(...), token: str = Form(...), db: Session = Depends(get_db)):
    link = f"http://127.0.0.1:8000/verify/{token}"
    
    html_body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #4b8f3f; margin: 0; font-size: 28px;">Smart 3D</h1>
                <p style="color: #666; font-size: 16px;">Ваш партнер у світі 3D-друку</p>
            </div>
            
            <h2 style="font-size: 20px; color: #222; margin-bottom: 20px;">Вітаємо у Smart 3D!</h2>
            
            <p>Ви успішно пройшли перший етап реєстрації. Щоб активувати ваш акаунт та почати замовляти послуги, будь ласка, натисніть на кнопку нижче для підтвердження вашої пошти:</p>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{link}" style="background-color: #a3d392; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 18px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">Підтвердити пошту</a>
            </div>
            
            <p style="font-size: 14px; color: #888;">Якщо ви не реєструвалися на нашому сайті, просто проігноруйте цей лист.</p>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            
            <div style="text-align: center; color: #bbb; font-size: 12px;">
                <p>© 2026 Smart 3D. Всі права захищені.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    def do_send():
        success = send_html_email(email, "Smart 3D - Підтвердження реєстрації", html_body)
        notification = Notification(user_email=email, message=f"Verification email sent to {email}", status="sent" if success else "failed")
        with SessionLocal() as session:
            session.add(notification)
            session.commit()
            if success:
                print(f"Verification email sent to {email}")
            else:
                print(f"Failed to send email to {email} (Circuit Breaker or Auth Error)")

    background_tasks.add_task(do_send)
    return {"status": "processing"}

# Получить уведомления пользователя
@app.get("/notifications/{user_email}")
def get_notifications(user_email: str, db: Session = Depends(get_db)):
    notes = db.query(Notification).filter(Notification.user_email == user_email).order_by(Notification.created_at.desc()).all()
    return [{"id": n.id, "message": n.message, "status": n.status, "created_at": n.created_at} for n in notes]
