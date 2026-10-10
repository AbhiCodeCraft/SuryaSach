# NASA POWER data contract

Milestone 3 chooses **Option C: daily resource data now, an hourly adapter before
pvlib modeling**. Daily totals are useful for onboarding and inspecting historical
resource availability. They cannot reproduce hourly sun position, plane-of-array
irradiance, or temperature-dependent PV output. No generation is calculated here.

## Research and request

Official references reviewed before implementation:

- [Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- [Hourly API](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/)
- [Parameter dictionary](https://power.larc.nasa.gov/parameters/) and
  [parameter conventions](https://power.larc.nasa.gov/docs/tutorials/parameters/)
- [Data FAQ, including units and latency](https://power.larc.nasa.gov/docs/faqs/data/)
- [API errors](https://power.larc.nasa.gov/docs/services/api/)
- [Request guidance](https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/)
- [Source coverage](https://power.larc.nasa.gov/docs/methodology/data/sources/)
- [Data revisions and spatial resolution](https://power.larc.nasa.gov/docs/services/)

Use `https://power.larc.nasa.gov/api/temporal/daily/point`, `community=RE`
(Renewable Energy), `format=JSON`, `time-standard=LST`, and identical inclusive
`start`/`end` dates formatted `YYYYMMDD`. Latitude is north-positive in [-90, 90];
longitude is east-positive in [-180, 180]. All coordinates must be finite.

Parameter identifiers are shared across services, but availability and units depend
on community and temporal resolution. Do not reuse daily units for an hourly client.
Eight parameters fit the daily point limit of 20 (hourly limit: 15).

## Verified units

The following exact unit strings and response structure were verified against a
live NASA Daily API v2.10.0 response for Delhi (28.6139, 77.209), 2026-09-15,
through Docker on 2026-10-10 IST. Host requests timed out; Docker could reach NASA.

| NASA parameter | Meaning for this daily request | NASA unit | Internal field / unit |
| --- | --- | --- | --- |
| ALLSKY_SFC_SW_DWN | All-sky global horizontal solar energy | `kW-hr/m^2/day` | `ghi_kwh_m2_day`, kWh/m2/day |
| ALLSKY_SFC_SW_DNI | All-sky direct normal solar energy | `kW-hr/m^2/day` | `dni_kwh_m2_day`, kWh/m2/day |
| ALLSKY_SFC_SW_DIFF | All-sky diffuse horizontal solar energy | `kW-hr/m^2/day` | `dhi_kwh_m2_day`, kWh/m2/day |
| T2M | Mean air temperature at 2 m | `C` | `temp_avg_c`, degrees C |
| T2M_MIN | Minimum air temperature at 2 m | `C` | `temp_min_c`, degrees C |
| T2M_MAX | Maximum air temperature at 2 m | `C` | `temp_max_c`, degrees C |
| WS2M | Mean wind speed at 2 m | `m/s` | `wind_speed_2m_avg_m_s`, m/s |
| RH2M | Mean relative humidity at 2 m | `%` | `relative_humidity_avg_pct`, percent |

All conversions are the identity: internal value = NASA value. Solar values are
energy per area for the day, not instantaneous W/m2. Do **not** multiply them by
24 or divide them by 1000. Do not interpret daily DNI as horizontal direct energy
or assume GHI = DNI + DHI. Unexpected unit metadata must fail explicitly.

## Dates and availability

`date=YYYY-MM-DD` means **NASA local solar day**, not an Asia/Kolkata civil day.
NASA defines LST using longitude swaths 15 degrees wide, centered on solar noon.
There is no conversion to UTC or IST and no invented midnight timestamp in this
daily contract. Responses explicitly include `time_standard: LST`.

The application accepts dates from 1984-01-01 (solar-source coverage) through
today in India; that input bound does not promise every parameter is available.
NASA's general daily meteorological coverage starts in 1981, hourly coverage in
2001. Sources and parameter coverage differ. Solar data commonly lags 5-7 days;
meteorology commonly lags 2-3 days. These are estimates, not service guarantees.
Recent DNI/DHI can be missing even when GHI exists, as the live Delhi response
demonstrated. Never substitute clear-sky data or fabricated weather.

## Implemented contract

- Pydantic normalized daily model with provenance, UTC retrieval time, completeness
  status, and missing-field names. Completeness is not a scientific accuracy rating.
- Required GHI missing/sentinel: data-unavailable error. Optional missing values:
  `null` and partial status. Zero remains valid (including polar night).
- Missing parameter metadata, wrong units/time standard, malformed structures,
  non-finite numbers, and invalid physical ranges: explicit upstream-data errors.
- Finite, bounded, in-process cache behind a repository protocol: 512 entries,
  24-hour TTL, partial responses one-hour TTL. Cache keys include contract version,
  endpoint/community/time standard/parameter set, date, and coordinates rounded to
  four decimal places. Send those same coordinates upstream and return them in the
  normalized model. This precision is key stability, not rooftop accuracy.
- Cache disappears on restart; it is an optimization, not saved user data. No errors
  or negative results cached. No stale-on-error fallback. Future durable/DynamoDB
  storage can implement the same boundary. Finite TTL allows source revisions.
- Explicit HTTPX timeouts, one retry for transient connection/timeouts or 5xx,
  bounded concurrent upstream requests; no immediate retry on 4xx/429. NASA guidance
  recommends at most five concurrent requests; no exact requests/second guarantee
  was found. Avoid bulk repeated requests within the same native source grid.

HTTPX uses a 5-second connect/pool timeout and 20-second read/write inactivity timeout,
with one retry after 250 ms for network failures/timeouts or upstream 5xx. These are
per-operation timeouts, not a total wall-clock deadline: DNS and multiple resolved
addresses may extend elapsed time. At most four requests run upstream per application
instance; admission waits at most one second. No distributed limit or request coalescing
is implemented. Deploying many workers requires revisiting this policy.

## HTTP API

- `GET /solar-resource?latitude=28.6139&longitude=77.209&date=2026-06-15`
- `GET /systems/{system_id}/solar-resource?date=2026-06-15`

The saved-system route loads current persisted coordinates through the existing
owner-scoped profile service. Editing a location selects a different cache key.
No weather UI was added in this milestone. OpenAPI is available at `/docs`.

| Result | HTTP status / code |
| --- | --- |
| Complete or partial normalized data | 200, `status` describes field completeness |
| Invalid/missing query, non-finite/out-of-range coordinates, future/unsupported date | 422, existing field-error format |
| Unknown saved system | 404, existing profile error |
| GHI date missing, null, or NASA fill value | 404 / `resource_unavailable` |
| Required GHI parameter omitted entirely | 502 / `missing_required_parameter` |
| Invalid JSON/shape/numeric range, wrong metadata/units/time standard | 502 / `upstream_invalid_data` |
| NASA rejects a validated request (including upstream 4xx other than 429) | 502 / `upstream_rejected_request` |
| Timeout after retry | 504 / `upstream_timeout` |
| Network failure or upstream 5xx after retry | 503 / `upstream_unavailable` |
| NASA 429; no automatic retry | 503 / `upstream_rate_limited` |
| Local upstream concurrency slots exhausted | 503 / `upstream_busy` |

Resource failures have `{"detail":{"code":"...","message":"..."}}`; upstream
bodies and transport details are not echoed. NASA may reject a date outside its
current availability with HTTP 422 rather than a fill-valued response; this remains
an explicit upstream rejection, not a fabricated successful or zero-valued day.

## Running checks

From `backend` in PowerShell:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m pip check
```

Live tests are skipped unless explicitly enabled. They fail on network errors; they
never silently skip failed requests or assert fixed historical weather values:

```powershell
$env:NASA_SMOKE='1'
$env:NASA_SMOKE_DATE='2026-06-15'
.venv/Scripts/python.exe -m pytest -m external -q -s
Remove-Item Env:NASA_SMOKE
Remove-Item Env:NASA_SMOKE_DATE
```

Without `NASA_SMOKE_DATE`, the live tests use 30 days before today in India.
See [Milestone 3 verification](milestone-3-verification.md) for observed values,
environment-specific network behavior, and Docker commands.

## Precision and future modeling

NASA POWER provides an independent satellite/model-derived environmental baseline.
Current native grids are about 1 x 1 degree for solar and 0.5 x 0.625 degree for
meteorology. It does not measure the particular roof, its shading, dust, inverter
losses, or meter-scale microclimate. Recent source data can be revised after months.

Before Milestone 4 modeling, add hourly UTC inputs with interval semantics verified
against official metadata, align observations and resource intervals to the same
period, and explicitly handle India's half-hour civil-time offset. Preserve real
hourly GHI/DNI/DHI and weather rather than inventing an hourly profile from daily
totals. Choose wind height to match the eventual temperature model. Missing DNI/DHI
requires an explicit, validated modeling policy or a data-unavailable result.
