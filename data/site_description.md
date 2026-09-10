---
doc_id: kb-site-description
title: Demo site description — campus-microgrid-a
tags: [site, campus, microgrid]
---

# Demo site description — `campus-microgrid-a`

The default (and currently only) fixture site models an abstract campus
microgrid: a single electrical connection point with local solar generation
and battery storage, serving a mixed load (offices, some evening
activity, e.g. a library or dining hall).

## Assumed characteristics baked into the fixtures

- Weekday demand is higher than weekend demand (a `0.7` multiplier is
  applied on Saturday/Sunday).
- Demand ramps up during the day (06:00 onward) and has a secondary evening
  bump (18:00–21:00).
- The site has unobstructed south-facing-equivalent solar exposure with no
  shading events modeled.
- One point of grid interconnection, with both import and export metering
  available (export can be disabled per-scenario via `allow_export=False`).

## What "abstract" means here

`campus-microgrid-a` does not correspond to any real, named institution. Its
purpose is to be a stable, reproducible playground for exploring how
battery size, solar size, tariff choice, and export policy interact — not
to model a specific real facility's actual energy profile.

## Adding a second site

The engine already threads `ScenarioRequest.site` through
`engine.fixtures.load_site_rows(site)`; adding a second site is a matter of
adding new, equally provenance-documented CSVs and referencing them from
that function — no changes to the dispatch logic are required.