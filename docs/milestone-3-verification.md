# Milestone 3 verification

Initial verification began 2026-10-10 IST (2026-10-09 UTC), from clean `main` at
`6b1744f`. Final continuation checks ran 2026-10-10 at approximately 09:12 IST
(03:42 UTC), preserving the four existing Milestone 3 implementation commits and
unfinished documentation. No additional implementation changes were needed.
Existing profiles, onboarding, and architecture were preserved. No frontend feature,
generation calculation, pvlib dependency, AWS service, or fabricated fallback was added.

## Local checks

| Check | Result |
| --- | --- |
| Backend pytest | 157 passed, 3 opt-in external tests skipped |
| Separate opt-in NASA suite, final Docker image | 3 passed in 4.03 seconds |
| Ruff check | Pass |
| Ruff format --check | Pass, 26 Python files |
| pip check | No broken requirements |
| Frontend lint / typecheck / production build | All pass |
| Playwright, installed Edge, desktop and mobile | 18 passed |
| git diff --check | Pass |
| Backend Docker image build | Pass, Python 3.12, runtime HTTPX installed |

Tests include all 41 existing backend checks plus 116 new deterministic checks.
They cover parameter mapping, identity unit conversion, query boundaries, non-finite
and overflowing upstream numbers, missing/sentinel/zero values, physical ranges,
wrong units, malformed structures, date/time metadata, timeout/4xx/5xx mapping,
retry recovery, cache hits/expiry/eviction/coordinate precision, saved-system edits,
and avoiding NASA requests for invalid queries or unknown profiles.

The existing Starlette TestClient deprecation warning about HTTPX remains visible;
it does not fail tests. An initial sandboxed run could not access pytest's existing
temporary directory; rerunning with authorized filesystem access passed. This was
an environment permission issue, not an application regression.

## Real NASA observations

The running container's HTTP API successfully returned all eight normalized fields
for **2026-06-15**, NASA local solar time. Values below were observed, not hard-coded
test expectations. Broad smoke assertions check magnitude, not exact historical values.

| Location (latitude, longitude) | GHI | DNI | DHI | Mean / min / max C | Wind at 2 m, m/s | RH % |
| --- | --- | --- | --- | --- | --- | --- |
| Delhi (28.6139, 77.2090) | 5.6741 | 2.1581 | 3.1711 | 34.81 / 28.31 / 41.63 | 1.91 | 42.18 |
| Jaipur (26.9124, 75.7873) | 7.3306 | 5.7362 | 2.4166 | 33.34 / 27.42 / 39.48 | 2.42 | 44.16 |
| Bengaluru (12.9716, 77.5946) | 6.4795 | 4.3258 | 2.7902 | 26.04 / 21.20 / 32.35 | 4.05 | 70.28 |

All three locations were reproduced by the final image's opt-in suite on continuation,
with the same values shown above. All solar columns are **kWh/m2/day**.
All three had `status=complete`, API v2.10.0,
and source labels SYN1DEG, MERRA2, POWER. The magnitudes are plausible for daily
solar energy and regional weather; no 24x or 1000x discrepancy was present.

Earlier contract research fetched **Delhi, 2026-09-15** directly from NASA through
Docker: GHI 5.0191, DNI/DHI -999, temperatures 28.31 / 24.55 / 32.40 C,
wind 1.15 m/s, RH 85.49%, sources FLASHFLUX, GEOSIT, POWER. This independently
demonstrated recent component-data gaps. Deterministic tests verify that those
sentinels become null optional fields and partial status, never zero energy.

## Network qualification

NASA connectivity was intermittent from this environment. Host requests timed out.
Docker delivered the real observations above, but the separate opt-in pytest run
for 2026-09-15 failed all three checks with `ConnectTimeout`; a second opt-in run
for 2026-06-15 also failed all three with the same connection error. Those failures
were not suppressed or converted into skipped/passing tests. Jaipur's first HTTP
endpoint attempt returned the expected structured 504, and a later attempt succeeded.

On continuation, **the opt-in external suite passed all three locations** for
2026-06-15 from the final Docker image. The tests and timeout policy were unchanged;
no failures were suppressed. Earlier connectivity failures remain relevant: recheck
NASA availability before an interactive demo and handle upstream errors explicitly.
Normal pytest continues to skip these external tests unless opted in. `/health`
intentionally does not assert upstream connectivity. No system proxy, DNS,
TLS-verification, or security settings were changed to force a successful result.

## Docker checks

The backend ran as `appuser`, with Docker reporting healthy and `/health` returning
200. Both coordinate and saved-system resource routes returned real normalized data.
A disposable profile was created in the verification container; its saved coordinates
selected the same resource/cache entry. Invalid latitude, longitude, and a future
date each returned 422. No user's persisted profile database was used for testing.

The parser's integer-overflow hardening was followed by a final image rebuild.
Continuation rebuilt and started that exact code in `surya-sach-m3-final` on
loopback port 18004. Health returned 200; direct Delhi resource retrieval returned
200 in 1.22 seconds. A newly created disposable profile's resource route returned
200 with identical normalized data and retrieval timestamp, confirming cache reuse.
Docker reported healthy and `appuser`. All three invalid queries again returned 422.
Temporary test servers and verification containers are cleaned up after verification.

## Reproduce

From the repository root, with dependencies already installed:

```powershell
cd backend
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe -m app --reload
```

In a second terminal, from the repository root:

```powershell
cd frontend
npm run lint
npm run typecheck
npm run build
npm run start
```

With both servers running, `npm run test:e2e` from `frontend` runs browser checks.
Use a separate `DATABASE_PATH` for test profiles. External pytest commands and all
response/error semantics are in [the NASA contract](nasa-power.md).

Docker alternative, from the root (stop the local backend if it owns port 8000):

```powershell
docker build -t surya-sach-api:milestone3 backend
docker run --rm --name surya-sach-api -p 127.0.0.1:8000:8000 --mount type=volume,source=surya-sach-data,target=/app/data surya-sach-api:milestone3
```

Then in another terminal:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod 'http://localhost:8000/solar-resource?latitude=28.6139&longitude=77.209&date=2026-06-15'
```

## Milestone boundary and next step

The bounded memory cache is intentionally non-durable (512 entries, 24-hour complete
TTL, one-hour partial TTL); the repository protocol permits a future durable adapter.
No auth, distributed rate limit, hourly data, weather UI, generation model, or performance
claim is included. NASA is a gridded independent baseline, not rooftop ground truth.

Before Milestone 4, retain the opt-in live checks and account for upstream outages.
Add verified hourly UTC resource intervals and an explicit local observation
period policy before pvlib transposition/temperature modeling. Decide how missing
DNI/DHI and unknown roof tilt/orientation affect availability and uncertainty.
