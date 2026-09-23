# IDMAP Backend Dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies (build-essential, curl, git for prisma/packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy Prisma schema and generate client
COPY prisma ./prisma
RUN prisma generate --schema=./prisma/schema.prisma || true

# Copy application source code
COPY backend ./backend
COPY src ./src
COPY docs ./docs

# Create directories for reports and models
RUN mkdir -p reports/retraining src/cv_models/checkpoints

EXPOSE 8000

# Command to launch FastAPI
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
