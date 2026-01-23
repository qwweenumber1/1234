from fastapi import FastAPI, Form, Depends, HTTPException, Cookie, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import smtplib
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .models import Base, Notification

# Database setup
DATABASE_URL = os.getenv("NOTIFICATION_DATABASE_URL", "sqlite:///./notification.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notification Service")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok", "service": "notification"}

# --- SMTP Config ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "3dsmartservices@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "bsky kbpc uhjq ssxv")

class CircuitBreaker:
    def __init__(self):
        self.failed_attempts = 0
        self.max_failures = 3
        self.cooldown_time = 900
        self.last_failure_time = 0

    def is_open(self):
        if self.failed_attempts >= self.max_failures:
            current_time = time.time()
            if current_time - self.last_failure_time < self.cooldown_time:
                return True
            else:
                self.failed_attempts = 0
        return False

    def record_failure(self):
        self.failed_attempts += 1
        self.last_failure_time = time.time()

    def record_success(self):
        self.failed_attempts = 0

cb = CircuitBreaker()

def build_themed_email(title, greeting, message, action_url=None, action_text=None):
    """Generates a professionally styled HTML email."""
    
    # Styles
    bg_color = "#ffffff"
    content_bg = "#ffffff"
    primary_color = "#a3d392"  # The brand light green
    dark_green = "#263a24"
    text_color = "#2f2f2f"
    footer_color = "#6b6b6b"
    
    action_button = ""
    if action_url and action_text:
        action_button = f'''
        <div style="margin: 30px 0; text-align: center;">
            <a href="{action_url}" style="background-color: {primary_color}; color: #000000; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; font-size: 18px; box-shadow: 0 4px 10px rgba(163, 211, 146, 0.4);">
                {action_text}
            </a>
        </div>
        '''

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: 'Segoe UI', Roboto, Arial, sans-serif; background-color: {bg_color}; margin: 0; padding: 0; color: {text_color}; line-height: 1.6;">
        <div style="max-width: 600px; margin: 40px auto; background: {content_bg}; border: 1px solid #e0eee0; border-radius: 20px; overflow: hidden;">
            <div style="background-color: {primary_color}; padding: 40px 20px; text-align: center; border-bottom: 5px solid #8bbb7a;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 800; letter-spacing: 3px; color: #000000; text-transform: uppercase;">SMART 3D</h1>
            </div>
            <div style="padding: 40px;">
                <h2 style="color: {dark_green}; margin-top: 0; font-weight: 700; font-size: 22px;">{title}</h2>
                <p style="font-size: 16px;">{greeting},</p>
                <p style="font-size: 16px; color: #4b4848;">{message}</p>
                {action_button}
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="margin: 0; font-weight: 700; color: {dark_green};">З повагою,</p>
                    <p style="margin: 0; color: {dark_green};">Команда Smart 3D Professionals</p>
                </div>
            </div>
            <div style="padding: 25px; text-align: center; font-size: 13px; color: {footer_color}; background-color: #f9fbf9;">
                <p style="margin: 0;">&copy; 2026 Smart 3D. Всі права захищені.</p>
                <div style="margin-top: 10px;">
                    <a href="#" style="color: {dark_green}; text-decoration: underline;">Підтримка</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

def send_html_email(to_email: str, subject: str, html_body: str):
    if cb.is_open():
        print("SMTP Circuit Breaker is OPEN. Skipping email.")
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
    except Exception as e:
        print(f"Error sending email: {e}")
        cb.record_failure()
        return False

@app.post("/notify")
def notify(user_email: str = Form(...), message: str = Form(...), db: Session = Depends(get_db)):
    notification = Notification(user_email=user_email, message=message)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return {"status": "sent", "notification_id": notification.id}

@app.post("/send-verification")
def send_verification(background_tasks: BackgroundTasks, email: str = Form(...), token: str = Form(...), base_url: str = Form("http://127.0.0.1:8000"), db: Session = Depends(get_db)):
    link = f"{base_url}/verify/{token}"
    html_body = build_themed_email(
        "Підтвердження реєстрації",
        "Вітаємо",
        "Дякуємо за реєстрацію у Smart 3D Professionals! Будь ласка, підтвердіть вашу електронну адресу, щоб отримати доступ до всіх можливостей нашого сервісу.",
        link,
        "Підтвердити Email"
    )
    
    def do_send():
        success = send_html_email(email, "Smart 3D - Підтвердження реєстрації", html_body)
        notification = Notification(user_email=email, message=f"Verification email sent", status="sent" if success else "failed")
        with SessionLocal() as session:
            session.add(notification)
            session.commit()

    background_tasks.add_task(do_send)
    return {"status": "processing"}

@app.post("/send-contact-email")
def send_contact_email(background_tasks: BackgroundTasks, name: str = Form(...), email: str = Form(...), subject: str = Form(...), message: str = Form(...)):
    admin_email = SMTP_USER 
    html_body = build_themed_email(
        f"Новий запит: {subject}",
        "Адміністратор",
        f"Отримано нове повідомлення від клієнта <strong>{name}</strong> ({email}):<br><br>{message}"
    )
    def do_send():
        send_html_email(admin_email, f"Запит від клієнта: {subject}", html_body)
    background_tasks.add_task(do_send)
    return {"status": "processing"}

@app.post("/send-status-update")
def send_status_update(background_tasks: BackgroundTasks, email: str = Form(...), order_id: int = Form(...), new_status: str = Form(...), base_url: str = Form("http://127.0.0.1:8000")):
    html_body = build_themed_email(
        f"Оновлення статусу замовлення #{order_id}",
        "Вітаємо",
        f"Статус вашого замовлення #{order_id} було змінено на: <strong>{new_status}</strong>. Ви можете перевірити деталі у вашому кабінеті.",
        f"{base_url}/orders_page",
        "Переглянути замовлення"
    )
    def do_send():
        send_html_email(email, f"Smart 3D - Оновлення статусу замовлення #{order_id}", html_body)
    background_tasks.add_task(do_send)
    return {"status": "processing"}

@app.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    # Note: In the restored standalone service, we might need a way to filter by user
    # but for now I'll just return based on what the gateway sends if it sends email
    notes = db.query(Notification).order_by(Notification.created_at.desc()).all()
    return [{"id": n.id, "message": n.message, "status": n.status, "created_at": n.created_at} for n in notes]
