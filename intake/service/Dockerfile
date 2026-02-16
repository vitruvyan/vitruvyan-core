# Dockerfile for AEGIS Intake API (CAD/BIM + Financial + Text)
# Multi-stage build for optimized container size

# ===========================
# STAGE 1: Base Dependencies
# ===========================
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (for ezdxf, ifcopenshell, image processing)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ===========================
# STAGE 2: Python Dependencies
# ===========================
FROM base as dependencies

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY services/core/api_aegis_intake/requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ===========================
# STAGE 3: Application Code
# ===========================
FROM dependencies as runtime

# Set working directory
WORKDIR /app

# Copy entire vitruvyan_core (shared library)
COPY vitruvyan_core /app/vitruvyan_core

# Copy service code
COPY services/core/api_aegis_intake /app/services/core/api_aegis_intake

# Set Python path to include app directory
ENV PYTHONPATH=/app:${PYTHONPATH}

# Expose port
EXPOSE 8022

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8022/health || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "services.core.api_aegis_intake.main:app", "--host", "0.0.0.0", "--port", "8022", "--workers", "1"]
