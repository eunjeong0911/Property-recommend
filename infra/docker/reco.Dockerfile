FROM python:3.11-slim

WORKDIR /app

COPY infra/docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/reco .
COPY libs /libs

ENV PYTHONPATH=/app:/libs

CMD ["python", "serve.py"]
