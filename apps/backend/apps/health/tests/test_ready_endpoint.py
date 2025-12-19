"""
Ready endpoint property tests.

**Feature: aws-deployment-prep, Property 2: Ready endpoint reflects actual connectivity state**
**Validates: Requirements 1.3, 1.4**
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
from unittest.mock import patch, MagicMock
from apps.health.views import ready


class TestReadyEndpointProperty:
    """
    Property 2: Ready endpoint reflects actual connectivity state
    
    *For any* combination of service connectivity states (DB connected/disconnected),
    the `/ready` endpoint SHALL return HTTP 200 only when all required services 
    are connected, and HTTP 503 otherwise.
    """
    
    @given(
        db_connected=st.booleans()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_ready_endpoint_reflects_db_connectivity_state(self, db_connected):
        """
        **Feature: aws-deployment-prep, Property 2: Ready endpoint reflects actual connectivity state**
        **Validates: Requirements 1.3, 1.4**
        
        For any database connectivity state:
        - If DB is connected: return 200 with status "ok" and db "connected"
        - If DB is disconnected: return 503 with status "error" and db "disconnected"
        """
        request_factory = RequestFactory()
        request = request_factory.get("/ready")
        
        if db_connected:
            # Mock successful DB connection
            with patch('apps.health.views.connection') as mock_conn:
                mock_cursor = MagicMock()
                mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
                mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
                
                response = ready(request)
                
                assert response.status_code == 200, "Ready endpoint must return 200 when DB is connected"
                content = json.loads(response.content.decode("utf-8"))
                assert content["status"] == "ok"
                assert content["db"] == "connected"
        else:
            # Mock failed DB connection
            with patch('apps.health.views.connection') as mock_conn:
                mock_conn.cursor.side_effect = Exception("DB connection failed")
                
                response = ready(request)
                
                assert response.status_code == 503, "Ready endpoint must return 503 when DB is disconnected"
                content = json.loads(response.content.decode("utf-8"))
                assert content["status"] == "error"
                assert content["db"] == "disconnected"
    
    def test_ready_endpoint_returns_json_content_type(self):
        """Verify ready endpoint returns JSON content type."""
        request_factory = RequestFactory()
        request = request_factory.get("/ready")
        
        with patch('apps.health.views.connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            
            response = ready(request)
            
            assert response["Content-Type"] == "application/json"
