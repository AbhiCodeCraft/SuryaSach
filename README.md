# Surya Sach

Independent rooftop-solar performance verification for Indian homeowners.

Know what your solar system produced — and what it reasonably should have.

## Current status

**Milestone 3: NASA POWER integration.** The backend retrieves validated daily solar
and weather resources by coordinates or saved system, with explicit units, local solar
day semantics, missing-data status, bounded caching, and upstream error handling.
See the [NASA data contract](docs/nasa-power.md) and
[verification record](docs/milestone-3-verification.md).

**Milestone 2 remains available:** Create, review, view, and edit rooftop profiles
through a seven-step mobile-friendly flow. Profiles persist in local SQLite across backend
restarts. Unknown orientation/tilt and year-only installation timing remain explicit.
The original live backend health indicator and its tests remain in place.

**NOT YET IMPLEMENTED:** Hourly resource inputs, solar modeling, Textract,
AWS persistence, user authentication, reports, anomaly detection, or AWS deployment.

## Architecture and layout

Next.js serves the UI. Browser JavaScript calls FastAPI directly over HTTP; the API
allows only configured browser origins. Python's built-in SQLite provides local storage;
no separate database installation or external service is required. This is a local, shared
development workspace with a server-assigned `local-owner`, not authenticated user storage.
Use test information only and keep the API bound to loopback outside a local container.

```text
frontend/       Next.js App Router, TypeScript, Tailwind CSS, browser tests
  src/app/      Pages and layout
  src/components/  UI components
  src/lib/      Central API client
  src/types/    API types
backend/        FastAPI, Pydantic settings, pytest, Ruff, Dockerfile
  app/api/      HTTP routes
  app/config/   Environment settings
  app/schemas/  Response models
  app/models/   Framework-independent solar-system records
  app/services/ Profile creation/retrieval/update logic
  app/repositories/ Repository protocol and SQLite adapter
  data/         Ignored local database, created on first profile access
  tests/        Health, CORS, profile validation and persistence tests
docs/           Architecture, calculation principles, verification record
scripts/        Small development helpers
```

## Prerequisites

- Node.js 20.9+ and npm; tested with Node 20.16.0 and npm 10.8.1.
- Python 3.11+; tested with Python 3.12.10. Use Python 3.12 for parity with Docker.
- Docker Desktop with Linux containers, optional for local development.
- Microsoft Edge for the included Playwright browser tests.

The Next.js runtime is 16.4.0. The lint preset is pinned to 16.3.0 with
TypeScript ESLint 8.46.4 because newer transitive lint packages require Node 20.19+.
The npm lockfile fixes the full dependency tree. Python direct dependencies are pinned;
transitive Python dependencies resolve on installation. No global Python packages are used.

## First-time setup (Windows PowerShell)

