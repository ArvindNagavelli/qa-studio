# QA Studio

An AI-native QA workspace: turn requirements into AI-generated test cases and golden
datasets (CSV / YAML / JSON export), run tests, track defects and report on quality.
Google sign-in with Admin and QA roles.

> **Status:** repository scaffold. Features are built in later iterations.

## Stack

| Layer    | Technology                                                                    |
| -------- | ----------------------------------------------------------------------------- |
| Backend  | Python 3.10–3.14, FastAPI, SQLAlchemy 2 (async) + asyncpg, Alembic, Pydantic 2 |
| Database | PostgreSQL 16                                                                 |
| LLM      | Anthropic API (a mock provider for development and tests)                      |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, shadcn/ui     |
| Auth     | Google Identity Services + application JWTs                                   |

## Repository layout

```
backend/     FastAPI service, Alembic migrations, tests      -> backend/README.md
frontend/    Next.js web app                                 -> frontend/README.md
scripts/     lock_backend.sh, make_upload.sh
.github/     CI workflow
docker-compose.yml   optional local Postgres + API (development only)
```

## Quick start (no Docker required)

Requirements: Python 3.10+ and Node 22. Everything installs from pinned lockfiles, so
setup works on an offline machine with access to PyPI and npm mirrors only.

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip    # the pip bundled with Python may have known advisories
pip install -r requirements-dev.lock
pytest                     # starts an embedded PostgreSQL 16 from a pip wheel
cp .env.example .env       # fill in values, then:
uvicorn app.main:app --reload

# Frontend
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

### Docker Compose (optional, local development only)

`docker-compose.yml` runs PostgreSQL 16 and the API for local development. **It is not
used by CI or by the offline task environment**, which has no Docker; there the backend
tests use the embedded PostgreSQL from `pixeltable-pgserver`.

```bash
cp .env.example .env && cp backend/.env.example backend/.env   # fill in values
docker compose up --build
```

## Dependency pinning

- **Backend:** `backend/pyproject.toml` declares version ranges. `backend/requirements.lock`
  (runtime) and `backend/requirements-dev.lock` (runtime + dev) pin exact versions with one
  version per package across Python 3.10–3.14. `scripts/lock_backend.sh` regenerates them
  and verifies that every pin installs from a binary wheel on Linux (Ubuntu 24.04) and
  Windows for each supported Python, and that `pip-audit` finds no known vulnerabilities.
- **Frontend:** `frontend/package-lock.json` (exact versions); install with `npm ci`.
  `npm audit` must report 0 vulnerabilities.

## Quality checks

| Area     | Command                                                     |
| -------- | ----------------------------------------------------------- |
| Backend  | `pytest`, `ruff check .`, `ruff format --check .`, `mypy`   |
| Frontend | `npm run lint`, `npm run typecheck`, `npm run build`        |
| Repo     | `pre-commit run --all-files` (secrets, large files, format) |
| Audit    | `npm audit` (frontend), `scripts/lock_backend.sh` (pip-audit) |

CI (`.github/workflows/ci.yml`) runs these on every push and pull request.

## Security

Secrets are never committed: see [SECURITY.md](SECURITY.md). Copy the `.env.example`
files to create local configuration.

## Packaging for upload

`scripts/make_upload.sh` builds `qa-studio-upload.zip` from the last commit with
`git archive` (tracked files only), rejects local-only or generated paths, and enforces
a 10 MB limit.

## License

[MIT](LICENSE)
