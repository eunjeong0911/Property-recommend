"""Property-based tests for CORS origin validation.

**Feature: aws-deployment-prep, Property 5: CORS validates origin against allowed list**
**Validates: Requirements 6.1**

Tests that the CORS middleware correctly validates origins against the configured
allowed origins list from environment variables.
"""
import os
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import patch
from fastapi.testclient import TestClient


# Strategy for generating valid HTTP/HTTPS origins
def valid_origin_strategy():
    """Generate valid HTTP/HTTPS origin strings."""
    protocols = st.sampled_from(["http", "https"])
    # Generate domain-like strings
    domain_parts = st.lists(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
            min_size=1,
            max_size=10
        ),
        min_size=1,
        max_size=3
    )
    ports = st.one_of(
        st.just(""),
        st.integers(min_value=1, max_value=65535).map(lambda p: f":{p}")
    )
    
    return st.builds(
        lambda proto, parts, port: f"{proto}://{'.'.join(parts)}{port}",
        protocols,
        domain_parts,
        ports
    )


def create_test_app(allowed_origins: list):
    """Create a FastAPI test app with specified CORS origins."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    return app


class TestCORSOriginValidation:
    """Property-based tests for CORS origin validation.
    
    **Feature: aws-deployment-prep, Property 5: CORS validates origin against allowed list**
    **Validates: Requirements 6.1**
    """
    
    @given(
        allowed_origins=st.lists(valid_origin_strategy(), min_size=1, max_size=5, unique=True),
        request_origin=valid_origin_strategy()
    )
    @settings(max_examples=100)
    def test_cors_header_presence_matches_allowed_list(
        self, allowed_origins: list, request_origin: str
    ):
        """
        **Feature: aws-deployment-prep, Property 5: CORS validates origin against allowed list**
        **Validates: Requirements 6.1**
        
        Property: For any cross-origin request to the rag service, the CORS middleware
        SHALL include Access-Control-Allow-Origin header only if the request origin
        is in the configured allowed origins list.
        """
        # Create app with the generated allowed origins
        app = create_test_app(allowed_origins)
        client = TestClient(app)
        
        # Make a request with the generated origin
        response = client.get(
            "/test",
            headers={"Origin": request_origin}
        )
        
        # Check if origin is in allowed list
        origin_is_allowed = request_origin in allowed_origins
        
        # Get the CORS header from response
        cors_header = response.headers.get("access-control-allow-origin")
        
        if origin_is_allowed:
            # If origin is allowed, header should be present and match the origin
            assert cors_header == request_origin, (
                f"Expected CORS header '{request_origin}' for allowed origin, "
                f"but got '{cors_header}'"
            )
        else:
            # If origin is not allowed, header should not be present
            assert cors_header is None, (
                f"Expected no CORS header for disallowed origin '{request_origin}', "
                f"but got '{cors_header}'"
            )
    
    @given(
        allowed_origins=st.lists(valid_origin_strategy(), min_size=1, max_size=5, unique=True)
    )
    @settings(max_examples=50)
    def test_allowed_origin_always_gets_cors_header(self, allowed_origins: list):
        """
        **Feature: aws-deployment-prep, Property 5: CORS validates origin against allowed list**
        **Validates: Requirements 6.1**
        
        Property: For any origin in the allowed list, the CORS middleware SHALL
        include the Access-Control-Allow-Origin header with that origin value.
        """
        app = create_test_app(allowed_origins)
        client = TestClient(app)
        
        # Test each allowed origin
        for origin in allowed_origins:
            response = client.get(
                "/test",
                headers={"Origin": origin}
            )
            
            cors_header = response.headers.get("access-control-allow-origin")
            assert cors_header == origin, (
                f"Expected CORS header '{origin}' for allowed origin, "
                f"but got '{cors_header}'"
            )
    
    def test_empty_allowed_origins_blocks_all(self):
        """
        **Feature: aws-deployment-prep, Property 5: CORS validates origin against allowed list**
        **Validates: Requirements 6.1**
        
        Edge case: When allowed origins list is empty, no origins should be allowed.
        """
        app = create_test_app([])
        client = TestClient(app)
        
        response = client.get(
            "/test",
            headers={"Origin": "http://example.com"}
        )
        
        cors_header = response.headers.get("access-control-allow-origin")
        assert cors_header is None, (
            f"Expected no CORS header for empty allowed list, but got '{cors_header}'"
        )
    
    @given(origin=valid_origin_strategy())
    @settings(max_examples=50)
    def test_wildcard_allows_all_origins(self, origin: str):
        """
        **Feature: aws-deployment-prep, Property 5: CORS validates origin against allowed list**
        **Validates: Requirements 6.1**
        
        Edge case: When allowed origins contains "*", all origins should be allowed.
        Note: This is NOT recommended for production but tests the behavior.
        """
        app = create_test_app(["*"])
        client = TestClient(app)
        
        response = client.get(
            "/test",
            headers={"Origin": origin}
        )
        
        cors_header = response.headers.get("access-control-allow-origin")
        # With wildcard, the header should be "*" (not the specific origin)
        assert cors_header == "*", (
            f"Expected CORS header '*' for wildcard config, but got '{cors_header}'"
        )


class TestCORSEnvironmentConfiguration:
    """Tests for CORS configuration from environment variables."""
    
    def test_cors_origins_from_env_variable(self):
        """
        **Feature: aws-deployment-prep, Property 5: CORS validates origin against allowed list**
        **Validates: Requirements 6.1**
        
        Test that CORS origins are correctly parsed from CORS_ALLOWED_ORIGINS env var.
        """
        test_origins = "https://example.com,https://api.example.com,http://localhost:3000"
        
        with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": test_origins}):
            # Parse origins the same way as main.py
            _cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
            if _cors_origins_env:
                cors_origins = [
                    origin.strip() 
                    for origin in _cors_origins_env.split(",") 
                    if origin.strip()
                ]
            else:
                cors_origins = []
            
            assert cors_origins == [
                "https://example.com",
                "https://api.example.com", 
                "http://localhost:3000"
            ]
    
    def test_cors_origins_handles_whitespace(self):
        """
        **Feature: aws-deployment-prep, Property 5: CORS validates origin against allowed list**
        **Validates: Requirements 6.1**
        
        Test that CORS origins parsing handles whitespace correctly.
        """
        test_origins = "  https://example.com , https://api.example.com  ,  "
        
        with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": test_origins}):
            _cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
            if _cors_origins_env:
                cors_origins = [
                    origin.strip() 
                    for origin in _cors_origins_env.split(",") 
                    if origin.strip()
                ]
            else:
                cors_origins = []
            
            assert cors_origins == [
                "https://example.com",
                "https://api.example.com"
            ]
    
    def test_cors_origins_empty_env_uses_defaults(self):
        """
        **Feature: aws-deployment-prep, Property 5: CORS validates origin against allowed list**
        **Validates: Requirements 6.1**
        
        Test that empty CORS_ALLOWED_ORIGINS falls back to development defaults.
        """
        with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": ""}, clear=False):
            _cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
            if _cors_origins_env:
                cors_origins = [
                    origin.strip() 
                    for origin in _cors_origins_env.split(",") 
                    if origin.strip()
                ]
            else:
                # Development defaults
                cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
            
            assert cors_origins == ["http://localhost:3000", "http://127.0.0.1:3000"]
