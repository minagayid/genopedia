# Genopedia API deployment

The CLI remains offline-first. This optional service adds FastAPI, accounts, PostgreSQL, and Docker deployment.

## Included

- Email/password signup and login with Argon2 hashing.
- Short-lived bearer access tokens and rotating opaque refresh tokens stored only as hashes.
- HttpOnly refresh cookie, logout/revocation, profile endpoint, active-account checks, and audit events.
- Optional Google/GitHub OAuth using verified provider emails.
- CORS allow-list, auth rate limits, health probes, Alembic migrations, non-root Docker image, and PostgreSQL volume.

## Local setup

1. Install Docker and Compose v2.
2. Copy .env.example to .env and replace all example secrets. Never commit .env.
3. Set API_PUBLIC_URL, FRONTEND_URL, and CORS_ORIGINS to your real origins. For local use set APP_ENV=development, API URL http://localhost:8000, frontend URL http://localhost:3000, and matching CORS origin.
4. Run docker compose up --build -d.
5. Check /health/live, /health/ready, and /docs on port 8000.

Migrations run before Uvicorn starts. PostgreSQL data persists in the genopedia_postgres volume.

## Endpoints

- POST /auth/signup — email, password (12–128 chars), optional full name.
- POST /auth/login — email/password.
- POST /auth/refresh — rotate refresh cookie.
- POST /auth/logout — revoke refresh session.
- GET /auth/me — current profile; requires a bearer access token.
- GET /auth/oauth/google/login and /auth/oauth/github/login — optional social login.
- GET /health/live and /health/ready — health probes.

OAuth redirects to FRONTEND_URL/auth/callback with the access token in the URL fragment. The frontend must read it into memory and remove the fragment immediately. Do not persist access tokens in localStorage.

## Before production traffic

Configure HTTPS and a trusted proxy; keep COOKIE_SECURE=true; use managed PostgreSQL or tested backups; add edge rate limiting because the in-process limiter is not shared between workers; configure OAuth callback URLs exactly; rotate secrets; implement email verification and password-reset email delivery; add monitoring, account deletion/retention, and appropriate privacy terms. Do not store genomic files or sensitive sequence data in profiles/audit fields without access controls, retention policy, and consent.

## Web workspace (frontend)

`frontend/` is a Vite + React + TypeScript single-page app that consumes this API.

- Landing page, email/password signup and login, per-user analysis dashboard.
- Analyses (paste or upload FASTA/FASTQ/VCF/raw text), quality/anomaly/variant views, color-coded sequence viewer, HTML report download, pairwise comparison.
- AI assistant page bound to `/ai/status` + `/ai/query`: it shows the live model state and stays off until a validated OpenAI-compatible endpoint is configured through `AI_MODEL_BASE_URL`/`AI_MODEL_NAME`/`AI_MODEL_API_KEY` with `AI_MODEL_STATE=available`. No fabricated answers.

Local development:

```powershell
cd frontend
npm install
npm run dev   # http://localhost:3000, proxies /auth /analyses /ai /health to port 8000
```

Production configuration: set `VITE_API_BASE_URL` at build time when the API lives on another origin; when the app is served same-origin (Vercel rewrites below), leave it empty. `FRONTEND_URL` and `CORS_ORIGINS` on the API must list the frontend origin.

## Vercel deployment

`vercel.json` builds the frontend and routes `/auth/*`, `/analyses/*`, `/ai/*`, and `/health/*` to the FastAPI serverless entry `api/index.py`. Provision a managed PostgreSQL database, set the production environment variables (`APP_ENV=production`, `DATABASE_URL`, strong `JWT_SECRET_KEY` and `SESSION_SECRET_KEY`, `COOKIE_SECURE=true`, `CORS_ORIGINS`/`FRONTEND_URL`), then run `alembic upgrade head` once against that database before traffic. Serverless filesystems are ephemeral, so all analysis state lives in PostgreSQL; keep `ANALYSIS_MAX_BYTES` within the platform request-body limit.
