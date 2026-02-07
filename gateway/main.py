from fastapi import FastAPI, Request, UploadFile, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse


from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os
from datetime import datetime
import asyncio
import logging

# --- User configuration ---
server = '127.0.0.1'
port = 8010

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Gateway")


class RequestCompiler:
    def validate_request_format(self, data: any) -> bool:
        # Check if Format is valid.
        if data is None: return True
        if isinstance(data, (int, str, float, bool)): return True
        if isinstance(data, (dict, list)): return True
        
        # Handle Starlette/FastAPI specific data types
        try:
            from starlette.datastructures import FormData
            if isinstance(data, FormData): return True
        except ImportError:
            pass
            
        return False

    def compile_request(self, data: any) -> any:
        if self.validate_request_format(data):
            return data
        return None

    def validate_response_format(self, data: any) -> bool:
        # data is httpx.Response object
        if hasattr(data, 'status_code'):
            # Simple check: Is it a valid HTTP response?
            # User mentioned "invalid format... return error or None"
            # We can check content-type or just status
            return True
        return False

    def compile_response(self, data: any) -> any:
        # Validate or Compile response
        return data

compiler = RequestCompiler()

class ConnectionKeeper:
    def __init__(self):
        self.working = True
        
    async def start(self):
        self.working = True
        asyncio.create_task(self._ping_loop())
        logger.info(f"ConnectionKeeper started for {server}:{port}")

    async def stop(self):
        self.working = False
        logger.info("ConnectionKeeper stopped")

    async def _ping_loop(self):
        logger.info("Starting ping loop")
        while self.working:
            try:
                await self.ping()
            except Exception as e:
                logger.error(f"Error in ping loop: {e}")
            await asyncio.sleep(5)

    async def ping(self):
        try:
            # Attempt to connect with a timeout
            future = asyncio.open_connection(server, port)
            reader, writer = await asyncio.wait_for(future, timeout=3.0)
            
            # Connection successful
            # logger.info(f"Ping active: Connected to {server}:{port}")
            
            writer.close()
            await writer.wait_closed()
        except asyncio.TimeoutError:
            logger.error(f"Ping timeout: Could not connect to {server}:{port} within 3s")
        except Exception as e:
            logger.error(f"Ping failed: {e}")

connection_keeper = ConnectionKeeper()


# Rate Limiter Logic
class RateLimiter:
    def __init__(self):
        self.ip_stats = {}  # {ip: {'reqs': [timestamps], 'blocked_until': timestamp}}

    def check_request(self, ip: str) -> bool:
        now = datetime.now().timestamp()
        
        if ip not in self.ip_stats:
            self.ip_stats[ip] = {'reqs': [], 'blocked_until': 0}
        
        stats = self.ip_stats[ip]
        
        # Check if blocked
        if stats['blocked_until'] > now:
            remaining = int(stats['blocked_until'] - now)
            # logger.warning(f"IP {ip} is blocked for {remaining}s")
            return False

        # Clean old requests (older than 1s)
        stats['reqs'] = [t for t in stats['reqs'] if now - t < 1.0]
        
        # Add new request
        stats['reqs'].append(now)
        
        # Check rate
        if len(stats['reqs']) > 20:  # Increased limit to 20 req/s
            stats['blocked_until'] = now + 3600  # Block for 1 hour
            logger.warning(f"IP {ip} blocked for 1 hour (Rate limit exceeded: {len(stats['reqs'])} req/s)")
            return False
            
        return True

limiter = RateLimiter()

app = FastAPI(title="API Gateway")

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Exclude static files from rate limiting
    if request.url.path.startswith("/static"):
        return await call_next(request)

    client_ip = request.client.host
    if not limiter.check_request(client_ip):
        return JSONResponse(
            status_code=429, 
            content={"detail": "Too many requests. You are blocked for 1 hour."}
        )
    response = await call_next(request)
    return response


@app.on_event("startup")
async def startup_event():
    await connection_keeper.start()

@app.on_event("shutdown")
async def shutdown_event():
    await connection_keeper.stop()

