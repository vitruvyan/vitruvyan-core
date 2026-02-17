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

COPY services/api_edge_oculus_prime/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

COPY vitruvyan_core /app/vitruvyan_core
COPY infrastructure/edge/oculus_prime /app/infrastructure/edge/oculus_prime
COPY services/api_edge_oculus_prime /app/services/api_edge_oculus_prime
COPY intake /app/intake
COPY oculus_prime /app/oculus_prime

ENV PYTHONPATH=/app:/app/vitruvyan_core

EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8050/health || exit 1

CMD ["uvicorn", "services.api_edge_oculus_prime.main:app", "--host", "0.0.0.0", "--port", "8050", "--workers", "1"]
