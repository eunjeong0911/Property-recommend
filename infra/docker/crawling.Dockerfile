FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and Korean fonts
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

COPY infra/docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browsers
RUN playwright install --with-deps chromium

COPY scripts /app/scripts

# Set default command (can be overridden by docker-compose)
CMD ["python", "scripts/data_import/importers/import_properties_full.py"]
