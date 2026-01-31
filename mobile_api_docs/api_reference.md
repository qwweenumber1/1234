# API Reference

## Authentication Endpoints

### 1. Registration
- **URL**: `/register`
- **Method**: `POST`
- **Format**: `Form Data`
- **Fields**: `email`, `password`
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Registration successful. Please verify your email.",
    "access_token": "eyJhbG...",
    "token_type": "bearer",
    "user": { "email": "user@example.com", "role": "user", "is_verified": false }
  }
  ```

### 2. Login
- **URL**: `/login`
- **Method**: `POST`
- **Format**: `Form Data`
- **Fields**: `email`, `password`
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Login successful",
    "access_token": "eyJhbG...",
    "token_type": "bearer",
    "user": { "email": "user@example.com", "role": "user", "is_verified": true }
  }
  ```

### 3. Current User Info
- **URL**: `/me`
- **Method**: `GET`
- **Header**: `Authorization: Bearer <token>`
- **Success Response (200 OK)**:
  ```json
  {
    "email": "user@example.com",
    "role": "user",
    "is_verified": true
  }
  ```

---

## Orders Endpoints

### 4. Create Order
- **URL**: `/create_order`
- **Method**: `POST`
- **Format**: `Multipart Form Data`
- **Fields**: 
  - `description` (string, required)
  - `material` (string, required: `PLA`, `ABS`, `PETG`, `TPU`, `Nylon`)
  - `color` (string, optional)
  - `width` (number, optional: X in mm)
  - `length` (number, optional: Y in mm)
  - `height` (number, optional: Z in mm)
  - `infill` (number, optional: 0-100)
  - `real_weight` (number, optional: W in g)
  - `file` (file, optional)
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Order created",
    "order_id": 123,
    "file_path": "uploads/...",
    "price": 150,
    "currency": "UAH"
  }
  ```

### 4.1. Resend Verification
- **URL**: `/resend-verification`
- **Method**: `POST`
- **Format**: `Form Data`
- **Fields**: `email`
- **Success Response (200 OK)**:
  ```json
  { "message": "Link resent successfully" }
  ```

### 5. Get User Orders
- **URL**: `/orders`
- **Method**: `GET`
- **Header**: `Authorization: Bearer <token>`
- **Success Response (200 OK)**:
  ```json
  {
    "orders": [
      {
        "id": 1,
        "description": "3D Model print",
        "status": "pending",
        "created_at": "2026-01-28T20:40:00"
      }
    ]
  }
  ```

### 6. Delete Order
- **URL**: `/orders/{order_id}`
- **Method**: `DELETE`
- **Header**: `Authorization: Bearer <token>`
- **Success Response (200 OK)**:
  ```json
  { "message": "Order deleted" }
  ```
