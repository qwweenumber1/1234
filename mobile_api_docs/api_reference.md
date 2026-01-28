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
  - `color` (string, optional)
  - `size` (string, optional)
  - `file` (file, optional)
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Order created",
    "order_id": 123,
    "file_path": "uploads/..."
  }
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
