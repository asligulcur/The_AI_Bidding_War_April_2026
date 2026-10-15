# Hub-and-spoke procurement orchestrator (Python + Anthropic)
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ ./agents/
COPY skills/ ./skills/
COPY config ./config/
COPY orchestrator.py .

# ANTHROPIC_API_KEY must be supplied at runtime (e.g. --env-file .env)
ENV ANTHROPIC_MODEL=claude-sonnet-4-6

CMD ["python", "orchestrator.py"]
