# PDF Chat Agent - FastAPI Service
# Multi-stage build for production-ready container

FROM python:3.13-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better Docker cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY tools/ ./tools/
COPY ingestor/ ./ingestor/
COPY src/ ./src/
COPY configs/ ./configs/
COPY tests/ ./tests/

# Expose FastAPI port
EXPOSE 8000


# Run FastAPI with uvicorn
CMD ["uvicorn", "src.apis.main:app", "--host", "0.0.0.0", "--port", "8000"]
