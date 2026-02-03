import pytest
from unittest.mock import patch, MagicMock

def test_gateway_health(gateway_client):
    response = gateway_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "gateway"}

@pytest.mark.asyncio
async def test_gateway_index(gateway_client):
    with patch("gateway.main.proxy_request") as mock_proxy:
        # Create a mock response object
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html>Index</html>"
        mock_resp.headers = {"content-type": "text/html"}
        
        # Since proxy_request is awaited, the mock must return a coroutine or use AsyncMock
        from unittest.mock import AsyncMock
        mock_proxy.side_effect = AsyncMock(return_value=mock_resp)
        
        response = gateway_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

@pytest.mark.asyncio
async def test_gateway_proxy_me(gateway_client):
    # Mocking the proxy_request function
    with patch("gateway.main.proxy_request") as mock_proxy:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"email": "test@example.com"}
        
        from unittest.mock import AsyncMock
        mock_proxy.side_effect = AsyncMock(return_value=mock_resp)
        
        response = gateway_client.get("/me")
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
        mock_proxy.assert_called_once()

@pytest.mark.asyncio
async def test_gateway_login_proxy(gateway_client):
    with patch("gateway.main.proxy_request") as mock_proxy:
        # Mocking auth service response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "fake_token"}
        
        from unittest.mock import AsyncMock
        mock_proxy.side_effect = AsyncMock(return_value=mock_resp)
        
        response = gateway_client.post("/login", data={"email": "test@example.com", "password": "pass"}, follow_redirects=False)
        # Gateway redirects on success
        assert response.status_code == 303
        assert response.headers["location"] == "/orders_page"
        assert "access_token" in response.cookies
