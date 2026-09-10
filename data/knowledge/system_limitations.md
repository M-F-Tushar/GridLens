---
doc_id: kb-system-limitations
title: Known system limitations
tags: [limitations, scope]
---

# Known system limitations

GridLens is a **decision-support and learning tool**, not an operational
grid-control system. Concretely, it does not:

- Perform real-time control of any physical device. All results are
  simulations run on demand, never a live control loop.
- Model power flow (voltage, frequency, line losses, network topology).
  It is an energy-balance (kWh in/out per hour) model only.
- Participate in energy markets or perform bidding/settlement.
- Use deep-learning or otherwise data-hungry forecasting; only simple,
  explainable baselines (see `forecast_methodology.md`).
- Run autonomous agents that take actions without a human in the loop.
- Execute arbitrary generated code. Nothing in GridLens evaluates a string
  as code, and no user input is ever passed to `eval`/`exec`/a subprocess
  shell.
- Support multiple tenants, user accounts, or billing.
- Guarantee any particular numerical accuracy against a real facility;
  results are only as good as the (currently synthetic) input data.

## Why this list exists

Every one of these boundaries is a deliberate, documented scope decision,
not an oversight — see the project's "Production Scope" section for the
full included/excluded list. Anyone extending GridLens toward real
operational use should treat each excluded item as its own separate,
carefully-scoped project with its own safety review, not a quick addition.