FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY infra/docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/backend .
COPY libs /libs

ENV PYTHONPATH=/app:/libs

# Production server: gunicorn with 2 workers and keep-alive for ALB compatibility
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--keep-alive", "65"]
