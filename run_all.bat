start uvicorn services.auth.main:app --reload --port 8005
start uvicorn services.orders.main:app --reload --port 8001
start uvicorn services.payment.main:app --reload --port 8003
start uvicorn services.notification.main:app --reload --port 8004
start uvicorn services.admin.main:app --reload --port 8006
start uvicorn gateway.main:app --reload --port 8000
