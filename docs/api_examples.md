# GridLens API Examples

All examples assume the app is running locally (`uvicorn app.main:app --reload`)
with **no** environment variables set — the offline/local-provider defaults.

## Health check

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool