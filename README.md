# GridLens — Energy-System Scenario and Decision Engine

An LLM-assisted energy intelligence platform for scenario modeling, forecasting, and evidence-grounded decision support.

GridLens combines a deterministic microgrid simulation engine with a grounded explanation layer. It enables users to model distributed energy resource scenarios involving electricity demand, solar PV generation, battery energy storage, grid imports and exports, operating costs, and carbon emissions.

All calculations are performed deterministically in Python. An LLM-powered retrieval-augmented generation (RAG) layer sits on top of those numerical outputs to explain system behavior, answer operational questions using cited project documentation, and communicate outcomes without modifying or inventing underlying values.

> **Design Principle:** GridLens uses AI for explanation and decision support—not for arithmetic. Every KPI is computed by the simulation engine first; the language model layer can only interpret results and cite verified evidence.

---

## Table of Contents

- [Why GridLens](#why-gridlens)
- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Project Layout](#project-layout)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Services](#running-the-services)
  - [Running with Docker](#running-with-docker)
- [API Reference and Examples](#api-reference-and-examples)
- [Evaluation and Verification](#evaluation-and-verification)
- [Known Limitations](#known-limitations)
- [Future Roadmap](#future-roadmap)
- [License](#license)

---

## Why GridLens?

Energy modeling tools frequently make it challenging for facility managers, planners, and engineers to understand *why* a particular microgrid configuration yields specific cost savings, emission reductions, or battery degradation profiles. GridLens bridges this gap by pairing transparent, reproducible numerical calculation with an auditable natural-language explanation interface.

Users can:
- Model solar PV and battery energy storage dispatch over configurable horizons (up to 168 hours).
- Compare two independent scenario configurations to measure cost, emission, and self-consumption deltas.
- Generate explainable baseline demand and solar forecasts.
- Review interactive dispatch and battery state-of-charge visualizations.
- Query system documentation on tariffs, round-trip efficiency, derating factors, and energy balance.
- Receive responses with chunk-level citations pointing directly to versioned knowledge base sources.
- Receive an explicit abstention response (`insufficient_evidence: true`) rather than an invented answer when a query falls outside available evidence.

---

## System Architecture

GridLens strictly separates the deterministic numerical layer from the conversational AI layer:

```text
+-----------------------------------------------------------------------+
|                           User Surfaces                               |
|          Gradio Web UI (4 Tabs)        |         FastAPI REST API     |
+----------------------------------------+------------------------------+
                                    |
                    +---------------+---------------+
                    |                               |
                    v                               v
    +------------------------------+  +-------------------------------+
    | Deterministic Engine Layer   |  | RAG & Explanation Layer       |
    | - scenario_engine.py         |  | - ingest.py & chunking.py     |
    | - compare.py                 |  | - store.py & retriever.py     |
    | - forecast.py                |  | - answer.py (cited facts)     |
    | - fixtures & tariffs         |  | - Local or Hosted LLM         |
    +------------------------------+  +-------------------------------+
                    |                               |
                    +---------------+---------------+
                                    |
                                    v
                    +-------------------------------+
                    | Knowledge Base & Fixture Data |
                    | - data/fixtures/*.csv         |
                    | - data/knowledge/*.md (12 docs|
                    +-------------------------------+
```

### Grounded-Answer Safeguards
- **Local Knowledge Base:** 12 structured Markdown documents with YAML front matter covering tariffs, storage efficiency, solar derating, carbon factors, forecasting, KPIs, energy balance, and limitations.
- **Citation Preservation:** Every evidence-backed claim references specific document chunk IDs (for example, `[kb-battery-efficiency::chunk-0]`).
- **Evidence-Based Abstention:** Questions outside the knowledge base trigger a standard "insufficient evidence" response instead of an ungrounded guess.
- **Deterministic Fact Injection:** All numerical values in explanations are derived from already-computed `ScenarioResult` or `ScenarioComparison` records.
- **Prompt Injection Defense:** Retrieved document chunks are formatted as untrusted data blocks, preventing prompt takeover.
- **Offline-First Operation:** Default configuration operates fully locally with zero external network calls or API keys required.

---

## Key Features

- **Deterministic Hourly Engine:** Computes demand, solar output, battery dispatch, battery losses, state of charge, grid import/export, curtailment, time-of-use costs, and emissions.
- **Energy Balance Validation:** Evaluates energy conservation and operational constraints at every time step; invalid states are caught and surfaced in diagnostics.
- **Scenario Comparison:** Generates numerical KPI deltas and deterministic narrative points directly in Python without LLM hallucination.
- **Baseline Forecasting:** Implements seasonal-naive and rolling-mean forecasting baselines for explainable load and generation estimates.
- **Cited Explanations:** Merges numerical facts with retrieved document chunks to produce verifiable explanations.
- **Interactive UI:** A 4-tab Gradio dashboard (Scenario, Forecast, Compare, Ask GridLens) with Plotly figures.
- **Hardened API:** FastAPI surface featuring Pydantic validation, CORS protection, structured JSON logging with secret redaction, and centralized error handling.
- **Weather Adapter:** Optional Open-Meteo adapter with local disk caching and automatic fixture fallback.

---

## Project Layout

```text
GridLens/
├── app/                        # FastAPI application layer
│   ├── config.py               # Environment configuration
│   ├── logging_config.py       # Structured JSON logging and request middleware
│   ├── main.py                 # REST API endpoints and exception handlers
│   └── schemas.py              # Request and response schemas
├── app.py                      # Standalone launcher for the Gradio interface
├── data/
│   ├── fixtures/               # Synthetic hourly demand, solar, and tariff data (+ PROVENANCE.md)
│   └── knowledge/              # 12 Markdown documentation files for RAG (+ system_limitations.md)
├── docs/                       # Architecture, runbooks, and evaluation notes
│   ├── architecture.md         # System design and boundaries
│   ├── api_examples.md         # Endpoint curl examples
│   ├── data_provenance.md      # Fixture origin documentation guide
│   ├── evaluation_results.md   # Retrieval and quality benchmark report
│   ├── gridlens_comprehensive_audit_report.md # Comprehensive architectural audit report
│   ├── limitations.md          # Technical and operational limitations guide
│   └── runbook.md              # Operations and triage runbook
├── domain/
│   └── models.py               # Shared Pydantic data contracts
├── engine/                     # Pure Python deterministic simulation
│   ├── compare.py              # Scenario delta calculation
│   ├── fixtures.py             # Fixture data loaders
│   ├── forecast.py             # Seasonal-naive and rolling-mean baselines
│   └── scenario_engine.py      # Hourly energy balance and battery dispatch
├── evaluation/
│   ├── eval.py                 # Retrieval and question evaluation harness
│   └── eval_set.json           # 12-case benchmark evaluation set
├── integrations/
│   └── weather.py              # Open-Meteo weather adapter with fallback
├── llm/
│   ├── conversation.py         # Session history registry
│   ├── openai_provider.py      # Hosted OpenAI client wrapper
│   └── provider.py             # LLM provider abstractions
├── rag/                        # Retrieval-augmented generation pipeline
│   ├── answer.py               # Citation and answer composition service
│   ├── chunking.py             # Deterministic Markdown chunking
│   ├── embeddings.py           # Dependency-free hash-based embeddings
│   ├── ingest.py               # Incremental file-hashed ingestion
│   ├── retriever.py            # Similarity scoring and vector search
│   └── store.py                # In-memory vector and keyword store
├── tests/                      # Full pytest test suite (111 tests)
├── ui/
│   ├── charts.py               # Plotly figure and markdown formatting helpers
│   └── gradio_app.py           # 4-tab Gradio user interface
├── Dockerfile                  # Production container definition
├── pyproject.toml              # Build and tool configuration
└── requirements.txt            # Python dependencies
```

---

## Getting Started

### Prerequisites

- Python 3.11 or 3.12
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/M-F-Tushar/GridLens.git
   cd GridLens
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment settings (optional, defaults work out-of-the-box):
   ```bash
   cp .env.example .env
   ```

### Running the Services

#### 1. Start the FastAPI Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Check service health:
```bash
curl -s http://127.0.0.1:8000/health
```

#### 2. Launch the Gradio Web Interface
In a separate terminal (with the virtual environment activated):
```bash
python -m ui.gradio_app
```
Open your browser at `http://127.0.0.1:7860`.

### Running with Docker

Build the container image:
```bash
docker build -t gridlens .
```

Run the container:
```bash
docker run -p 8000:8000 -p 7860:7860 gridlens
```

> **Note on Container Services:** The container entrypoint launches the FastAPI REST service on port 8000 by default. To also run the Gradio UI inside the container on port 7860, run:
> ```bash
> docker exec -it <container_id> python -m ui.gradio_app
> ```

---

## API Reference and Examples

### Run a Scenario
Execute an hourly simulation over a 24-hour horizon:
```bash
curl -s -X POST http://127.0.0.1:8000/api/scenarios/run \
  -H "Content-Type: application/json" \
  -d '{
        "scenario_id": "demo-1",
        "horizon_hours": 24,
        "solar_capacity_kwp": 250,
        "battery_capacity_kwh": 400
      }' | python3 -m json.tool
```

### Compare Two Scenarios
Compute deterministic KPI deltas and takeaway narratives between two configurations:
```bash
curl -s -X POST http://127.0.0.1:8000/api/scenarios/compare \
  -H "Content-Type: application/json" \
  -d '{
        "base": {"scenario_id": "no-battery", "battery_capacity_kwh": 0},
        "candidate": {"scenario_id": "with-battery", "battery_capacity_kwh": 500}
      }' | python3 -m json.tool
```

### Generate a Baseline Forecast
Generate 48 hours of seasonal-naive demand and solar expectations:
```bash
curl -s "http://127.0.0.1:8000/api/forecast?horizon_hours=48&method=seasonal_naive" \
  | python3 -m json.tool
```

### Request a Cited Explanation
Ask an operational question grounded in the documentation:
```bash
curl -s -X POST http://127.0.0.1:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{"question": "How is battery round-trip efficiency modeled?"}' \
  | python3 -m json.tool
```

### Honest Abstention on Off-Topic Questions
Unsupported questions return `insufficient_evidence: true` instead of a fabricated answer:
```bash
curl -s -X POST http://127.0.0.1:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of France?", "similarity_threshold": 0.5}' \
  | python3 -m json.tool
```

### Input Validation Error Handling
Invalid inputs are caught by Pydantic before reaching the calculation engine:
```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/api/scenarios/run \
  -H "Content-Type: application/json" \
  -d '{"scenario_id": "bad", "horizon_hours": -1}'
# Returns 422
```

---

## Evaluation and Verification

### Unit and Integration Tests
GridLens includes 111 comprehensive test cases covering simulation accuracy, comparison logic, forecast algorithms, RAG retrieval, citations, logging, and UI callbacks:
```bash
python -m pytest -q
```

### RAG Evaluation Benchmark
Run the retrieval quality and answer groundedness benchmark against the 12-question evaluation set:
```bash
python -m evaluation.eval
```

Benchmark output measures:
- Retrieval hit rate
- Mean Reciprocal Rank (MRR)
- Citation presence rate
- No-answer correctness rate
- End-to-end question answering latency

---

## Known Limitations

- **Hash-Based Embeddings:** The default vector search uses a deterministic 256-bucket hash algorithm to operate with zero dependencies. While sufficient for small corpora, unrelated queries can produce non-zero similarity scores (0.1 to 0.3) due to hash collisions.
- **Synthetic Data:** Default fixture profiles are illustrative. Results should not be used as the sole basis for real-world capital investments without validation against local metered data.

- **No AC Power-Flow Modeling:** GridLens performs hourly energy accounting (kWh). It does not model bus voltages, frequency, reactive power (kVAR), line impedance, or physical transformer overloading.
- **In-Memory Session State:** Session histories are stored in process memory and reset upon server restart.

---

## Future Roadmap

The following architectural and domain enhancements are planned for future releases:

1. **Semantic Embeddings and Persistent Vector Storage:**
   - Replace hash-based embeddings with dense sentence transformers (e.g., HuggingFace embeddings).
   - Integrate a persistent vector store (such as Chroma, Qdrant, or PostgreSQL with pgvector) to support multi-process deployments and expanding document libraries.

2. **Persistent Relational Database and Multi-Tenancy:**
   - Integrate PostgreSQL with SQLAlchemy/SQLModel and Alembic migrations.
   - Introduce user accounts, workspace management, scenario versioning, and exportable PDF/CSV audit summaries.

3. **Real-World Utility Ingestion Pipelines:**
   - Support Green Button XML/ESPI interval data ingestion and utility CSV meter uploads.
   - Connect to real-time marginal carbon APIs (such as WattTime or ElectricityMaps).
   - Ingest dynamic utility tariff structures via OpenEI or Genability tariff feeds.

4. **Expanded Asset and DER Modeling:**
   - Multi-battery dispatch and asset degradation modeling.
   - Electric vehicle (EV) charging depot scheduling and fleet demand profiles.
   - Flexible building loads (HVAC temperature deadbands and heat pump thermal storage).
   - Backup diesel/gas generator dispatch curves and fuel constraints.

5. **Physical Grid and Interconnection Safety Constraints:**
   - Connect simulation outputs to AC power-flow solvers (OpenDSS or PandaPower) to evaluate voltage regulation and transformer thermal limits.
   - Validate proposed dispatch schedules against utility interconnection standards (such as IEEE 1547).

6. **Automated CI/CD and Infrastructure:**
   - Implement GitHub Actions workflows for continuous integration, linting, and automated Docker container builds.
   - Provide production deployment configurations including Kubernetes manifests, Helm charts, and Docker Compose configurations.

---

## License

This project is licensed under the Apache License 2.0. See the `LICENSE` file for details.
