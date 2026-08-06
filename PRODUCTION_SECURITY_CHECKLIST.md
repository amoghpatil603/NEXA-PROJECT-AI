# NEXA Production Security Checklist

## 1. Input Validation & Request Sanitization
- [x] Express `/api/chat` and `/api/chat/stream` endpoints enforce strict input schema (10,000 char max length, parameter clamping).
- [x] Python `backend/nexa_security/validation.py` provides validation for message length, token limits, history size, and temperature.
- [x] Prompt threat scanning active for suspicious execution and prompt injection patterns.

## 2. File Upload Protection
- [x] Max file upload size capped at 15MB.
- [x] MIME type and extension whitelisting implemented.
- [x] Dangerous executable extensions (`.exe`, `.sh`, `.bat`, `.py`, `.js`, etc.) blocked.
- [x] Canonical path resolution (`path.resolve`) enforces directory isolation inside `/uploads`.
- [x] Filenames sanitized to remove path traversal sequences (`../`) and non-alphanumeric characters.

## 3. Authentication & Authorization
- [x] Passwords hashed using PBKDF2 with SHA-256 (100,000 iterations).
- [x] Constant-time string comparison (`hmac.compare_digest`) used to prevent timing attacks.
- [x] Protected endpoints enforce RBAC permission checks.

## 4. HTTP Security & Headers
- [x] Helmet middleware active in Express server.
- [x] Rate limiting configured on `/api/` endpoints (1000 requests per 15 min window).
- [x] CORS policies configured.
- [x] `trust proxy` set for Cloud Run reverse proxy layer.

## 5. Error Handling & Information Exposure
- [x] Production error responses masked from public clients.
- [x] Full exception stack traces and database details logged internally.
- [x] No environment variables or API keys exposed in 500 error responses.

## 6. Verification & Health Check
- [x] `compile_applet` build succeeds cleanly.
- [x] Vitest frontend tests pass.
- [x] Python security validation tests (`tests/test_security_validation.py`) pass.
