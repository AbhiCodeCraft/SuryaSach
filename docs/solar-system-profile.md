# Solar-system profile conventions

This document describes stored owner-reported facts, not a generation model.

## Representation and validation

| Field | Meaning and constraints |
| --- | --- |
| `capacity_kw` | Installed panel capacity in kW; finite number greater than 0, at most 100 |
| `location_label` | Trimmed human-readable text, 1–120 characters |
| `latitude` | Finite decimal degrees, −90 through 90 |
| `longitude` | Finite decimal degrees, −180 through 180 |
| `install_date` | Calendar date from 1900-01-01 through today in India, or null |
| `install_year` | Integer from 1900 through the current year in India, or null |
| `azimuth_degrees` | Finite number 0 inclusive to 360 exclusive, or null |
| `tilt_degrees` | Finite number from 0 through 90 inclusive, or null |
| `vendor_name` | Optional trimmed text, up to 120 characters; blank becomes null |
| `system_id` | Server-generated UUID |
| `owner_id` | Server-assigned `local-owner`; a placeholder, not authentication |
| `created_at`, `updated_at` | Server timestamps in UTC; creation timestamp preserved on edits |

Exactly one of installation date or installation year must be present. A year-only answer
never turns into January 1 or another fabricated date. Day/year limits use India time
(UTC+05:30), independent of the server's timezone. 100 kW is a residential-MVP input guardrail,
not a physical or regulatory limit. The year 1900 is a broad input sanity bound, not a
claim about rooftop solar history. Numeric strings, booleans, NaN, and infinities are rejected
for numerical profile fields. Unknown request fields, including owner/ID injection, are rejected.

## Orientation

Azimuth is clockwise from **true north**. The homeowner can select a compass direction,
enter an exact angle, or explicitly say “I don’t know”. The stored representation supports
arbitrary angles without redesigning the model.

| Choice | Stored degrees |
| --- | --- |
| North | 0 |
| North-East | 45 |
| East | 90 |
| South-East | 135 |
| South | 180 |
| South-West | 225 |
| West | 270 |
| North-West | 315 |
| I don’t know | null |

Compass choices are reported approximations; exact numeric entries are also user-reported,
not independently measured or certified. No magnetic-declination correction is performed.
The model currently stores the angle, not its measurement method or an uncertainty estimate.

## Tilt and unknown information

Tilt is measured from horizontal: 0° means flat and 90° means vertical. The UI offers
numeric entry or “I don’t know”; there are no hidden categorical angle estimates.
`null` alone expresses unknown, so separate `tilt_known`/`azimuth_known` flags cannot
contradict the stored angle. Zero is a valid known value and must never be treated as missing.

When the user switches a known field to unknown, review and saved data show unknown.
Any draft number retained while moving between form choices is not sent as the selected value.
Future modeling may use documented assumptions with lower confidence, but those assumptions
must be stored separately and must not overwrite owner-reported unknowns.

## Location and persistence

Coordinates are entered explicitly using decimal degrees, with guidance for copying a
rooftop pin from a map app. There is no automatic geocoding, coordinate/name consistency
check, map integration, browser geolocation, or third-party location request. The location
label is for humans; coordinates will be the later solar-data input. No coordinate is invented.

Local SQLite stores profiles across backend restarts. The repository is development-only,
with shared local ownership, last-write-wins updates, and no authentication. All writes pass
backend validation before entering the service/repository path. Test databases and evidence
screenshots are ignored by Git; no user information belongs in committed fixtures.

## Before NASA POWER integration

Verify the available data cadence and delay for recent dates, input units, missing-data
markers, coordinate resolution, and daily timezone alignment. Decide how a year-only
installation record and unknown geometry affect uncertainty without inventing owner facts.
Generation readings and weather periods will need an explicit matching calendar convention.
None of these later calculations or assumptions is implemented in Milestone 2.
