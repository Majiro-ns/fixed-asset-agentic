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
COPY ui/styles.py ./ui/
COPY ui/similar_cases.py ./ui/
COPY ui/components/ ./ui/components/

# Copy demo data (optional, for local demo mode)
COPY data/demo/ ./data/demo/

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup --home /home/appuser appuser \
    && mkdir -p /home/appuser/.streamlit && chown -R appuser:appgroup /home/appuser
ENV HOME=/home/appuser
USER appuser

# Expose Streamlit default port
EXPOSE 8501

# Cloud Run sets PORT env var automatically
ENV PORT=8501

# API URL configurable via build arg or runtime env var
ARG API_URL=http://localhost:8080
ENV API_URL=${API_URL}

# Start Streamlit with Cloud Run compatible settings
CMD ["sh", "-c", "exec streamlit run ui/app_minimal.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]
