FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and locales
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Set locale for Korean support
RUN locale-gen ko_KR.UTF-8
ENV LANG ko_KR.UTF-8
ENV LANGUAGE ko_KR.UTF-8
ENV LC_ALL ko_KR.UTF-8
ENV PYTHONIOENCODING=utf-8

COPY infra/docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/rag .
COPY libs /libs

ENV PYTHONPATH=/app:/libs

# Production server: uvicorn with 2 workers for production traffic
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