From the repository root:

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env.local
cd frontend
npm ci
```

The environment files are optional for default localhost settings. Keep them untracked.
When copying examples on an existing checkout, do not overwrite your own configuration.

## Run locally (two terminals)

Backend, from the repository root:

```powershell
cd backend
.venv/Scripts/python.exe -m app --reload
```

Frontend, from the repository root in a second terminal:

```powershell
cd frontend
npm run dev
```

Open **http://localhost:3000**. The footer should show **Backend: Connected**.
Choose **Add your solar system**, or open http://localhost:3000/systems to view saved profiles.
API health: http://localhost:8000/health. Interactive API docs: http://localhost:8000/docs.
Stop each server with Ctrl+C. No virtual-environment activation or PowerShell policy change is needed.

For macOS/Linux, create the environment with `python3.12 -m venv backend/.venv`,
replace `.venv/Scripts/python.exe` with `.venv/bin/python`, and use `cp` to copy examples.

## Configuration

Backend settings are loaded from `backend/.env`; process environment variables take precedence.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `Surya Sach API` | OpenAPI application title |
| `APP_ENV` | `development` | Environment label, reserved for later policies |
| `API_HOST` | `127.0.0.1` | Bind address for `python -m app` |
| `API_PORT` | `8000` | API listening port |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | JSON array of allowed browser origins |
| `DATABASE_PATH` | Absolute `backend/data/surya-sach.sqlite3` in this checkout | Local development SQLite file; parent directory created automatically |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Frontend's public API address |

Use `localhost:3000` rather than `127.0.0.1:3000`, unless you add that exact origin.
If Next.js selects another port because 3000 is busy, stop the conflicting process or
explicitly update CORS. CORS is not authentication; all current API endpoints are unauthenticated.
Frontend `NEXT_PUBLIC_*` values are included in browser bundles: never put secrets there.
Restart development servers after changing configuration; rebuild the frontend for production changes.

## Checks

Backend, from `backend/`:

```powershell
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m pip check
```

Frontend, from `frontend/`:

```powershell
npm run lint
npm run typecheck
npm run build
```

To test the production frontend locally, stop the development server and run `npm start`
after `npm run build`. With the frontend at localhost:3000 and backend at localhost:8000,
run `npm run test:e2e` in another frontend terminal. Tests use your installed Edge in
headless mode at desktop and mobile viewport sizes. They verify real API connectivity,
loading, failed requests, retry, invalid payloads, timeout, onboarding, validation, editing,
saved summaries, and absence of horizontal overflow. Onboarding tests create test profiles.
Use an isolated `DATABASE_PATH` for browser testing to keep them out of your own local data.
The backend unit tests always use temporary SQLite files.
No AWS credentials or fabricated solar data are involved.

`scripts/check.ps1` runs backend checks and frontend lint/typecheck/build from any directory.
It requires dependencies to have been installed first and stops on the first failed check.

## Backend Docker

From the repository root, with Docker Desktop running:

```powershell
docker build -t surya-sach-api:milestone3 ./backend
docker run --rm --name surya-sach-api -p 127.0.0.1:8000:8000 --mount type=volume,source=surya-sach-data,target=/app/data surya-sach-api:milestone3
```

Stop the local Python server first if it uses port 8000. In another terminal:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

On macOS/Linux use `curl http://localhost:8000/health`.
The image binds to `0.0.0.0` inside the container, runs as UID 10001, includes a health check,
and excludes tests, virtual environments, and environment files from its build context.
Pass configuration via `docker run -e VARIABLE=value`; if changing `API_PORT`, change
the container side of the port mapping too. Do not pass the development `.env` unchanged:
its loopback `API_HOST` would override the container's bind address.
The named volume keeps SQLite data across container removal and recreation. Without it,
data survives a container restart but is lost when the container is removed. The local
Python database and Docker named volume are independent stores. Docker Compose adds
little value for one container, so it is intentionally omitted.

## Solar profile API

| Endpoint | Behavior |
| --- | --- |
| `POST /systems` | Validate and create; 201 with a Location header |
| `GET /systems` | List local profiles, newest first |
| `GET /systems/{system_id}` | Retrieve a profile; 404 if missing |
| `PUT /systems/{system_id}` | Replace profile details; preserve ID, owner, and creation timestamp |
| `GET /health` | Existing API reachability response |

Invalid requests return 422 with field/message details; storage failures return 503.
No private input is echoed in validation errors. Metadata is server-managed. PUT is a full
replacement: optional fields omitted from a request become null. Concurrent edits are
last-write-wins in this local prototype. There is no deletion, pagination, or authentication yet.

See [profile conventions](docs/solar-system-profile.md) for fields, limits, unknown values,
installation precision, and coordinate/angle conventions. Local database files are ignored
by Git and excluded from Docker builds. Do not commit or share databases containing private data.

## Isolated browser verification

The standard test command uses localhost:3000. To test without touching a server already
on port 8000, use three terminals. Backend, from `backend/`:

```powershell
$env:API_PORT = '8002'
$env:CORS_ORIGINS = '["http://localhost:3001"]'
$env:DATABASE_PATH = Join-Path (Get-Location) 'data/e2e.sqlite3'
.venv/Scripts/python.exe -m app
```

Frontend, from `frontend/` (stop any production frontend before rebuilding):

```powershell
$env:NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8002'
npm run build
npm start -- --port 3001
```

Tests, from `frontend/` in another terminal:

```powershell
$env:PLAYWRIGHT_BASE_URL = 'http://localhost:3001'
npm run test:e2e
```

These environment assignments affect only their terminals. Afterwards, close the test
terminals and rebuild with `npm run build` in a fresh terminal to restore the default
production API address. `npm run dev` uses the current environment or `.env.local`.

## Product principles and future work

Future checks will use an independent solar/weather baseline, report expected ranges,
preserve assumptions and evidence, and require repeated observations before flagging a
persistent anomaly. Generation data alone will not establish a specific hardware fault.

See [architecture](docs/architecture.md), [calculation principles](docs/calculation-method.md),
and [Milestone 2 verification](docs/milestone-2-verification.md).
Development stops at onboarding until Milestone 3 is explicitly authorized.