app.mount("/uploaded_files", StaticFiles(directory="uploaded_files"), name="uploaded_files")

# ================= SERVICES =================
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8005"),
    "orders": os.getenv("ORDERS_SERVICE_URL", "http://127.0.0.1:8001"),
    "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://127.0.0.1:8004"),
    "admin": os.getenv("ADMIN_SERVICE_URL", "http://127.0.0.1:8006"),
    "ai": os.getenv("AI_SERVICE_URL", "http://127.0.0.1:8007"),
    "frontend": os.getenv("FRONTEND_SERVICE_URL", "http://127.0.0.1:8008"),
}

# ================= UPLOADS =================
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ================= PROXY =================
async def proxy_request(service: str, path: str, request: Request, method: str = "GET", data=None, files=None, params=None):
    url = SERVICES[service] + path
    cookies = {}
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if token:
        cookies["access_token"] = token
    
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        cookies["refresh_token"] = refresh_token

    timeout = httpx.Timeout(60.0, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            # Prepare files if any
            httpx_files = None
            if files:
                httpx_files = {}
                for key, val in files.items():
                    if isinstance(val, tuple) and len(val) >= 2:
                        # (filename, fileobj, content_type)
                        httpx_files[key] = val
                    else:
                        httpx_files[key] = val
            
            # --- Check 1: Validate Request Format (Before Sending) ---
            # We validate 'data' or 'json' if present
            if data and not compiler.validate_request_format(data):
                logger.error(f"Invalid request format: {data}")
                return JSONResponse({"detail": "Invalid request format"}, status_code=400)
            
            resp = await client.request(
                method, 
                url, 
                data=data, 
                files=httpx_files, 
                cookies=cookies, 
                params=params,
                headers={k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length", "content-type"]}
            )

            # --- Check 2: Validate Response Format (Before Receiving/Returning) ---
            # We assume we expect JSON or success status
            if not compiler.validate_response_format(resp):
                 logger.error(f"Invalid response format from {url}")
                 # User asked to return Error or None (represented here as error response)
                 return JSONResponse({"detail": "Invalid response from upstream service"}, status_code=502)

            return resp
        except httpx.RequestError as e:
            return JSONResponse({"detail": f"Request error: {str(e)}"}, status_code=503)
        finally:
            # Ensure all file objects are closed
            if files:
                for val in files.values():
                    if isinstance(val, tuple) and len(val) > 1 and hasattr(val[1], 'close'):
                        val[1].close()

# ================= FRONTEND PROXY =================
@app.get("/static/{path:path}")
async def proxy_static(path: str, request: Request):
    resp = await proxy_request("frontend", f"/static/{path}", request)
    if isinstance(resp, JSONResponse): return resp
    response = Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
    response.headers["Vary"] = "X-SPA, X-Requested-With"
    return response

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    resp = await proxy_request("frontend", "/", request)
    if isinstance(resp, JSONResponse): return resp
    response = HTMLResponse(content=resp.text, status_code=resp.status_code)
    response.headers["Vary"] = "X-SPA, X-Requested-With"
    return response

@app.get("/{page}_page", response_class=HTMLResponse)
async def proxy_pages(page: str, request: Request):
    resp = await proxy_request("frontend", f"/{page}_page", request)
    if isinstance(resp, JSONResponse): return resp
    response = HTMLResponse(content=resp.text, status_code=resp.status_code)
    response.headers["Vary"] = "X-SPA, X-Requested-With"
    return response

@app.get("/info", response_class=HTMLResponse)
async def info_page(request: Request):
    resp = await proxy_request("frontend", "/info", request)
    if isinstance(resp, JSONResponse): return resp
    response = HTMLResponse(content=resp.text, status_code=resp.status_code)
    response.headers["Vary"] = "X-SPA, X-Requested-With"
    return response

@app.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request):
    resp = await proxy_request("frontend", "/contacts", request)
    if isinstance(resp, JSONResponse): return resp
    response = HTMLResponse(content=resp.text, status_code=resp.status_code)
    response.headers["Vary"] = "X-SPA, X-Requested-With"
    return response

@app.get("/registration_success", response_class=HTMLResponse)
async def registration_success(request: Request):
    resp = await proxy_request("frontend", "/registration_success", request)
    if isinstance(resp, JSONResponse): return resp
    response = HTMLResponse(content=resp.text, status_code=resp.status_code)
    response.headers["Vary"] = "X-SPA, X-Requested-With"
    return response

@app.get("/register_error", response_class=HTMLResponse)
async def register_error(request: Request):
    resp = await proxy_request("frontend", "/register_error", request)
    if isinstance(resp, JSONResponse): return resp
    response = HTMLResponse(content=resp.text, status_code=resp.status_code)
    response.headers["Vary"] = "X-SPA, X-Requested-With"
    return response

@app.get("/login_error", response_class=HTMLResponse)
async def login_error(request: Request):
    resp = await proxy_request("frontend", "/login_error", request)
    if isinstance(resp, JSONResponse): return resp
    response = HTMLResponse(content=resp.text, status_code=resp.status_code)
    response.headers["Vary"] = "X-SPA, X-Requested-With"
    return response

@app.get("/favicon.ico", include_in_schema=False)
async def favicon(request: Request):
    resp = await proxy_request("frontend", "/static/favicon.ico", request)
    if isinstance(resp, JSONResponse): return resp
    return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))

