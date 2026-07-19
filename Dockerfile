# ==========================================
# BUILD STAGE
# ==========================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies in a virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# RUNTIME STAGE
# ==========================================
FROM python:3.11-slim

# Create a non-root user
RUN groupadd -r streamora && useradd -r -g streamora streamora

WORKDIR /app

# Install runtime dependencies (e.g., curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=streamora:streamora . .

# Set environment variables
ENV STREAMORA_ENV=production
ENV PYTHONPATH=/app
ENV PORT=8000

# Switch to non-root user
USER streamora

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health/live || exit 1

# Run with Gunicorn using Uvicorn workers
CMD sh -c "gunicorn services.agent.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}"
