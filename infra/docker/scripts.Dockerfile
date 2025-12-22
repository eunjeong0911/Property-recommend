FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY infra/docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts .
COPY libs /libs
COPY data /data
COPY data/GraphDB_data /GraphDB_data

ENV PYTHONPATH=/app:/libs

CMD ["python", "-u"]