@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}

# ================= AUTH =================
@app.post("/register")
async def register(request: Request, email: str = Form(...), password: str = Form(...)):
    # form = await request.form() # No longer needed as we have specific params
    base_url = str(request.base_url).rstrip('/')
    
    data = {"email": email, "password": password}
    resp = await proxy_request("auth", "/register", request, method="POST", data=data)
    if isinstance(resp, JSONResponse): return resp
    if resp.status_code != 200:
        detail = "Помилка реєстрації"
        try:
            detail = resp.json().get("detail", detail)
        except Exception:
            detail = resp.text
        
        # If client explicitly asks for JSON, or doesn't explicitly ask for HTML
        accept_header = request.headers.get("accept", "").lower()
        if "application/json" in accept_header or "text/html" not in accept_header:
            return JSONResponse({"detail": detail}, status_code=resp.status_code)

        from urllib.parse import quote
        return RedirectResponse(f"/register_error?detail={quote(detail)}", status_code=303)
    
    auth_data = resp.json()
    token = auth_data["access_token"]
    refresh_token = auth_data.get("refresh_token")
    v_token = auth_data.get("verification_token")
    email = auth_data["user"]["email"]

    if v_token:
        async with httpx.AsyncClient() as client:
            await client.post(SERVICES["notification"] + "/send-verification", 
                             data={"email": email, "token": v_token, "base_url": base_url}, 
                             timeout=10.0)

    response_json = {
        "message": "Registration successful. Please verify your email.",
        "access_token": token,
        "refresh_token": refresh_token,
        "verification_token": v_token,
        "email": email
    }

    # If it's an API call (not expecting HTML), return JSON
    # If client explicitly asks for JSON, or doesn't explicitly ask for HTML
    accept_header = request.headers.get("accept", "").lower()
    if "application/json" in accept_header or "text/html" not in accept_header:
        # Include token and basic info
        return JSONResponse(response_json)

    response = RedirectResponse("/registration_success", status_code=303)
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    response.set_cookie("logged_in", "true", httponly=False, samesite="lax")
    if refresh_token:
        response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax", max_age=7*24*3600)
    return response


@app.post("/contacts")
async def handle_contacts(request: Request):
    form = await request.form()
    # Forward to notification service
    async with httpx.AsyncClient() as client:
        await client.post(SERVICES["notification"] + "/send-contact-email", data=form, timeout=20.0)
    return JSONResponse({"status": "sent"})

