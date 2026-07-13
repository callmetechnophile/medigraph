FROM python:3.12-slim

WORKDIR /app

# Copy dependency configuration and source code
COPY pyproject.toml ./
COPY app/ ./app/

# Install pip dependencies directly into the system python environment
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Create temp directories for reports
RUN mkdir -p /app/tmp/reports

# Expose port (Render defaults to 10000)
EXPOSE 10000

# Run with uvicorn using shell to expand $PORT dynamically
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
