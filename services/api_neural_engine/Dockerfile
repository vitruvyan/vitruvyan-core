# Dockerfile per Vitruvyan Neural Engine API
# Multi-stage build seguendo pattern Sacred Orders

# ===========================
# STAGE 1: Base Dependencies
# ===========================
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ===========================
# STAGE 2: Python Dependencies
# ===========================
FROM base as dependencies

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY infrastructure/docker/requirements/requirements.neural_engine.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ===========================
# STAGE 3: Application
# ===========================
FROM dependencies as final

# Set working directory
WORKDIR /app

# Copy vitruvyan_core package (domain-agnostic neural engine)
COPY vitruvyan_core/ /app/vitruvyan_core/
# Compatibility aliases for legacy absolute imports used across core/contracts.
COPY vitruvyan_core/core/ /app/core/
COPY vitruvyan_core/contracts/ /app/contracts/
COPY vitruvyan_core/domains/ /app/domains/

# Copy service code
COPY services/api_neural_engine/ /app/services/api_neural_engine/

# Set PYTHONPATH to include /app
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create non-root user for security
RUN useradd -m -u 1000 vitruvyan && \
    chown -R vitruvyan:vitruvyan /app

USER vitruvyan

# Expose port 8003 (Neural Engine canonical port in Vitruvyan ecosystem)
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run FastAPI application with Uvicorn
CMD ["uvicorn", "services.api_neural_engine.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8003", \
     "--workers", "2", \
     "--log-level", "info"]
