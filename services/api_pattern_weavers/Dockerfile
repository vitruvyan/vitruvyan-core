FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY docker/services/api_pattern_weavers/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy core modules, config, and service
COPY core/ ./core/
COPY config/ ./config/
COPY docker/services/api_pattern_weavers/ ./docker/services/api_pattern_weavers/

# Make startup script executable
RUN chmod +x ./docker/services/api_pattern_weavers/start.sh

# Expose port
EXPOSE 8017

# Health check (using Python instead of curl since curl is not installed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import httpx; r=httpx.get('http://localhost:8017/health', timeout=5.0); exit(0 if r.status_code == 200 else 1)"

# Run both API and Redis listener
CMD ["./docker/services/api_pattern_weavers/start.sh"]
