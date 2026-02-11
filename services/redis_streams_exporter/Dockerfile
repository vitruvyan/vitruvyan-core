FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy exporter
COPY redis_streams_exporter.py .

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:9121/health').raise_for_status()"

# Run exporter
CMD ["python3", "redis_streams_exporter.py"]
