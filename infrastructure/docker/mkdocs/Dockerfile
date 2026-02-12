# ============================================================================
# MkDocs Documentation Server — Vitruvyan Core
# ============================================================================
# Purpose: Serve documentation as static site with hot-reload
# Pattern: infrastructure utility (monitoring-like)
# Port:    9800 → 8000 (internal)
# ============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install MkDocs and plugins
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Documentation will be mounted as volumes
EXPOSE 8000

# Default command (can be overridden in docker-compose.yml)
CMD ["mkdocs", "serve", "-a", "0.0.0.0:8000"]
