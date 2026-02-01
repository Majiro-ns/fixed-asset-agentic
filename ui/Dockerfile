# Streamlit UI Dockerfile
# Build from project root: docker build -f ui/Dockerfile -t fixed-asset-ui .
FROM python:3.11-slim

WORKDIR /app

# Install UI dependencies only
RUN pip install --no-cache-dir \
    streamlit \
    requests \
    pydantic>=2.0.0

# Copy UI code
COPY ui/app_minimal.py ./ui/

# Copy demo data (optional, for local demo mode)
COPY data/demo/ ./data/demo/

# Expose Streamlit default port
EXPOSE 8501

# Cloud Run sets PORT env var automatically
ENV PORT=8501

# API URL can be overridden via environment variable
ENV API_URL="https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"

# Start Streamlit with Cloud Run compatible settings
CMD ["sh", "-c", "exec streamlit run ui/app_minimal.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]
