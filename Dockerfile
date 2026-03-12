# Multi-stage build for Liases Foras Application
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend requirements and install
COPY frontend/requirements.txt ./frontend/requirements.txt
RUN pip install --no-cache-dir -r frontend/requirements.txt

# Copy application code
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Copy additional necessary files
COPY .env.production.example ./.env.example

# Create necessary directories
RUN mkdir -p /app/output /app/logs

# Expose ports
# Backend API
EXPOSE 8000
# Frontend Streamlit
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default command (can be overridden)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
