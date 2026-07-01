FROM python:3.11-slim

WORKDIR /app

ENV PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org download.pytorch.org"

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY infra/docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY analytics .

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
