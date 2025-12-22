"""
Health check endpoints for AWS ECS/ALB monitoring.

Provides:
- /health: Simple liveness check (always returns 200 OK)
- /ready: Readiness check (verifies database connectivity)
"""
from django.http import JsonResponse
from django.db import connection


def health(request):
    """
    Liveness probe endpoint.
    Returns 200 OK with {"status": "ok"} if the service is running.
    """
    return JsonResponse({"status": "ok"}, status=200)


def ready(request):
    """
    Readiness probe endpoint.
    Verifies database connectivity before returning 200 OK.
    Returns 503 Service Unavailable if database is not connected.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ok", "db": "connected"}, status=200)
    except Exception:
        return JsonResponse({"status": "error", "db": "disconnected"}, status=503)
