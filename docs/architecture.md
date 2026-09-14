# GridLens Architecture

## One-sentence summary

GridLens is a deterministic energy-scenario engine (demand, solar, battery,
grid, cost, emissions) wrapped in a FastAPI service, with an optional,
strictly-grounded retrieval-augmented explanation layer and a Gradio/Plotly
UI — built so that every number a user sees is computed in Python, never
guessed by a language model.

## Directory map
domain/ Pydantic data contracts (ScenarioRequest, HourlyRecord, ScenarioResult, ForecastResult, ScenarioComparison, SourceReference, ExplanationRequest/Result, ...) engine/ Deterministic scenario engine, forecast, and comparison. Never imports llm/ or rag/. data/fixtures/ Versioned synthetic input data (load, solar, weather, carbon, tariffs) + PROVENANCE.md data/knowledge/12 Markdown knowledge-base documents used by RAG (tariffs, battery efficiency, ...) rag/ Chunking, hash-based embeddings, vector/keyword store, ingestion, retrieval llm/ Provider abstraction (local deterministic + OpenAI), tool schemas, conversation state integrations/ Optional external adapters (Open-Meteo weather) with cache/retry/fallback app/ FastAPI app, request/response wiring, config, structured logging middleware ui/ Gradio app and Plotly chart builders evaluation/ eval_set.json + eval.py (retrieval/answer-quality harness), benchmark_ingest.py docs/ This document, threat model, provenance, runbook, limitations, demo script tests/ pytest suite (unit, API, RAG, UI, evaluation, end-to-end smoke)

## Layering rule (the single most important invariant)

domain (data contracts) ^ | engine (pure, deterministic) -----------------------+ ^ | | v app (FastAPI) <---- rag (retrieval) <---- llm (providers) ^ | ui (Gradio)


`engine/` never imports from `llm/` or `rag/`. This means every energy,
cost, and emissions number in GridLens is reproducible and unit-testable
without a network connection, an API key, or a language model — and it means
a bug in the (optional) explanation layer can never silently change a
scenario result.

## Request lifecycle (traced end to end)

1. **Data source** — either bundled, versioned fixtures (`data/fixtures/`,
   always available) or the optional `integrations/weather.py` Open-Meteo
   adapter (cached, retried, schema-validated, falls back to fixtures).
2. **Validation** — the request is parsed into a `domain/models.py` Pydantic
   model (`ScenarioRequest`, `ExplanationRequest`, ...); invalid input is
   rejected with `422` before any calculation runs.
3. **Deterministic calculation** — `engine/scenario_engine.py` runs the
   hourly simulation (demand, solar, battery SOC, grid import/export,
   curtailment, cost, emissions, constraint diagnostics).
4. **Forecast** — `engine/forecast.py` produces an independent seasonal-naive
   or rolling-mean baseline, never fed through an LLM.
5. **Retrieval** — for `/api/explain` only, `rag/retriever.py` retrieves
   citation-bearing chunks from the ingested knowledge base above a
   similarity threshold.
6. **Explanation** — `rag/answer.py` builds an answer strictly from already
   computed scenario/comparison numbers plus retrieved citations; it never
   lets a model invent a number, and returns "insufficient evidence" rather
   than guessing.
7. **API response** — `app/main.py` serializes a `domain/models.py` response
   model; a generic exception handler ensures internals are never leaked.
8. **Logging** — `app/logging_config.py` emits one structured, secret-redacted
   JSON log line per request (request ID, operation, duration, scenario ID,
   data source, cache status, forecast method, model name, retrieval count,
   error category).
9. **Evaluation** — `evaluation/eval.py` measures retrieval hit rate, MRR,
   citation presence, groundedness (via fact-substring checks), no-answer
   correctness, latency, and token usage against `evaluation/eval_set.json`.

## Why this system is not yet suitable for operational grid control

1. **No power-flow simulation** — GridLens balances energy (kWh) hourly; it
   does not model voltage, frequency, phase, or network topology, all of
   which real grid control requires.
2. **No real-time control loop** — the engine runs on-demand for a fixed
   horizon; it has no closed-loop feedback, no sub-second response, and no
   safety interlocks required for live equipment control.
3. **Synthetic, unvalidated data** — fixture load/solar/weather/tariff data
   is illustrative (see `data/fixtures/PROVENANCE.md` and
   `data/knowledge/system_limitations.md`), not measurement-grade or
   certified for a real site, so no operational decision should be made
   from it without independent validation.