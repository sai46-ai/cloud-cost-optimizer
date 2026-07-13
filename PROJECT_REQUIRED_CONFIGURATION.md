# 📋 CloudWise AI — Required Production Configuration & Setup Checklist

This document details all mandatory and optional environment variables, cloud credentials, security keys, and manual deployment steps required to operate CloudWise AI in local, staging, and production environments.

---

## 🔑 Environment Variables Reference

| Environment Variable | Mandatory / Optional | Purpose & Location | Required Format / Description | Example Placeholder (Dummy) |
|---|---|---|---|---|
| `ENVIRONMENT` | **Mandatory** | Application environment mode (`backend/app/core/config.py`) | String (`development`, `staging`, `production`) | `production` |
| `DEBUG` | **Mandatory** | Debug logging toggle (`backend/app/core/config.py`) | Boolean (`true`, `false`) | `false` |
| `SECRET_KEY` | **Mandatory** | Cryptographic secret key for signing JWT tokens (`backend/app/core/security.py`) | 64-character hexadecimal string | `0e2ca093ff8729f53466ef720c14b79acb132cec93a1888db9f9156cbd6df536` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | **Mandatory** | JWT access token expiration duration | Integer (minutes) | `60` |
| `DATABASE_URL` | **Mandatory** | Database connection string (`backend/app/database.py`) | PostgreSQL URL or local SQLite URL | `sqlite:///./cloudwise.db` or `postgresql://user:pass@host:5432/dbname` |
| `GEMINI_API_KEY` | **Optional** | Google Gemini API key for FinOps Assistant chatbot (`backend/app/ai/assistant.py`) | Google AI Studio API Key string | `AIzaSyA1b2C3d4E5f6G7H8I9J0` |
| `GEMINI_MODEL` | **Optional** | Gemini Model identifier | Model name string | `gemini-3.5-flash` |
| `AWS_ACCESS_KEY_ID` | **Optional** | AWS Access Key ID for live Cost Explorer & CloudWatch API syncing | 20-character uppercase alphanumeric string | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | **Optional** | AWS Secret Access Key | 40-character secret key string | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_SESSION_TOKEN` | **Optional** | Required for AWS Academy / Learner Lab temporary session tokens | Session token string | `IQoJb3JpZ2luX2Vj...` |
| `AWS_REGION` | **Optional** | Default AWS target region | AWS Region string | `us-east-1` |
| `REDIS_URL` | **Optional** | Redis instance connection string for Celery background tasks | Redis connection URI | `redis://127.0.0.1:6379/0` |
| `CELERY_BROKER_URL` | **Optional** | Celery broker URL | Redis connection URI | `redis://127.0.0.1:6379/0` |
| `CELERY_RESULT_BACKEND` | **Optional** | Celery result storage backend | Redis connection URI | `redis://127.0.0.1:6379/0` |
| `CORS_ORIGINS` | **Mandatory** | Allowed CORS origins for API request verification | Comma-separated HTTP URLs | `http://localhost:5173,http://127.0.0.1:5173` |

---

## 🛠️ Step-by-Step Production Setup Guide

### 1. Generate Secure JWT Key
Generate a 64-character random secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Assign the generated string to `SECRET_KEY` in `.env` and `backend/.env`.

### 2. Configure Google Gemini AI Key (Optional)
To enable the interactive FinOps assistant:
1. Navigate to [Google AI Studio](https://aistudio.google.com/).
2. Create an API Key.
3. Update `.env`:
   ```bash
   GEMINI_API_KEY="AIzaSy..."
   GEMINI_MODEL="gemini-3.5-flash"
   ```

### 3. Configure AWS Integration Credentials (Optional)
CloudWise AI operates using strictly read-only IAM policies. For AWS Academy Learner Lab or temporary IAM roles:
```bash
AWS_ACCESS_KEY_ID="AKIA..."
AWS_SECRET_ACCESS_KEY="wJalr..."
AWS_SESSION_TOKEN="IQoJb3..."
AWS_REGION="us-east-1"
```

---

## 🛡️ Manual Verification Checklist Before Production Deployment

- [x] Environment variable `.env` file created and excluded from git tracking (`.gitignore`).
- [x] Default development `SECRET_KEY` replaced with a production-grade cryptographic token.
- [x] Database initialized and migrations applied (`alembic upgrade head` or `init_db()`).
- [x] Security headers validated (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`).
- [x] CORS allowed origins restricted to trusted domain endpoints.
- [x] Production bundle verified via `npm run build` in frontend.
