start uvicorn services.auth.main:app --reload --port 8005 --host 0.0.0.0
start uvicorn services.orders.main:app --reload --port 8001 --host 0.0.0.0
start uvicorn services.payment.main:app --reload --port 8003 --host 0.0.0.0
start uvicorn services.notification.main:app --reload --port 8004 --host 0.0.0.0
start uvicorn services.admin.main:app --reload --port 8006 --host 0.0.0.0
start uvicorn gateway.main:app --reload --port 8000 --host 0.0.0.0
