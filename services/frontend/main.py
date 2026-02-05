from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

app = FastAPI(title="Frontend Service")

# Mount static files
# We assume this service runs from the root or can access the frontend folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))

def get_html(name: str, request: Request):
    # Check if the request is an AJAX request (for SPA)
    is_spa = request.headers.get("X-SPA") == "true" or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    response = templates.TemplateResponse(name, {"request": request, "is_spa": is_spa})
    response.headers["Vary"] = "X-SPA, X-Requested-With"
    return response

@app.get("/", response_class=HTMLResponse)
async def index(request: Request): return get_html("index.html", request)

@app.get("/info", response_class=HTMLResponse)
async def info_page(request: Request): return get_html("info.html", request)

@app.get("/register_page", response_class=HTMLResponse)
async def register_page(request: Request): return get_html("register.html", request)

@app.get("/register_error", response_class=HTMLResponse)
async def register_error(request: Request): return get_html("register_error.html", request)

@app.get("/login_page", response_class=HTMLResponse)
async def login_page(request: Request): return get_html("login.html", request)

@app.get("/login_error", response_class=HTMLResponse)
async def login_error(request: Request): return get_html("login_error.html", request)

@app.get("/orders_page", response_class=HTMLResponse)
async def orders_page(request: Request): return get_html("orders.html", request)

@app.get("/admin_page", response_class=HTMLResponse)
async def admin_page(request: Request): return get_html("admin.html", request)

@app.get("/registration_success", response_class=HTMLResponse)
async def registration_success(request: Request):
    return get_html("registration_success.html", request)

@app.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request):
    return get_html("contacts.html", request)

@app.get("/verify/{token}", response_class=HTMLResponse)
async def verify_page(request: Request, token: str):
    # This might need to check with auth service? 
    # Or just show a loading page that calls auth via JS?
    # Usually verification is a redirection or a simple result page.
    # For now, let's keep it consistent with what gateway had.
    return get_html("verification_verified.html", request) # Note: Gateway had logic here.

@app.get("/health")
def health():
    return {"status": "ok", "service": "frontend"}
