import httpx
import asyncio

async def test_gateway_proxy():
    # Simulate a request like the browser would send
    url = "http://127.0.0.1:8000/ai/chat" # Gateway URL
    files = {"message": (None, "Привіт!")}
    
    # We don't need to actually start the whole system if we just want to verify 
    # the logic in isolation, but here we'll try to reach the gateway if it's running.
    try:
        async with httpx.AsyncClient() as client:
            # This should now work if the gateway is running
            response = await client.post(url, data={"message": "Тест"}, timeout=5.0)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Gateway might not be running: {e}")

if __name__ == "__main__":
    asyncio.run(test_gateway_proxy())
