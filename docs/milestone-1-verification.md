# Milestone 1 verification

Verified on Windows with Node 20.16.0, npm 10.8.1, Python 3.12.10,
Docker Engine 28.5.1, and installed Microsoft Edge.

## Results

| Check | Result |
| --- | --- |
| `python -m pytest` | 5 passed: health, allowed/disallowed CORS origins, preflight, environment settings |
| `python -m ruff check .` | Passed |
| `python -m ruff format --check .` | Passed, 12 Python files |
| `python -m pip check` | No broken requirements |
| `npm run lint` | Passed |
| `npm run typecheck` | Passed |
| `npm run build` | Passed; home page statically prerendered |
| `npm start` | Production frontend served successfully |
| README development commands | `python -m app --reload` and `npm run dev` both started successfully |
| `npm run test:e2e` | 10 passed against the running production frontend and local Python API |
| Docker build | `surya-sach-api:milestone1` built successfully |
| Docker HTTP health | Returned HTTP success and the expected health JSON through published port 8001 |
| Docker internal health check | Healthy |
| Docker user | UID 10001, non-root |
| Visual review | Desktop 1440px and mobile 390px screenshots inspected; no overlap or horizontal overflow |
| Git exclusions | Environment files, virtual environment, node_modules, build and test output ignored; `.env.example` files tracked |

The browser suite checks both desktop and mobile layouts. Each layout covers a real
API request, loading state, a simulated network failure followed by retry against the
real backend, an invalid health payload, and a stalled request. Failures are simulated
only inside tests, never in application behavior. The footer displays Connected only
after validating the actual API response.

An initial six-worker browser run timed out under local contention. The suite is now
configured with one worker; the complete rerun passed. Screenshots and Playwright
output are local ignored artifacts, not repository source files.

## Known limits

- The installed Starlette test client emits an upstream deprecation warning for its
  `httpx` compatibility path. All tests pass; no warnings are suppressed.
- No AWS deployment or integration has been attempted. There are no credentials,
  user data, solar calculations, or persistence in this milestone.
- This health check verifies API reachability, not future external dependencies.
- Python direct dependencies are version-pinned; transitive versions are not fully locked.
- Browser coverage is Chromium-based Edge, including mobile viewport emulation;
  physical mobile devices, Safari, and Firefox have not been tested.

The temporary Docker verification container was stopped after checking it.
