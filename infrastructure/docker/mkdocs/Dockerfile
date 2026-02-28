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

# Create output directories and symlinked docs_root (for full site)
# Create separate docs_root_public (for public landing page only)
RUN mkdir -p /app/site /app/site_public /app/site_docs_public /app/docs_root /app/docs_root_public && \
    ln -s /app/docs /app/docs_root/docs && \
    ln -s /app/vitruvyan_core /app/docs_root/vitruvyan_core && \
    ln -s /app/vitruvyan_edge /app/docs_root/vitruvyan_edge && \
    ln -s /app/services /app/docs_root/services && \
    ln -s /app/infrastructure /app/docs_root/infrastructure && \
    ln -s /app/tests /app/docs_root/tests && \
    ln -s /app/examples /app/docs_root/examples && \
    ln -s /app/config /app/docs_root/config && \
    ln -s /app/scripts /app/docs_root/scripts && \
    ln -s /app/index.md /app/docs_root/index.md && \
    ln -s /app/index.it.md /app/docs_root/index.it.md

# Documentation will be mounted as volumes
EXPOSE 8000

# Default command: serve both sites (dev mode with hot-reload on full site)
CMD ["mkdocs", "serve", "-a", "0.0.0.0:8000"]
