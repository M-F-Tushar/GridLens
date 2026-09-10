---
doc_id: kb-forecast-methodology
title: Forecast methodology and its assumptions
tags: [forecast, methodology, baseline]
---

# Forecast methodology and its assumptions

GridLens implements two baseline forecast methods in `engine/forecast.py`,
selectable via `ForecastMethod`:

## `seasonal_naive`

Forecasts hour *h* of the horizon as whatever the fixture recorded 24 hours
before the reference point (`as_of_hour_index`). This captures daily shape
(morning ramp, evening peak, night trough) very well when the underlying
pattern truly repeats day-to-day, and degrades gracefully to "yesterday's
value" when it does not.

## `rolling_mean`

Forecasts every hour of the horizon as the flat mean of the trailing
`rolling_window_hours` (default 24) window ending just before the reference
point. This smooths out daily shape entirely — useful as a sanity-check
baseline, and notably worse than `seasonal_naive` whenever demand or solar
have a strong daily rhythm (which the fixtures do).

## Why not a machine-learning forecaster

Deep-learning/ML forecasting is explicitly out of GridLens's production
scope. Simple baselines are:

- Fully deterministic and instantly explainable ("it's the same as
  yesterday" or "it's the recent average").
- Free to compute, with no training step, GPU, or model file.
- A meaningful comparison point for any future, more sophisticated
  forecaster: if a fancier model can't beat `seasonal_naive`, it isn't
  worth the added complexity.

## Known limitation

Neither baseline uses actual weather forecasts, calendar effects beyond
"yesterday", or knowledge of holidays/special events. The forecast's
accuracy is only as good as how repetitive the real underlying demand/solar
pattern actually is.