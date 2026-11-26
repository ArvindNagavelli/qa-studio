# QA Studio backend

FastAPI + SQLAlchemy 2 (async, asyncpg) + Alembic. Python 3.10–3.14; developed on 3.12.

## Setup (no Docker needed)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip   # the pip bundled with Python may have known advisories
pip install -r requirements-dev.lock
cp .env.example .env               # then fill in values
```

Install **only from the lockfiles**. `pyproject.toml` holds the version ranges; the
lockfiles hold the exact versions. Every pin is verified to install from binary wheels on
**Linux and Windows** for CPython 3.10–3.14, and to have no known vulnerabilities
(`pip-audit`).

**Windows:** some packages (notably `anthropic`) contain file paths up to ~150 characters
inside `site-packages`. Unless Windows long-path support is enabled, keep the venv's own
path under ~90 characters (e.g. `C:\dev\qa-studio\backend\.venv` is fine), otherwise pip
fails with `OSError: [Errno 2] No such file or directory`.

`pre-commit` (the git-hook runner) is installed only on Python 3.11+: its dependency
`filelock` has no security-patched release for Python 3.10. Tests, ruff and mypy work on
every supported Python.

## Run

```bash
uvicorn app.main:app --reload       # http://localhost:8000/health, docs at /docs
```

## Quality checks

```bash
pytest                    # starts an embedded PostgreSQL 16 (pixeltable-pgserver); no Docker
ruff check . && ruff format --check .
mypy
```

The test suite starts a real PostgreSQL from the `pixeltable-pgserver` wheel in a temp
directory. When run as root (common in sandboxes), it creates a `pgserver` system user,
because PostgreSQL refuses to run as root.

## Migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

`alembic/env.py` reads `DATABASE_URL` from app settings; `alembic.ini` holds no URL.

## Configuration

Settings come from environment variables or `backend/.env` (see `.env.example`).
`DATABASE_URL` and `JWT_SECRET` (≥ 32 chars) are required; startup fails with a message
naming the missing variable, never its value. All secrets are `SecretStr` and are masked
in logs and reprs.

## Changing dependencies

Edit the ranges in `pyproject.toml`, then run `scripts/lock_backend.sh` (needs
[uv](https://docs.astral.sh/uv/)) and commit both lockfiles.

## Layout

```
app/
  main.py         FastAPI app (GET /health)
  core/           config, database, security
  api/v1/         versioned routers
  models/         SQLAlchemy models
  schemas/        Pydantic schemas
  services/llm/   LLM provider abstraction
  prompts/        prompt templates
alembic/          migrations
tests/
```
