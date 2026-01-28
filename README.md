# Multi-Service Backend with API Gateway

A robust microservices-based backend system with a central API Gateway, written in Python with FastAPI.

## Features
- **API Gateway**: Central entry point for all requests.
- **Auth Service**: User registration, login, and JWT-based authentication.
- **Orders Service**: Management of user orders and file uploads.
- **Admin Service**: Dashboard and status management.
- **Notification Service**: SMTP email integration (verification emails).
- **AI Service**: Chat integration.
- **Mobile Friendly**: Supports standard `Bearer Token` authentication.

## Quick Start (Local Run)

### 1. Requirements
Ensure you have **Python 3.10+** installed. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Copy the example file and fill in your secrets (SMTP, AI keys, etc.):
```bash
copy .env.example .env
```
*(Note: At minimum, you should set a custom `SECRET_KEY`).*

### 3. Run All Services
Simply run the batch file:
```bash
run_all.bat
```
The Gateway will be available at: `http://localhost:8000`

## Mobile Integration
For mobile app developers, see detailed documentation in [mobile_api_docs/](mobile_api_docs/):
- **Base URL**: Use your local machine's IP (e.g., `http://192.168.x.x:8000`).
- **Authorization**: Include `Authorization: Bearer <token>` header in requests.
