from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import httpx
import json

app = FastAPI(title="Smart 3D AI Assistant")

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai"}

# --- Amarsia Config ---
# I'm using the Standard API (Runner) as it is the most stable and reliable for this type of integration.
AMARSIA_API_KEY = os.getenv("AMARSIA_API_KEY", "TGcj37gy64RMm-AX3_X1u5oRYmabfimrnyeKeY5YUOc")
# Вставте ваш Deployment ID з кабінету Amarsia сюди
AMARSIA_DEPLOYMENT_ID = os.getenv("AMARSIA_DEPLOYMENT_ID", "9f23919b-ce07-421a-a2d1-0af61e2816e4")
BASE_URL = "https://api.amarsia.com/v1"

SYSTEM_PROMPT = """
Ви — помічник студії Smart 3D. 
ВАЖЛИВО: Не представляйтеся у кожній відповіді. Користувач вже знає, хто ви.
Відповідайте ТІЛЬКИ на запитання, що стосуються 3D-друку, моделювання, матеріалів, доставки та послуг студії Smart 3D.
Якщо запитання не стосується цієї сфери (наприклад, політика, кулінарія, загальні знання, не пов'язані з 3D), ввічливо відмовтеся відповідати, пояснивши, що ви спеціалізуєтесь лише на 3D-друці.

ВАЖЛИВО: Ви НЕ можете приймати або аналізувати фотографії, зображення чи файли. 
Ніколи не просіть користувача надіслати фото. Якщо користувач пропонує надіслати фото, поясніть, що зараз ви працюєте лише з текстом.

Інформація про студію:
- Технології: FDM (міцні деталі), SLA (висока детальність), кольоровий FDM.
- Матеріали: PLA, PETG, ABS, нейлон, фотополімери.
- Терміни: Стандарт (3-5 днів), Експрес (1-2 дні), Терміново (до 24 год).
- Послуги: 3D-друк, моделювання, відновлення зламаних деталей.
- Доставка: Нова Пошта по всій Україні.

Відповідайте українською мовою, лаконічно та професійно.
"""

@app.post("/chat")
async def chat(message: str = Form(...)):
    url = f"{BASE_URL}/runner/{AMARSIA_DEPLOYMENT_ID}"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": AMARSIA_API_KEY
    }
    
    # We send the system prompt combined with the user's message for context
    combined_message = f"{SYSTEM_PROMPT}\n\nКористувач: {message}\n\nПомічник:"
    
    payload = {
        "content": [{
            "type": "text",
            "text": combined_message
        }]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Use Standard API for a complete response
            resp = await client.post(url, headers=headers, json=payload, timeout=45.0)
            
            if resp.status_code != 200:
                error_detail = resp.text
                print(f"Amarsia API Error: {resp.status_code} - {error_detail}")
                return {"response": f"Сталася помилка API (код {resp.status_code}). Деталі: {error_detail[:100]}..."}
            
            data = resp.json()
            # According to docs, the response has a "content" field
            reply = data.get("content", "Вибачте, я не зміг сформувати відповідь.")
            return {"response": reply}
            
    except httpx.ConnectError:
        print("Amarsia Connection Error")
        return {"response": "Не вдалося з'єднатися з Amarsia AI. Перевірте підключення до мережі."}
    except Exception as e:
        print(f"General Error: {e}")
        return {"response": "Вибачте, сталася технічна помилка в роботі ШІ."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
