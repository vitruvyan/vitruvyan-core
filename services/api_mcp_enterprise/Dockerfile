# Dockerfile for MCP Enterprise Server
# Standalone enterprise MCP bridge (outside core docker-compose)

FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/api_mcp_enterprise/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy enterprise domain pack (needed for enterprise config/schemas)
COPY vitruvyan_core/domains/enterprise/mcp_server/ /app/domains/enterprise/mcp_server/

# Copy MCP Enterprise server code
COPY services/api_mcp_enterprise/main.py .
COPY services/api_mcp_enterprise/config.py .
COPY services/api_mcp_enterprise/adapters ./adapters
COPY services/api_mcp_enterprise/api ./api

EXPOSE 8021

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8021/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8021"]
