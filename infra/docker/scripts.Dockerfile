# =============================================================================
# Scripts Dockerfile (데이터 Import, 유틸리티 스크립트용)
# =============================================================================
# NOTE: data 폴더와 scripts 폴더는 docker-compose에서 볼륨으로 마운트됨
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY infra/docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# libs만 COPY (scripts, data는 볼륨으로 마운트)
COPY libs /libs

ENV PYTHONPATH=/app:/libs:/data

CMD ["python", "-u"]
