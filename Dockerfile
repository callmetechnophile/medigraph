# ---- Build Stage ----
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml ./
COPY app/ ./app/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install .

# ---- Production Stage ----
FROM python:3.12-slim AS production

LABEL maintainer="Healthcare Intelligence Platform"
LABEL description="Enterprise Healthcare Intelligence Platform Backend"

# Security: run as non-root
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Create temp directories
RUN mkdir -p /app/tmp/reports && chown -R appuser:appuser /app

USER appuser

# Expose port (Render defaults to 10000 or $PORT)
EXPOSE 10000

# Run with uvicorn using shell to expand $PORT dynamically
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]

