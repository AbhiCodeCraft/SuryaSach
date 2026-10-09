# Milestone 2 verification

Final verification resumed on 2026-10-10 from the existing working tree after a usage-limit
interruption. The onboarding implementation was preserved; no architecture change or
Milestone 3 work was introduced during continuation.

## Backend

- `python -m pytest`: **41 passed**, including the unchanged health tests.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: passed, 19 files.
- `python -m pip check`: no broken requirements.

Coverage includes create/get/list/update, invalid inputs on both create and update,
unknown and zero-degree angles, optional installer, date/year precision, future dates,
server-managed metadata, owner scoping, missing records, CORS, safe storage errors,
NaN/infinity rejection, and persistence across application instances using the same file.

The existing upstream Starlette warning about its `httpx` test-client compatibility path
remains. Tests pass without suppressing the warning.

## Frontend

- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `npm run build`: passed with the default local API configuration.
- `npm run test:e2e`: **18 passed** in the fresh continuation run (45.2 seconds).
  This run used the development frontend on port 3001 and isolated API/database on port
  8002. The earlier complete production-frontend browser run also passed all 18 cases.

The full browser suite contains 18 desktop/mobile cases, including all Milestone 1 tests.
It verifies live health requests, loading/failure/retry/timeout states, onboarding,
authoritative API saves, review, unknown values, validation, exact-angle editing, reload,
listing, missing profiles, and backend-error recovery. Tests use a separate SQLite database;
no sample profiles are added to the user's default database.

Desktop location, mobile orientation, and mobile review screenshots were visually inspected
during the original Milestone 2 run. Screenshots and test output remain ignored local artifacts.
Coverage uses headless Edge and mobile viewport emulation, not physical mobile devices.

## Docker

The final `surya-sach-api:milestone2` image was rebuilt during continuation. Verification
confirmed HTTP health, Docker health status, and non-root UID 10001. A real profile was
created and updated through the API, including a known zero tilt and unknown orientation.
After stopping and removing the container, a new container using the same named volume
returned the same edited profile. The temporary container and test volume were then removed.

## Scope and limitations

SQLite persistence is local/development-only. Profiles share a server-owned placeholder
identity; there is no authentication. Coordinates are entered manually. Updates are
last-write-wins, and create requests have no idempotency key. Deletion and pagination are
deferred. NASA POWER, generation calculations, readings, Textract, AWS storage, Cognito,
reports, and performance assessment remain unimplemented.

Repository documentation describes these limits and the angle/date conventions.
Only environment examples are tracked; local database files and test artifacts are ignored.
`git diff --check` passed. The continuation also completed this previously missing document
so the README verification link resolves. No new functional bug was found in the rerun.
