import pytest

def test_health(auth_client):
    response = auth_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "auth"}

def test_register_user(auth_client):
    response = auth_client.post("/register", data={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["user"]["email"] == "test@example.com"

def test_register_duplicate_user(auth_client):
    # First registration
    auth_client.post("/register", data={"email": "dup@example.com", "password": "password123"})
    # Duplicate registration
    response = auth_client.post("/register", data={"email": "dup@example.com", "password": "password123"})
    assert response.status_code == 400
    assert "Цей Email вже зареєстрований" in response.json()["detail"]

def test_login_user(auth_client):
    # Register first
    auth_client.post("/register", data={"email": "login@example.com", "password": "password123"})
    # Login
    response = auth_client.post("/login", data={"email": "login@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_credentials(auth_client):
    response = auth_client.post("/login", data={"email": "wrong@example.com", "password": "password123"})
    assert response.status_code == 401

def test_me_endpoint(auth_client):
    # Register and get token
    resp = auth_client.post("/register", data={"email": "me@example.com", "password": "password123"})
    token = resp.json()["access_token"]
    
    # Access /me with cookie
    auth_client.cookies.set("access_token", token)
    response = auth_client.get("/me")
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
