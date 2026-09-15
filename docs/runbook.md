# GridLens — Operations & Triage Runbook

This runbook provides actionable procedures for bootstrapping, operating, verifying, and troubleshooting GridLens in development and production environments.

---

## 1. Quick Start & Service Execution

### Virtual Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Start the FastAPI REST Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Healthcheck: `curl -s http://localhost:8000/health`

### Launch the Gradio Web Interface
```bash
python -m ui.gradio_app
```
- Web UI: `http://localhost:7860`

---

## 2. Docker Operations

### Build Image
```bash
docker build -t gridlens .
```

### Run Container
```bash
docker run -d --name gridlens-svc -p 8000:8000 -p 7860:7860 gridlens
```

### Accessing the Web UI in Container
By default, the container entrypoint launches the FastAPI REST API on port 8000. To launch the Gradio Web UI on port 7860 within the running container:
```bash
docker exec -d gridlens-svc python -m ui.gradio_app
```

---

## 3. Verification & Code Quality

### Run Unit & Integration Tests
```bash
python -m pytest -q
```

### Run Evaluation Harness
```bash
python -m evaluation.eval
```

### Linting & Formatting
```bash
python -m ruff check .
```

---

## 4. Troubleshooting & Triage

| Symptom | Cause | Resolution |
|---|---|---|
| `ImportError: cannot import name 'UTC' from 'datetime'` | Running on Python 3.10 | Upgrade runtime to Python 3.11 or 3.12. |
| `HTTP 400 Unknown site: <site_name>` | Request specifies an unsupported site | GridLens currently supports `campus-microgrid-a`. Check fixture data. |
| Connection Refused on `http://localhost:7860` (Docker) | Gradio has not been launched inside container | Run `docker exec -d <container> python -m ui.gradio_app`. |
| `/api/explain` returns `insufficient_evidence: true` | Query is off-topic or score is below threshold (`0.30`) | Query topic is outside knowledge base; provide relevant documentation or verify query phrasing. |
| Session state lost after restart | In-memory session registry | Process memory resets on restart; persistent storage requires external database integration. |
