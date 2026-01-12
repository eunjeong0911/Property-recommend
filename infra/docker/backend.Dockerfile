# =============================================================================
# Backend Dockerfile - Optimized for AWS ECS Deployment
# =============================================================================
# Multi-stage build for smaller image size and better security

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY apps/backend/requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Production image
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Security: Create non-root user
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY --chown=appuser:appgroup apps/backend /app
COPY --chown=appuser:appgroup libs /libs

# Set environment variables
ENV PYTHONPATH=/app:/libs \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Collect static files (if needed)
RUN python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check for ALB/ECS
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Production server: gunicorn with optimized settings
# - workers: 2 * CPU + 1 (adjust based on ECS task CPU)
# - keep-alive: 65s (must be > ALB idle timeout of 60s)
# - timeout: 30s for request processing
# - graceful-timeout: 30s for graceful shutdown
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--threads", "4", \
     "--worker-class", "gthread", \
     "--keep-alive", "65", \
     "--timeout", "30", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output"]
