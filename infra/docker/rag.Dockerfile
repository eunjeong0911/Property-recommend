FROM python:3.11-slim

WORKDIR /app

COPY apps/rag/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/rag .
COPY libs /libs

ENV PYTHONPATH=/app:/libs

CMD ["python", "main.py"]
