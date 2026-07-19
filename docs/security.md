# Security Architecture

## Authentication
Uses JSON Web Tokens (JWT) inside HttpOnly, Secure, SameSite=Lax cookies.
- Trust boundary is the `AuthMiddleware`.
- Uses Bcrypt for passwords in constant-time hashing.

## Rate Limiting
Nginx handles Layer 7 rate limits per IP. FastAPI handles specific API route limits with `slowapi`.

## CSRF Protection
Origin and Referer validation occurs in `AuthMiddleware`.
