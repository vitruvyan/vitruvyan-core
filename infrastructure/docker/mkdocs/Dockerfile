# ============================================================================
# MkDocs Documentation Server — Vitruvyan Core
# ============================================================================
# Purpose: Serve documentation as static site with hot-reload
# Pattern: infrastructure utility (monitoring-like)
# Port:    9800 → 8000 (internal)
# ============================================================================

FROM python:3.11-slim

# Install system dependencies (git for git-revision-date-localized plugin)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install MkDocs and plugins
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy build script
COPY build-all.sh /app/build-all.sh
RUN chmod +x /app/build-all.sh

# Create site directories
RUN mkdir -p /app/site /app/site_public

# Documentation will be mounted as volumes
EXPOSE 8000

# Default command: serve both sites (dev mode with hot-reload on full site)
CMD ["mkdocs", "serve", "-a", "0.0.0.0:8000"]