@app.get("/verify/{token}")
async def verify_email(token: str, request: Request):
    resp = await proxy_request("auth", f"/verify/{token}", request)
    if not isinstance(resp, JSONResponse) and resp.status_code == 200:
        # If it's an API call (not expecting HTML), return JSON
        accept_header = request.headers.get("accept", "")
        if "text/html" not in accept_header:
            return JSONResponse(resp.json())

        resp_f = await proxy_request("frontend", f"/verify/{token}", request)
        if isinstance(resp_f, JSONResponse): return resp_f
        return HTMLResponse(content=resp_f.text, status_code=resp_f.status_code)
    
    detail = "Verification failed"
    if not isinstance(resp, JSONResponse):
        try: detail = resp.json().get("detail", detail)
        except: pass
    return HTMLResponse(f"<h1>{detail}</h1>", status_code=400)

@app.post("/login")
async def login(request: Request, password: str = Form(...), email: str = Form(None), username: str = Form(None)):
    # form = await request.form()
    data = {"password": password}
    if email: data["email"] = email
    if username: data["username"] = username

    resp = await proxy_request("auth", "/login", request, method="POST", data=data)
    if isinstance(resp, JSONResponse): return resp
    if resp.status_code != 200:
        # If client explicitly asks for JSON, or doesn't explicitly ask for HTML
        accept_header = request.headers.get("accept", "").lower()
        if "application/json" in accept_header or "text/html" not in accept_header:
            try:
                return JSONResponse(resp.json(), status_code=resp.status_code)
            except:
                return JSONResponse({"detail": resp.text}, status_code=resp.status_code)

        if resp.status_code == 401:
            return RedirectResponse("/login_error", status_code=303)
        return JSONResponse(resp.json(), resp.status_code)
    
    auth_data = resp.json()
    token = auth_data["access_token"]
    refresh_token = auth_data.get("refresh_token")
    
    # If client explicitly asks for JSON, or doesn't explicitly ask for HTML
    accept_header = request.headers.get("accept", "").lower()
    if "application/json" in accept_header or "text/html" not in accept_header:
        # We don't set cookies here as it's an API call, 
        # but for SPA we might need them if the client doesn't handle tokens manually
        return JSONResponse(auth_data)

    response = RedirectResponse("/orders_page", status_code=303)
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    response.set_cookie("logged_in", "true", httponly=False, samesite="lax")
    if refresh_token:
        response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax", max_age=7*24*3600)
    return response

@app.post("/resend-verification")
async def resend_verification(request: Request):
    form = await request.form()
    base_url = str(request.base_url).rstrip('/')
    
    resp = await proxy_request("auth", "/resend-verification", request, method="POST", data=form)
    if isinstance(resp, JSONResponse): return resp
    if resp.status_code != 200:
        return JSONResponse(resp.json(), resp.status_code)
    
    data = resp.json()
    email = data["email"]
    v_token = data["verification_token"]

    async with httpx.AsyncClient() as client:
        await client.post(SERVICES["notification"] + "/send-verification", 
                         data={"email": email, "token": v_token, "base_url": base_url}, 
                         timeout=10.0)

    return JSONResponse({"message": "Link resent successfully"})

@app.post("/ai/chat")
async def ai_chat(request: Request, message: str = Form(...)):
    data = {"message": message}
    resp = await proxy_request("ai", "/chat", request, method="POST", data=data)
    if isinstance(resp, JSONResponse): return resp
    return JSONResponse(resp.json(), status_code=resp.status_code)

@app.get("/me")
async def me(request: Request):
    resp = await proxy_request("auth", "/me", request)
    if isinstance(resp, JSONResponse): return resp
    return JSONResponse(resp.json(), status_code=resp.status_code)

@app.post("/refresh")
async def refresh(request: Request):
    resp = await proxy_request("auth", "/refresh", request, method="POST")
    if isinstance(resp, JSONResponse): return resp
    if resp.status_code != 200:
        return JSONResponse(resp.json(), resp.status_code)
    
    data = resp.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    
    response = JSONResponse({"status": "refreshed"})
    response.set_cookie("access_token", access_token, httponly=True, samesite="lax")
    response.set_cookie("logged_in", "true", httponly=False, samesite="lax")
    response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax", max_age=7*24*3600)
    return response

