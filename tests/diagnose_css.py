import requests

GATEWAY_URL = "http://127.0.0.1:8000" # Assuming default gateway port

def check_css():
    print("Checking CSS through gateway...")
    try:
        url = f"{GATEWAY_URL}/static/css/index.css?v=6"
        resp = requests.get(url)
        print(f"URL: {url}")
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('Content-Type')}")
        print(f"Vary: {resp.headers.get('Vary')}")
        if resp.status_code == 200:
            print(f"Content length: {len(resp.content)}")
        else:
            print(f"Error content: {resp.text[:100]}")
    except Exception as e:
        print(f"Error checking CSS: {e}")

def check_html():
    print("\nChecking HTML through gateway...")
    try:
        url = f"{GATEWAY_URL}/"
        # Full load
        resp = requests.get(url)
        print(f"Full Load Content-Length: {len(resp.content)}")
        print(f"Full Load Vary: {resp.headers.get('Vary')}")
        has_head = b"<head>" in resp.content.lower()
        print(f"Full Load has <head>: {has_head}")

        # SPA load
        resp_spa = requests.get(url, headers={"X-SPA": "true"})
        print(f"SPA Load Content-Length: {len(resp_spa.content)}")
        print(f"SPA Load Vary: {resp_spa.headers.get('Vary')}")
        has_head_spa = b"<head>" in resp_spa.content.lower()
        print(f"SPA Load has <head>: {has_head_spa}")

        if has_head and not has_head_spa:
            print("SPA/Full separation is working correctly.")
        else:
            print("WARNING: SPA/Full separation might be broken!")
            if not has_head: print("ERROR: Full load missing <head>!")
            if has_head_spa: print("ERROR: SPA load contains <head>!")

    except Exception as e:
        print(f"Error checking HTML: {e}")

if __name__ == "__main__":
    check_css()
    check_html()
