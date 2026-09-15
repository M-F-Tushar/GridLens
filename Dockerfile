# GridLens — production image (FastAPI + Gradio UI).
#
# Build:  docker build -t gridlens .
# Run:    docker run --rm -p 8000:8000 -p 7860:7860 gridlens
#
# Runs fully offline with zero secrets set; set OPENAI_API_KEY (and
# GRIDLENS_LLM_PROVIDER=openai) via -e flags only if you want a hosted
# provider for the explanation service.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV GRIDLENS_ENV=production \
    PYTHONUNBUFFERED=1 \
    GRADIO_SERVER_NAME=0.0.0.0

EXPOSE 8000 7860

# Starts the FastAPI service; the Gradio UI can be run separately in the
# same image with: docker exec <container> python -m ui.gradio_app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]