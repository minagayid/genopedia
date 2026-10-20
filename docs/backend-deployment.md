# Genopedia API, authentication, and cloud deployment

## Included

The optional FastAPI service adds email/password registration and sign-in, revocable server-side sessions, profile reads/updates, database health checks, an interactive API reference, and a same-origin login/sign-up page at /. It is separate from the offline genomics engine and does not upload sequences automatically.

- Passwords are hashed with Argon2; plain-text passwords are never stored or returned.
- Session cookies are HttpOnly and SameSite=Lax, with Secure enabled by production configuration. Mutating authenticated requests require a double-submit CSRF token tied to the stored session.
- Session tokens are random, and only their SHA-256 hashes are stored. Logout revokes the current server-side session.
- Emails are normalized to lowercase and unique. Public responses omit hashes and session tokens.
- SQLAlchemy 2 and Alembic provide the persistent data layer and explicit schema migration.
- PostgreSQL is recommended for production. SQLite is convenient for local development and test cases.
- Docker runs as an unprivileged user; Compose provisions PostgreSQL with a persistent volume.

## Local development

Requires Python 3.10+ and, for Compose, Docker Engine with the Compose plugin.

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -e ".[api,dev]"
    alembic upgrade head
    uvicorn app.main:app --reload

Open http://127.0.0.1:8000/ for registration and sign-in, or http://127.0.0.1:8000/docs for the API reference. The default development database is the ignored local file genopedia.db.

## Run with Docker Compose

Copy .env.example to .env and then run:

    docker compose up --build

Open http://localhost:8000/. PostgreSQL data is stored in the named genopedia-postgres volume. For a local reset only, docker compose down -v removes that volume and all data it contains.

The example environment values are development-only. Replace them before exposing the service publicly. Do not commit .env.

## Production configuration

Use the hosting platform's secret/environment manager rather than storing settings in the image or source code:

- APP_ENV=production
- DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME (URL-encode reserved characters in credentials)
- SECURE_COOKIES=true
- SESSION_TTL_SECONDS=604800 or a shorter approved lifetime
- ALLOWED_ORIGINS=https://your-frontend.example.com (comma-separated exact origins; preferably keep the UI and API on the same origin)
- Optional COOKIE_DOMAIN=your-domain.example.com only when a shared subdomain cookie is specifically needed

Production configuration rejects insecure cookies and SQLite. TLS must terminate at a trusted platform ingress or reverse proxy. Configure HTTPS redirects, request/body-size limits, and per-IP/per-account rate limits for login and signup. Use a managed PostgreSQL service with backups, tested recovery, network controls, and least-privilege credentials. Keep database credentials out of image layers, build arguments, and logs.

The container applies Alembic migrations before startup. For multi-replica deployments, prefer a single controlled migration job rather than letting every replica attempt to migrate at once. Configure the platform readiness probe against /health/ready; /health/live only indicates that the process is alive.

## API

- POST /api/auth/signup — create an account and start a session.
- POST /api/auth/login — authenticate and start a session.
- GET /api/auth/me — current authenticated user.
- POST /api/auth/logout — revoke the current session; CSRF header required.
- GET /api/users/me — read the current profile.
- PATCH /api/users/me — update the display name; CSRF header required.
- GET /health/live and /health/ready — process/database health probes.

Passwords must be 12–128 characters. Login failures use a generic response to avoid disclosing whether an email is registered. Validation failures return 422, duplicate registration returns 409, and unauthenticated calls return 401.

## Before an internet-facing launch

This is a secure starter foundation, not a complete account-management service. Add email verification, secure password-reset delivery, monitored/rate-limited abuse prevention, audit/alerting, a clear privacy and retention policy, and a production browser/security review before public use. Google/GitHub OAuth requires provider credentials and redirect configuration; no fake social-login buttons are shipped. Add billing, team membership, sequence uploads, and per-user analysis history only after access-control, data-retention, and backup requirements are defined.

Do not store patient-identifiable or clinical data in this starter without a separate privacy, access-control, retention, and regulatory review. Genopedia's genomics outputs remain research-only and are not medical advice.
