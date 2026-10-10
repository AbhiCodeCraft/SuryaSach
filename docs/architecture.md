# Architecture

## Implemented through Milestone 3

```text
Browser <-- HTML / JavaScript -- Next.js (localhost:3000)
   |
   | browser fetch: /health and /systems
   v
FastAPI (localhost:8000)
   |
Pydantic request validation -> SystemService -> SystemRepository protocol
                                                   |
                                          SQLiteSystemRepository
                                                   |
                                          Local SQLite file
```

The frontend uses Next.js App Router, TypeScript, and Tailwind CSS. The home page is
prerendered; a small client component performs the health request after hydration.
The shared `src/lib/api.ts` owns the API address, five-second timeout, HTTP handling,
and runtime response validation. Unmounting cancels the request. Failure offers a retry.

FastAPI exposes a typed health response. `pydantic-settings` reads configuration from
the backend environment file or process environment. The application factory allows
tests to provide isolated settings. CORS defaults to the exact localhost frontend origin;
credentials are disabled and GET, POST, and PUT are allowed. No authentication is implemented.

`python -m app` runs Uvicorn using configured host and port. Local development uses a
project virtual environment. A Python 3.12 slim container provides the alternate backend
runtime, with a non-root user and Docker health check. There is no frontend container.

Health means the API can answer requests; it does not probe SQLite or NASA POWER.
Storage errors on profile requests return a safe 503. Solar generation calculations
remain deferred.

## Independent solar resource integration

`/solar-resource` and `/systems/{id}/solar-resource` validate coordinates and dates,
then call `NasaPowerService`. The latter loads the saved profile first. The service
uses HTTPX against NASA's fixed HTTPS daily point endpoint, verifies response units
and metadata, and returns a typed `SolarWeatherDay` rather than upstream dictionaries.
The [NASA contract](nasa-power.md) documents RE/LST semantics and the hourly upgrade.

The `SolarResourceCache` protocol has a bounded, thread-safe in-memory adapter.
Resource data is refetched after expiry or process restart; saved profiles continue
to use SQLite. The upstream concurrency bound and cache are per application instance.
Expected upstream failures return explicit 502/503/504 errors; missing required daily
GHI returns 404. Optional missing fields remain null with partial status.

## Solar-system onboarding

`/systems/new` is a deterministic React multi-step form. It collects capacity, location,
installation timing, orientation, tilt, optional installer, and review. Both unknown angles
are explicit choices; no default angle is substituted. The form keeps entries on validation
or network failure and shows server errors. `/systems` lists real stored profiles;
`/systems/[systemId]` fetches one profile and supports editing through the same form.
No profile, score, weather record, or performance result is mocked in the application.

The HTTP boundary uses Pydantic schemas for authoritative validation and response contracts.
The service works with plain immutable dataclass records and a repository protocol, not
FastAPI or SQLite. It creates UUIDs, assigns the local owner, and manages UTC timestamps.
The SQLite adapter uses parameterized statements, transactions, per-operation connections,
and explicit connection closing. Records contain JSON profiles keyed by system ID and owner.
The schema is intentionally minimal for the local milestone, without an ORM or migrations.

SQLite uses Python's standard library. The default file lives in ignored `backend/data/`;
`DATABASE_PATH` can select a different file, including isolated verification storage.
Profiles survive application restarts. Docker uses a writable `/app/data` owned by its
non-root user; the documented named volume retains data across container recreation.

Every browser currently shares the same server-assigned `local-owner`. Repository methods
accept an owner scope, but this is not identity verification or authorization. A future
authenticated adapter must derive the owner from verified identity, never from request JSON.
The service/repository boundary allows a later DynamoDB adapter without rewriting profile
business logic. No DynamoDB code or cloud setup is present now.

There is no optimistic concurrency, paging, deletion, or create-idempotency protocol yet.
Repeated confirmed creates produce separate profiles. Ambiguous network-save failures tell
users to check the list before retrying. These are explicit local prototype limitations.

## FUTURE — not implemented

```text
Next.js / AWS Amplify
        |
FastAPI / AWS App Runner
   +---- DynamoDB
   +---- S3 (private evidence and reports)
   +---- Textract (OCR candidates; owner confirmation required)
   +---- NASA POWER (daily integration exists; hourly adapter remains future)
   |
Solar Engine -> Analysis Engine -> PDF Reports
```

Cognito and per-user access control will be added before handling private user data in
a deployed product. AWS calls will use backend IAM roles; credentials must never reach
the browser. CloudWatch will provide operational visibility. Bedrock remains optional
for explanations only; calculations and screening rules will be deterministic.

The current scaffold deliberately contains no fake implementations of these services.
