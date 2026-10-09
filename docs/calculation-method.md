# Calculation method — planned

No solar calculation engine is implemented in Milestone 1. No numerical coefficients,
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

The implemented methodology, units, validation, and numerical assumptions will be documented
when the solar engine milestone is authorized. This file is a statement of principles,
not a working or certified model.
