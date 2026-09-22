# Mukando Backend

FastAPI + SQLAlchemy + PostgreSQL backend for Mukando.

## Database mode

The backend is synchronous throughout its application and database layers. SQLAlchemy uses a normal synchronous `Session` and PostgreSQL uses the `psycopg` driver.

Local development and production are intentionally separated:

```env
ENVIRONMENT=development
DATABASE_URL_LOCAL=postgresql+psycopg://postgres:postgres@localhost:5432/mukando
```

Production:

```env
ENVIRONMENT=production
DATABASE_URL_PRODUCTION=postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require
```

When `ENVIRONMENT=development` or `test`, the production URL is ignored. When `ENVIRONMENT=production`, `DATABASE_URL_PRODUCTION` is used, with the older `DATABASE_URL` accepted as a compatibility fallback.

## Local setup

```bash
cd backend
python -m venv env
source env/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Make sure local PostgreSQL is running and that the `mukando` database exists.

Generate JWT keys for local development:

```bash
python scripts/generate_keys.py
```

Run migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload
```

API: `http://localhost:8000`
Swagger: `http://localhost:8000/docs`
Health: `http://localhost:8000/health`

## Tests

Tests use a synchronous in-memory SQLite database and generated temporary RSA keys:

```bash
pytest -q
```

## Production

Set the Render environment variables from `render.yaml`, especially:

```text
ENVIRONMENT=production
DATABASE_URL_PRODUCTION=<your production PostgreSQL connection string>
FRONTEND_URL=<your deployed frontend origin>
JWT_PRIVATE_KEY=<production private key>
JWT_PUBLIC_KEY=<production public key>
```

Never commit `.env`, production credentials, or private JWT keys.
