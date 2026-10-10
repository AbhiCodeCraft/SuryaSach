# Calculation method — planned

Milestone 3 retrieves independent daily solar/weather resource data from NASA POWER.
The [NASA POWER contract](nasa-power.md) defines the endpoint, verified units,
missing-data handling, date semantics, cache, and limitations. It uses daily RE data
in NASA local solar time, which is not an Indian civil day. Solar fields are daily
energy in kWh/m2/day; weather fields are daily means or named extrema.

No solar generation calculation engine is implemented. No numerical coefficients,
uncertainty intervals, or anomaly thresholds have been selected or validated yet.

The later implementation must follow these principles:

- Use an independent solar/weather baseline, with NASA POWER as the intended source.
- Report a weather-adjusted expected **range**, not an exact generation claim.
- Normalize actual performance against available solar energy for the same observation period.
- Expose input units, roof assumptions, losses, uncertainty, and model version.
- Allow unknown orientation and tilt with documented assumptions and increased uncertainty.
- Distinguish one low observation from persistent underperformance.
- Suggest possible causes conservatively; do not claim a confirmed hardware diagnosis.
- Never fabricate missing weather measurements or delegate calculations to an LLM.

Before implementing pvlib, add hourly UTC resource inputs and define observation-period
alignment, including India's half-hour offset and the meaning of each hourly interval.
Do not feed daily energy into an instantaneous irradiance model or invent hourly
irradiance from daily totals. Unknown roof geometry, gridded-source uncertainty,
missing DNI/DHI, and the wind height required by a temperature model need explicit
policies. The generation methodology and coefficients remain deferred to Milestone 4.
