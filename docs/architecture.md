# Architecture

## Implemented in Milestone 1

```text
Browser <-- HTML / JavaScript -- Next.js (localhost:3000)
   |
   | browser fetch: GET /health
   v
FastAPI (localhost:8000)
```

The frontend uses Next.js App Router, TypeScript, and Tailwind CSS. The home page is
prerendered; a small client component performs the health request after hydration.
The shared `src/lib/api.ts` owns the API address, five-second timeout, HTTP handling,
and runtime response validation. Unmounting cancels the request. Failure offers a retry.

FastAPI exposes a typed health response. `pydantic-settings` reads configuration from
the backend environment file or process environment. The application factory allows
tests to provide isolated settings. CORS defaults to the exact localhost frontend origin;
credentials are disabled and only GET is currently needed. No authentication is implemented.

`python -m app` runs Uvicorn using configured host and port. Local development uses a
project virtual environment. A Python 3.12 slim container provides the alternate backend
runtime, with a non-root user and Docker health check. There is no frontend container.

Health means the API can answer requests. There are no dependencies, storage, external
APIs, domain services, or solar calculations to check in this milestone.

## FUTURE — not implemented

```text
Next.js / AWS Amplify
        |
FastAPI / AWS App Runner
   +---- DynamoDB
   +---- S3 (private evidence and reports)
   +---- Textract (OCR candidates; owner confirmation required)
   +---- NASA POWER (independent solar/weather data)
   |
Solar Engine -> Analysis Engine -> PDF Reports
```

Cognito and per-user access control will be added before handling private user data in
a deployed product. AWS calls will use backend IAM roles; credentials must never reach
the browser. CloudWatch will provide operational visibility. Bedrock remains optional
for explanations only; calculations and screening rules will be deterministic.

The current scaffold deliberately contains no fake implementations of these services.
