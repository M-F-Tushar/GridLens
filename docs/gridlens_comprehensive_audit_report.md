# GridLens — Comprehensive Architectural & Truthfulness Audit Report

**Date of Audit:** September 14, 2026  
**Subject:** Full Codebase Verification, Root File Inspection, Component Integration, and Failure Mode Analysis  
**Repository:** `GridLens`  

---

## Executive Summary

A comprehensive, file-by-file audit of the GridLens codebase was conducted to identify any discrepancies between documentation and implementation, locate broken or missing links in root files, verify the integration of all components, and establish an honest, unvarnished record of how and where the system can fail.

While GridLens functions reliably as a self-contained, educational, offline microgrid prototype (with 111 passing tests), several critical documentation inconsistencies, orphaned modules, container configuration gaps, and mathematical boundary constraints were uncovered.

---

## 1. Documentation & Root File Inconsistencies

### 1.1 Phantom Documentation Files in `README.md`
- **The Issue:** The root [`README.md`](file:///workspaces/GridLens/README.md) project layout section advertises several documentation files inside `docs/` that **do not exist on disk**:
  - `docs/data_provenance.md` (missing)
  - `docs/evaluation_results.md` (missing)
  - `docs/limitations.md` (missing)
  - `docs/runbook.md` (missing)
- **The Reality:** Only [`docs/architecture.md`](file:///workspaces/GridLens/docs/architecture.md) and [`docs/api_examples.md`](file:///workspaces/GridLens/docs/api_examples.md) exist in the `docs/` folder. The provenance documentation actually lives at [`data/fixtures/PROVENANCE.md`](file:///workspaces/GridLens/data/fixtures/PROVENANCE.md), and system limitations are documented under [`data/knowledge/system_limitations.md`](file:///workspaces/GridLens/data/knowledge/system_limitations.md).
- **Impact:** Any user or automated documentation tool clicking or following paths to `docs/runbook.md` or `docs/limitations.md` will encounter `404 File Not Found`.

### 1.2 Python Version Requirement Contradiction
- **The Issue:** [`README.md`](file:///workspaces/GridLens/README.md) claims support for `Python 3.10, 3.11, or 3.12`. However, [`pyproject.toml`](file:///workspaces/GridLens/pyproject.toml) explicitly enforces `requires-python = ">=3.11"`.
- **The Reality:** The project **strictly breaks on Python 3.10**. Both [`rag/answer.py`](file:///workspaces/GridLens/rag/answer.py#L3) and [`integrations/weather.py`](file:///workspaces/GridLens/integrations/weather.py#L5) execute:
  ```python
  from datetime import UTC, datetime
  ```
  `datetime.UTC` was introduced in Python 3.11. On Python 3.10, importing these modules throws a fatal `ImportError: cannot import name 'UTC' from 'datetime'`.

### 1.3 Missing Linter Dependency in `requirements.txt`
- **The Issue:** The project configuration in [`pyproject.toml`](file:///workspaces/GridLens/pyproject.toml) defines configuration for `ruff` (`[tool.ruff] line-length = 100`), and documentation instructions cite `python -m ruff check .`.
- **The Reality:** `ruff` is omitted from [`requirements.txt`](file:///workspaces/GridLens/requirements.txt). Running `python -m ruff check .` in a newly provisioned virtual environment fails with:
  ```text
  /workspaces/GridLens/.venv/bin/python: No module named ruff
  ```

### 1.4 Secret Exposure Vulnerability in `.dockerignore`
- **The Issue:** While [`.gitignore`](file:///workspaces/GridLens/.gitignore) properly ignores `.env`, [`.dockerignore`](file:///workspaces/GridLens/.dockerignore) does **not** include `.env`.
- **The Reality:** The `Dockerfile` executes `COPY . .`. If a developer creates a local `.env` file containing secrets (e.g., `OPENAI_API_KEY=sk-...`), building the Docker image will package the raw `.env` file directly into the image filesystem, exposing API keys to anyone pulling the container image.

---

## 2. Orphaned & Disconnected Subsystems

### 2.1 The Disconnected Weather Adapter (`integrations/weather.py`)
- **The Issue:** The [`OpenMeteoAdapter`](file:///workspaces/GridLens/integrations/weather.py#L42) is advertised in documentation as an integrated feature providing live solar and weather fetching with fallback.
- **The Reality:** `OpenMeteoAdapter` is an **isolated orphan**. Neither [`engine/scenario_engine.py`](file:///workspaces/GridLens/engine/scenario_engine.py), [`engine/forecast.py`](file:///workspaces/GridLens/engine/forecast.py), [`app/main.py`](file:///workspaces/GridLens/app/main.py), nor [`domain/models.py`](file:///workspaces/GridLens/domain/models.py) imports or executes this adapter. It is only called by its standalone test suite ([`tests/test_weather_adapter.py`](file:///workspaces/GridLens/tests/test_weather_adapter.py)). The simulation engine exclusively reads from static CSV fixture files.

### 2.2 Unused OpenAI Tool Specifications (`llm/tools.py`)
- **The Issue:** [`llm/tools.py`](file:///workspaces/GridLens/llm/tools.py) defines function schemas and dispatchers (`ToolSpec`, `list_tools()`, `call_tool()`) for tool-assisted LLM interactions.
- **The Reality:** No operational route or UI callback utilizes `llm/tools.py`. The `/api/explain` route uses retrieval and string prompt construction via [`rag/answer.py`](file:///workspaces/GridLens/rag/answer.py), bypassing the OpenAI function-calling mechanism entirely.

---

## 3. Containerization Discrepancies (`Dockerfile`)

### 3.1 Dead Port 7860 in Default Docker Container
- **The Issue:** [`Dockerfile`](file:///workspaces/GridLens/Dockerfile) specifies:
  ```dockerfile
  EXPOSE 8000 7860
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
  And [`README.md`](file:///workspaces/GridLens/README.md) instructs users:
  ```bash
  docker run -p 8000:8000 -p 7860:7860 gridlens
  ```
- **The Reality:** Uvicorn only binds to port 8000. Gradio (`ui/gradio_app.py`, intended for port 7860) is **never launched** by the container CMD. Users navigating to `http://localhost:7860` receive a `Connection Refused` error unless they manually run `docker exec <container> python -m ui.gradio_app`.

---

## 4. Engineering & Simulation Reality (How It Can Fail)

### 4.1 Fixed Single-Site Limitation
- **The Code:** [`engine/fixtures.py`](file:///workspaces/GridLens/engine/fixtures.py#L17) hardcodes:
  ```python
  KNOWN_SITES = frozenset({"campus-microgrid-a"})
  ```
- **Failure Mode:** Providing any other site name (e.g., `factory-1`, `hospital-b`) will raise a `ValueError: Unknown site`, causing the API to reject the request with HTTP 400. GridLens cannot simulate custom locations without manually modifying Python code and adding CSV files.

### 4.2 Two-Week Modulo Loop for Horizons > 336 Hours
- **The Code:** The fixture data contains exactly 336 rows (14 days). In [`engine/scenario_engine.py`](file:///workspaces/GridLens/engine/scenario_engine.py#L58):
  ```python
  row = rows[hour_index % len(rows)]
  ```
- **The Reality:** While `ScenarioRequest` caps `horizon_hours` at 168 (7 days), if the configuration is widened, simulations longer than two weeks will artificially duplicate the exact same two weeks of load and sunshine in an infinite repeating loop.

### 4.3 Asymmetric Battery Efficiency Accounting
- **The Code:** In [`engine/scenario_engine.py`](file:///workspaces/GridLens/engine/scenario_engine.py#L18-L30), round-trip efficiency ($\eta$) is split as $\sqrt{\eta}$ applied exclusively during charging:
  $$\text{SoC}_{\text{in}} = \text{Charge} \times \sqrt{\eta}$$
  $$\text{Loss} = \text{Charge} \times (1 - \sqrt{\eta})$$
- **The Reality:** Discharging applies **zero loss** to the state of charge. While mathematically valid for calculating net round-trip loss over a full cycle, it means the battery appears 100% efficient during discharge operations.

### 4.4 Omission of Electrical Physics & Grid Safety
- **The Reality:** The engine performs hourly algebraic arithmetic:
  $$\text{Grid Exchange} = \text{Demand} - \text{Solar} \pm \text{Battery}$$
- **The Risk:** GridLens does not model AC electrical physics. It does not calculate bus voltage fluctuations, power factor / reactive power (kVAR), electrical frequency, line thermal limits, or transformer saturation. If an engineer configured a 1,000 kW battery on a 100 kVA facility transformer, GridLens would show successful cost savings without warning that the physical equipment would fail or trip substation breakers.

---

## 5. RAG Retrieval & Groundedness Failure Modes

### 5.1 The Low-Threshold False-Positive Trap (0.05 vs. 0.30)
- **The Code:** [`rag/retriever.py`](file:///workspaces/GridLens/rag/retriever.py#L11) and [`domain/models.py`](file:///workspaces/GridLens/domain/models.py#L176) set:
  ```python
  DEFAULT_SIMILARITY_THRESHOLD = 0.05
  ```
- **The Mathematics:** [`rag/embeddings.py`](file:///workspaces/GridLens/rag/embeddings.py) uses a 256-bucket hash algorithm without semantics. Random word overlap across 256 buckets in English text routinely generates cosine similarity scores between 0.10 and 0.28.
- **The Failure Mode:** When queries are submitted to `/api/explain` using the default threshold (0.05), **abstention fails 100% of the time**. As verified by the test sweep in [`evaluation/eval.py`](file:///workspaces/GridLens/evaluation/eval.py):
  - At `threshold = 0.05`: `no_answer_correctness_rate` is **0.00**. Completely unrelated queries match random chunks and return bogus citations.
  - At `threshold = 0.30`: `no_answer_correctness_rate` is **1.00**, but on-topic hit rate drops from 1.00 to 0.80.
- **The Truth:** The API defaults to 0.05 to appear conversational, but this directly undermines the claimed "safeguard" of honest abstention unless callers explicitly override `similarity_threshold >= 0.30`.

### 5.2 Ephemeral In-Memory State Loss
- **The Reality:** Vector store chunk caches and [`SessionRegistry`](file:///workspaces/GridLens/llm/conversation.py#L46) reside purely in Python process RAM.
- **Failure Mode:** Any server restart, scaling event, or container reboot wipes all conversation memory, cached index hashes, and scenario histories instantly.

---

## 6. Actionable Remediation Checklist

To align the repository with reality and ensure complete transparency, the following changes are recommended:

1. **Synchronize Documentation with Code:**
   - Either create the missing files (`docs/data_provenance.md`, `docs/evaluation_results.md`, `docs/limitations.md`, `docs/runbook.md`) or update `README.md` to reference the existing files (`data/fixtures/PROVENANCE.md` and `data/knowledge/system_limitations.md`).
2. **Correct Version Specifiers:**
   - Update `README.md` to state `Requires Python 3.11 or 3.12` to prevent `ImportError` on Python 3.10.
3. **Add Developer Tooling to Dependencies:**
   - Add `ruff` to `requirements.txt` so linting commands work out of the box.
4. **Secure Container Build:**
   - Add `.env` to `.dockerignore` to prevent credential leakage in Docker images.
5. **Harmonize Docker Service Entrypoint:**
   - Update `Dockerfile` to launch both the FastAPI backend and Gradio UI (or clarify in `README.md` that Docker only runs the API by default).
6. **Harmonize RAG Threshold Default:**
   - Adjust `DEFAULT_SIMILARITY_THRESHOLD` from `0.05` to `0.25` - `0.30` in `domain/models.py` so the API abstains from answering off-topic questions by default.
