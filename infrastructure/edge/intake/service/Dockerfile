# Dockerfile for Intake API (Edge placement)

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY infrastructure/edge/intake/service/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

# Shared core package + edge intake module
COPY vitruvyan_core /app/vitruvyan_core
COPY infrastructure/edge/intake /app/infrastructure/edge/intake
COPY intake /app/intake

# Allow both `vitruvyan_core.core...` and legacy `core...` imports
ENV PYTHONPATH=/app:/app/vitruvyan_core

EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8050/health || exit 1

CMD ["uvicorn", "infrastructure.edge.intake.service.main:app", "--host", "0.0.0.0", "--port", "8050", "--workers", "1"]
