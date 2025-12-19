"""
Health endpoint property tests.

**Feature: aws-deployment-prep, Property 1: Health endpoint always returns 200 OK with status field**
**Validates: Requirements 1.1, 1.2**
"""
import os
import json
import pytest

# Configure Django settings before importing Django modules
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from hypothesis import given, strategies as st, settings, HealthCheck
from django.test import RequestFactory
from apps.health.views import health


class TestHealthEndpointProperty:
    """
    Property 1: Health endpoint always returns 200 OK with status field
    
    *For any* GET request to `/health` endpoint on backend service, 
    the response SHALL have HTTP status 200 and contain a JSON body 
    with `status` field equal to `"ok"`.
    """
    
    @given(
        # Generate various HTTP headers that might be sent
        user_agent=st.text(min_size=0, max_size=100),
        accept_header=st.sampled_from([
            "application/json",
            "text/html",
            "*/*",
            "application/xml",
        ]),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_health_endpoint_always_returns_200_with_status_ok(
        self, user_agent, accept_header
    ):
        """
        **Feature: aws-deployment-prep, Property 1: Health endpoint always returns 200 OK with status field**
        **Validates: Requirements 1.1, 1.2**
        
        For any valid HTTP request to /health, the response must:
        1. Have HTTP status code 200
        2. Contain valid JSON
        3. Have a "status" field equal to "ok"
        """
        request_factory = RequestFactory()
        
        # Create request with various headers
        request = request_factory.get(
            "/health",
            HTTP_USER_AGENT=user_agent,
            HTTP_ACCEPT=accept_header,
        )
        
        # Call the health view
        response = health(request)
        
        # Property assertions
        assert response.status_code == 200, "Health endpoint must return 200 OK"
        
        # Parse response content
        content = json.loads(response.content.decode("utf-8"))
        
        assert "status" in content, "Response must contain 'status' field"
        assert content["status"] == "ok", "Status field must be 'ok'"
    
    def test_health_endpoint_returns_json_content_type(self):
        """Verify health endpoint returns JSON content type."""
        request_factory = RequestFactory()
        request = request_factory.get("/health")
        response = health(request)
        
        assert response["Content-Type"] == "application/json"
