# Mobile Authentication Guide

## Flow Overview
1. Mobile app calls `/login` or `/register` with credentials.
2. Server responds with `access_token` in the JSON body.
3. Mobile app stores this token securely (e.g., Encrypted Shared Preferences, Secure Store).
4. Mobile app includes the token in ALL subsequent requests needing auth.

## Header Example
```http
Authorization: Bearer <eyJhbG...>
```

## Token Expiration
- Tokens are valid for **60 minutes** by default.
- If a request returns `401 Unauthorized`, the app should redirect to the login screen.

## Test Account
- **Email**: `test@example.com`
- **Password**: `password123`
*(Note: You can create this account through the `/register` endpoint if it doesn't exist yet)*

## Email Verification
- After registration, the user MUST verify their email before they can use `/create_order`.
- For testing purposes, you can manually update the database or use a real SMTP setup configured in `.env`.
