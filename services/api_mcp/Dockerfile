# Dockerfile for MCP Server (vitruvyan-core)
# Model Context Protocol Bridge to Sacred Orders

FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements from correct path
COPY services/mcp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy vitruvyan_core foundation modules (minimal dependencies)
COPY vitruvyan_core/core/__init__.py ./vitruvyan_core/core/__init__.py
COPY vitruvyan_core/core/foundation/__init__.py ./vitruvyan_core/core/foundation/__init__.py
COPY vitruvyan_core/core/foundation/persistence ./vitruvyan_core/core/foundation/persistence

# Copy MCP server main.py
COPY services/mcp/main.py .

# Expose port
EXPOSE 8020

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8020/health || exit 1

# Run server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8020", "--reload"]
