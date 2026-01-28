# Mobile Application Integration Guide

## Overview
This document provides the necessary information to connect a mobile application to the backend services.

- **Base URL**: `http://192.168.31.131:8000` (Gateway address)
- **API Version**: `v1` (Implicit in endpoints)
- **Data Format**: `JSON`
- **Content-Type**: `application/x-www-form-urlencoded` for Auth, `multipart/form-data` for Orders with files.

## Authentication
The system uses **JWT (JSON Web Tokens)**.
- For web browsers: The token is stored in the `access_token` cookie (HttpOnly).
- For mobile apps: The token is returned in the JSON response upon login/registration. You MUST include it in the `Authorization` header of subsequent requests.

**Header Format:**
```http
Authorization: Bearer <your_access_token>
```

## Special Headers
- `Accept: application/json`
- `Content-Type: application/json` (except for forms/file uploads)

## Restrictions
- Some endpoints (like `create_order`) require the user to be **verified** (via email).
- File uploads have a size limit (default FastAPI/OS limits apply).
