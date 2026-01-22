from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import httpx
import os
from datetime import datetime

app = FastAPI(title="API Gateway")

app.mount("/uploaded_files", StaticFiles(directory="uploaded_files"), name="uploaded_files")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# ================= SERVICES =================
SERVICES = {
    "auth": "http://127.0.0.1:8005",
    "orders": "http://127.0.0.1:8001",
    "payment": "http://127.0.0.1:8003",
    "notification": "http://127.0.0.1:8004",
    "admin": "http://127.0.0.1:8006",
}

# ================= UPLOADS =================
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ================= PROXY =================
async def proxy_request(service: str, path: str, request: Request, method: str = "GET", data=None, files=None):
    url = SERVICES[service] + path
    cookies = {}
    token = request.cookies.get("access_token")
    if token:
        cookies["access_token"] = token

    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method.upper() == "GET":
                resp = await client.get(url, cookies=cookies)
            elif method.upper() == "POST":
                resp = await client.post(url, data=data, files=files, cookies=cookies)
            elif method.upper() == "DELETE":
                resp = await client.delete(url, cookies=cookies)
            else:
                # For other methods/generic fallback
                resp = await client.request(method, url, data=data, files=files, cookies=cookies)
            
            # We don't raise_for_status here so we can forward the error code
        except httpx.RequestError as e:
            return {"detail": f"Request error: {str(e)}"}, 503
        
    try:
        return resp.json(), resp.status_code
    except Exception:
        return {"detail": resp.text}, resp.status_code

# ================= FRONTEND =================
def get_html(name: str):
    path = os.path.join("frontend", "templates", name)
    if not os.path.exists(path):
        return HTMLResponse("<h1>HTML not found</h1>", 404)
    with open(path, encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/", response_class=HTMLResponse)
def index(): return get_html("index.html")

@app.get("/register_page", response_class=HTMLResponse)
def register_page(): return get_html("register.html")

@app.get("/login_page", response_class=HTMLResponse)
def login_page(): return get_html("login.html")

@app.get("/orders_page", response_class=HTMLResponse)
def orders_page(): return get_html("orders.html")

@app.get("/admin_page", response_class=HTMLResponse)
def admin_page(): return get_html("admin.html")

# ================= AUTH =================
@app.post("/register")
async def register(request: Request):
    form = await request.form()
    async with httpx.AsyncClient() as client:
        resp = await client.post(SERVICES["auth"] + "/register", data=form)
    if resp.status_code != 200:
        try:
            return JSONResponse(resp.json(), resp.status_code)
        except Exception:
            return JSONResponse({"detail": resp.text}, resp.status_code)
    
    auth_data = resp.json()
    token = auth_data["access_token"]
    v_token = auth_data.get("verification_token")
    email = auth_data["user"]["email"]

    # Call notification service to "send" email
    if v_token:
        async with httpx.AsyncClient() as client:
            await client.post(SERVICES["notification"] + "/send-verification", data={"email": email, "token": v_token}, timeout=10.0)

    response = RedirectResponse("/registration_success", status_code=303)
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    return response

@app.get("/registration_success", response_class=HTMLResponse)
def registration_success():
    return get_html("registration_success.html")

@app.get("/contacts", response_class=HTMLResponse)
def contacts_page():
    return get_html("contacts.html")

@app.post("/contacts")
async def handle_contacts(request: Request):
    form = await request.form()
    # Forward to notification service
    # The notification service will send an email to the admin (you)
    async with httpx.AsyncClient() as client:
        await client.post(SERVICES["notification"] + "/send-contact-email", data=form, timeout=20.0)
    return JSONResponse({"status": "sent"})

@app.get("/verify/{token}")
async def verify_email(token: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(SERVICES["auth"] + f"/verify/{token}")
    if resp.status_code == 200:
        return get_html("verification_verified.html")
    return HTMLResponse(f"<h1>Verification failed</h1><p>{resp.json().get('detail')}</p>", status_code=resp.status_code)

@app.post("/login")
async def login(request: Request):
    form = await request.form()
    async with httpx.AsyncClient() as client:
        resp = await client.post(SERVICES["auth"] + "/login", data=form)
    if resp.status_code != 200:
        try:
            return JSONResponse(resp.json(), resp.status_code)
        except Exception:
            return JSONResponse({"detail": resp.text}, resp.status_code)
    token = resp.json()["access_token"]
    response = RedirectResponse("/orders_page", status_code=303)
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    return response

@app.get("/me")
async def me(request: Request):
    data, status_code = await proxy_request("auth", "/me", request)
    return JSONResponse(data, status_code=status_code)

@app.post("/logout")
async def logout():
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("access_token", path="/", domain=None)
    return response

# ================= ORDERS =================
@app.get("/orders")
async def orders(request: Request):
    data, status_code = await proxy_request("orders", "/orders", request)
    return JSONResponse(data, status_code=status_code)

@app.delete("/orders/{order_id}")
async def delete_order(order_id: int, request: Request):
    data, status_code = await proxy_request("orders", f"/orders/{order_id}", request, method="DELETE")
    return JSONResponse(data, status_code=status_code)

@app.post("/create_order")
async def create_order(request: Request):
    # Check if user is verified
    user_data, status_code = await proxy_request("auth", "/me", request)
    if status_code != 200:
        return JSONResponse(user_data, status_code)
    
    if not user_data.get("is_verified"):
        return JSONResponse({"detail": "Please verify your email to create orders."}, status_code=403)

    form = await request.form()
    data = {}
    files = {}

    for key, value in form.items():
        # Check if it's a file (UploadFile)
        if hasattr(value, "filename"):
            if value.filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{value.filename}"
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(await value.read())
                files = {"file": (filename, open(filepath, "rb"), value.content_type)}
            # If no filename (empty selection), strictly ignore it. Do not add to data.
        else:
            data[key] = value

    # Force multipart if no files
    if not files:
        files["_force_multipart"] = (None, b"")

    result, status_code = await proxy_request("orders", "/create_order", request, method="POST", data=data, files=files)
    return JSONResponse(result, status_code=status_code)

# ================= PAYMENT =================
@app.post("/payment/pay")
async def pay(request: Request):
    form = await request.form()
    data, status_code = await proxy_request("payment", "/pay", request, method="POST", data=form)
    return JSONResponse(data, status_code=status_code)

# ================= NOTIFICATION =================
@app.get("/notifications")
async def notifications(request: Request):
    data, status_code = await proxy_request("notification", "/notifications", request)
    return JSONResponse(data, status_code=status_code)

# ================= ADMIN =================
@app.get("/admin")
async def admin_dashboard(request: Request):
    # Pass 'email' query param if present
    email = request.query_params.get("email")
    path = f"/admin?email={email}" if email else "/admin"
    data, status_code = await proxy_request("admin", path, request)
    return JSONResponse(data, status_code=status_code)

@app.post("/admin/update_status/{order_id}")
async def update_status(order_id: int, request: Request):
    form = await request.form()
    data, status_code = await proxy_request("admin", f"/update_status/{order_id}", request, method="POST", data=form)
    return JSONResponse(data, status_code=status_code)

@app.delete("/admin/delete_order/{order_id}")
async def admin_delete_order(order_id: int, request: Request):
    data, status_code = await proxy_request("admin", f"/delete_order/{order_id}", request, method="DELETE")
    return JSONResponse(data, status_code=status_code)