@app.post("/logout")
async def logout():
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("access_token", path="/", domain=None)
    response.delete_cookie("refresh_token", path="/", domain=None)
    response.delete_cookie("logged_in", path="/", domain=None)
    return response

# ================= ORDERS =================
@app.get("/orders")
async def orders(request: Request):
    resp = await proxy_request("orders", "/orders", request)
    if isinstance(resp, JSONResponse): return resp
    return JSONResponse(resp.json(), status_code=resp.status_code)

@app.delete("/orders/{order_id}")
async def delete_order(order_id: int, request: Request):
    resp = await proxy_request("orders", f"/orders/{order_id}", request, method="DELETE")
    if isinstance(resp, JSONResponse): return resp
    return JSONResponse(resp.json(), status_code=resp.status_code)

@app.post("/create_order")
async def create_order(request: Request):
    # Check if user is verified
    resp_me = await proxy_request("auth", "/me", request)
    if isinstance(resp_me, JSONResponse): return resp_me
    if resp_me.status_code != 200:
        return JSONResponse(resp_me.json(), resp_me.status_code)
    
    user_data = resp_me.json()
    if not user_data.get("is_verified"):
        return JSONResponse({"detail": "Please verify your email to create orders."}, status_code=403)

    form = await request.form()
    data = {}
    files = {}

    for key, value in form.items():
        if hasattr(value, "filename"):
            if value.filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{value.filename}"
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(await value.read())
                files["file"] = (filename, open(filepath, "rb"), value.content_type)
        else:
            data[key] = value

    if not files:
        files["_force_multipart"] = (None, b"")

    resp = await proxy_request("orders", "/create_order", request, method="POST", data=data, files=files)
    if isinstance(resp, JSONResponse): return resp
    return JSONResponse(resp.json(), status_code=resp.status_code)


# ================= NOTIFICATION =================
@app.get("/calculate_price")
async def calculate_price(request: Request):
    params = request.query_params
    resp = await proxy_request("orders", "/calculate_price", request, params=params)
    if isinstance(resp, JSONResponse): return resp
    return JSONResponse(resp.json(), status_code=resp.status_code)

@app.get("/notifications")
async def notifications(request: Request):
    resp = await proxy_request("notification", "/notifications", request)
    if isinstance(resp, JSONResponse): return resp
    return JSONResponse(resp.json(), status_code=resp.status_code)

# ================= ADMIN =================
@app.get("/admin")
async def admin_dashboard(request: Request):
    email = request.query_params.get("email")
    path = f"/admin?email={email}" if email else "/"
    resp = await proxy_request("admin", path, request)
    if isinstance(resp, JSONResponse): return resp
    return JSONResponse(resp.json(), status_code=resp.status_code)

@app.post("/admin/update_status/{order_id}")
async def update_status(order_id: int, request: Request):
    form = await request.form()
    print(f"[Gateway] Forwarding status update for {order_id}: {dict(form)}")
    resp = await proxy_request("admin", f"/update_status/{order_id}", request, method="POST", data=form)
    print(f"[Gateway] Admin response for {order_id}: {resp.status_code}")
    if isinstance(resp, JSONResponse): return resp
    return JSONResponse(resp.json(), status_code=resp.status_code)

@app.delete("/admin/delete_order/{order_id}")
async def admin_delete_order(order_id: int, request: Request):
    resp = await proxy_request("admin", f"/delete_order/{order_id}", request, method="DELETE")
    if isinstance(resp, JSONResponse): return resp
    return JSONResponse(resp.json(), status_code=resp.status_code)

# ================= CATCH-ALL FOR SPA =================
# Moved to end to avoid shadowing API routes like /me, /orders, /calculate_price
@app.get("/{path:path}", response_class=HTMLResponse)
async def catch_all(path: str, request: Request):
    # Proxy everything else to frontend (e.g. /intro, /about)
    resp = await proxy_request("frontend", f"/{path}", request)
    if isinstance(resp, JSONResponse): return resp
    response = HTMLResponse(content=resp.text, status_code=resp.status_code)
    response.headers["Vary"] = "X-SPA, X-Requested-With"
    return response
