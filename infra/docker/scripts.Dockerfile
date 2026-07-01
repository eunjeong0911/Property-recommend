# =============================================================================
# Scripts Dockerfile (데이터 Import, 유틸리티 스크립트용)
# =============================================================================
# NOTE: scripts와 apps(모델 포함)는 이미지에 포함됨. data 폴더만 볼륨 마운트됨
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

ENV PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org download.pytorch.org"

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Common Requirements
COPY infra/docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only for crawling)
# RUN playwright install --with-deps chromium

# Install ML Dependencies for Reco Models (Cpu-only to save space)
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host download.pytorch.org \
    --trusted-host download-r2.pytorch.org \
    "torch>=2.1" --extra-index-url https://download.pytorch.org/whl/cpu \
    "xgboost>=2.0.0" \
    "lightgbm>=4.0"

# Copy Code & Models (Bake into image)
COPY libs /libs
COPY scripts /app/scripts
COPY apps /app/apps

ENV PYTHONPATH=/app:/libs:/data

CMD ["python", "-u", "scripts/run_all.py"]


