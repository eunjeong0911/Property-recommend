# =============================================================================
# RAG Service Dockerfile - Optimized for AWS ECS Deployment
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY apps/rag/requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Security: Create non-root user
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install runtime dependencies and locale support
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && sed -i '/ko_KR.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen

# Set locale for Korean support
ENV LANG=ko_KR.UTF-8 \
    LANGUAGE=ko_KR.UTF-8 \
    LC_ALL=ko_KR.UTF-8 \
    PYTHONIOENCODING=utf-8

# Copy wheels and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY --chown=appuser:appgroup apps/rag /app
COPY --chown=appuser:appgroup libs /libs

ENV PYTHONPATH=/app:/libs \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Production: uvicorn with multiple workers
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8001", \
     "--workers", "2", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--access-log"]
