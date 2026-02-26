FROM python:3.11-slim

WORKDIR /app

# System deps for scipy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Install service dependencies
COPY services/api_edge_dse/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install vitruvyan_core (PYTHONPATH includes /app so core.* imports resolve)
COPY vitruvyan_core /app/vitruvyan_core
COPY infrastructure /app/infrastructure

# Copy service source
COPY services/api_edge_dse /app/services/api_edge_dse

# PYTHONPATH so that `from core.*` and `from infrastructure.edge.dse.*` resolve
ENV PYTHONPATH="/app/vitruvyan_core:/app"

EXPOSE 8021

CMD ["python", "-m", "services.api_edge_dse.main"]
