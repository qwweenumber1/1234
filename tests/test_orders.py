import pytest

def test_health(orders_client):
    response = orders_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "orders"}

def test_create_order(orders_client):
    # Mock user dependency by setting a test header or similar if needed, 
    # but here we rely on dependency_overrides in conftest.py which might need more work if we use get_current_user.
    
    # Let's check how get_current_user is implemented in services/orders/security.py
    pass

def test_create_order_basic(orders_client, monkeypatch):
    # Mock get_current_user
    from services.orders.security import get_current_user
    from services.orders.main import app
    app.dependency_overrides[get_current_user] = lambda: "test@example.com"
    
    response = orders_client.post("/create_order", data={
        "description": "Test Order",
        "color": "Red",
        "size": "L"
    })
    
    assert response.status_code == 200
    assert response.json()["message"] == "Order created"
    assert "order_id" in response.json()
    
    app.dependency_overrides.clear()

def test_get_orders(orders_client):
    from services.orders.security import get_current_user
    from services.orders.main import app
    app.dependency_overrides[get_current_user] = lambda: "test@example.com"
    
    # Create an order first
    orders_client.post("/create_order", data={"description": "Order 1"})
    
    response = orders_client.get("/orders")
    assert response.status_code == 200
    assert len(response.json()["orders"]) >= 1
    
    app.dependency_overrides.clear()
