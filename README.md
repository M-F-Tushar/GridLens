# GridLens — Energy-System Scenario and Decision Engine

**An LLM-assisted energy intelligence platform for scenario modeling, forecasting, and evidence-grounded decision support.**

GridLens is a portfolio project that combines a deterministic microgrid simulation engine with a grounded LLM explanation layer. It helps users model energy-system scenarios involving electricity demand, solar generation, battery storage, grid imports and exports, operating cost, and carbon emissions.

The core calculations are performed deterministically in Python. An LLM-powered retrieval-augmented generation (RAG) layer sits on top of those results to explain model behavior, answer questions using cited project documentation, and communicate scenario outcomes without changing or inventing the underlying numbers.

> **Design principle:** GridLens uses AI for explanation and decision support—not for arithmetic. Every KPI is calculated by the simulation engine first; the LLM layer can only interpret results and cite available evidence.

## Why GridLens?

Energy modeling tools often make it difficult for non-specialists to understand *why* a scenario produces a particular cost, emissions profile, or battery outcome. GridLens addresses that gap by pairing transparent calculations with natural-language explanations.

Users can:

- Run a solar-and-battery scenario.
- Compare system configurations.
- Generate demand forecasts.
- Explore charts and hourly system behavior.
- Ask how assumptions, tariffs, battery efficiency, forecasts, or emissions calculations work.
- Receive answers grounded in a local knowledge base with citations.
- Get an explicit insufficient-evidence response instead of an unsupported answer.


### Grounded-answer safeguards

The AI layer includes several safeguards intended to make answers useful and auditable:

- **Local knowledge base:** Answers are retrieved from versioned Markdown documentation covering tariffs, storage efficiency, solar derating, carbon factors, forecasts, KPIs, energy balance, and known limitations.
- **Citation support:** Retrieved chunks are preserved as references in the answer response.
- **Evidence-based abstention:** Questions outside the available knowledge base can return `insufficient_evidence: true` instead of a fabricated answer.
- **Deterministic numerical facts:** Cost, energy, emissions, and KPI values are calculated before explanation generation and passed to the explanation layer as facts.
- **Prompt-injection-aware design:** Retrieved documents are treated as untrusted source material rather than executable instructions.
- **Offline default:** The project ships with a local deterministic provider, allowing the RAG workflow to run without API keys, network access, or hosted LLM dependencies.
- **Optional hosted-provider support:** The provider architecture can be configured for a hosted LLM when an API key is available.

### Retrieval pipeline

```text
Local Markdown Knowledge Base
            │
            ▼
    Chunking and Metadata
            │
            ▼
 Hash-Based Embeddings + Keyword Search
            │
            ▼
   Relevant Evidence Chunks
            │
            ▼
 Grounded Answer + Citations
```

The retrieval pipeline uses document chunking, metadata preservation, embeddings, vector search, and keyword search to identify relevant evidence. Evaluation tooling measures retrieval quality, citation presence, answer latency, and correct abstention for unsupported questions.

## Energy-System Features

- **Deterministic scenario engine** — Simulates hourly demand, solar generation, battery state of charge, grid imports and exports, curtailment, operating cost, and carbon emissions.
- **Scenario comparison** — Compares baseline and candidate configurations with deterministic KPI deltas.
- **Forecasting** — Produces explainable seasonal-naive and rolling-mean forecast baselines.
- **Interactive dashboard** — Includes a Gradio interface and Plotly visualizations for system behavior and scenario KPIs.
- **FastAPI backend** — Exposes scenario, comparison, forecast, health, and explanation endpoints.
- **Offline-first operation** — Supports local execution without an API key or internet connection.
- **Optional weather integration** — Provides validated, cached external weather access with deterministic fixture fallback.
