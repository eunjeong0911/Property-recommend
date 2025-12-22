"""
Property-based tests for JSON logging format.

**Feature: aws-deployment-prep, Property 4: Logger outputs valid JSON**
**Validates: Requirements 5.1, 5.2, 5.3**
"""
import os
import sys
import json
import logging
import io
import pytest

# Configure Django settings before importing Django modules
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from hypothesis import given, strategies as st, settings, HealthCheck
from pythonjsonlogger import jsonlogger


def create_json_logger(stream: io.StringIO) -> logging.Logger:
    """Create a logger with JSON formatter for testing."""
    logger = logging.getLogger(f"test_logger_{id(stream)}")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    
    handler = logging.StreamHandler(stream)
    # Use standard format fields that pythonjsonlogger recognizes
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        timestamp=True
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Safe text strategy for log messages (excludes problematic characters)
safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-_:;가나다라마바사아자차카타파하"
safe_text = st.text(alphabet=safe_chars, min_size=1, max_size=200)


class TestJsonLogFormat:
    """
    Property 4: Logger outputs valid JSON
    
    *For any* log event (info, warning, error), the logger output SHALL be 
    parseable as valid JSON containing at minimum `timestamp`, `level`, 
    and `message` fields.
    """
    
    @given(
        message=safe_text,
        level=st.sampled_from(["debug", "info", "warning", "error", "critical"]),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_log_output_is_valid_json(self, message: str, level: str):
        """
        **Feature: aws-deployment-prep, Property 4: Logger outputs valid JSON**
        **Validates: Requirements 5.1, 5.2, 5.3**
        
        For any log message and level, the output must be valid JSON.
        """
        stream = io.StringIO()
        logger = create_json_logger(stream)
        
        # Log the message at the specified level
        log_method = getattr(logger, level)
        log_method(message)
        
        # Get the log output
        output = stream.getvalue().strip()
        
        # Must be parseable as JSON
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Log output is not valid JSON: {output!r}, error: {e}")
        
        assert isinstance(parsed, dict), "Log output must be a JSON object"
    
    @given(
        message=safe_text,
        level=st.sampled_from(["debug", "info", "warning", "error", "critical"]),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_log_contains_required_fields(self, message: str, level: str):
        """
        **Feature: aws-deployment-prep, Property 4: Logger outputs valid JSON**
        **Validates: Requirements 5.1, 5.2, 5.3**
        
        For any log event, the JSON output must contain timestamp, level, and message fields.
        """
        stream = io.StringIO()
        logger = create_json_logger(stream)
        
        # Log the message
        log_method = getattr(logger, level)
        log_method(message)
        
        # Parse the output
        output = stream.getvalue().strip()
        parsed = json.loads(output)
        
        # Check required fields (pythonjsonlogger uses asctime for timestamp, levelname for level)
        # We check for either the standard names or renamed versions
        has_timestamp = "timestamp" in parsed or "asctime" in parsed
        has_level = "level" in parsed or "levelname" in parsed
        assert has_timestamp, "Log must contain 'timestamp' or 'asctime' field"
        assert has_level, "Log must contain 'level' or 'levelname' field"
        assert "message" in parsed, "Log must contain 'message' field"
        
        # Verify level matches (check both possible field names)
        expected_level = level.upper()
        actual_level = parsed.get("level") or parsed.get("levelname")
        assert actual_level == expected_level, f"Level should be {expected_level}, got {actual_level}"
        
        # Verify message matches
        assert parsed["message"] == message, f"Message mismatch: expected {message!r}, got {parsed['message']!r}"
    
    @given(
        message=safe_text,
        extra_key=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20),
        extra_value=st.one_of(
            st.integers(min_value=-1000, max_value=1000),
            st.text(alphabet=safe_chars, min_size=1, max_size=50),
            st.booleans(),
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_log_with_extra_fields(self, message: str, extra_key: str, extra_value):
        """
        **Feature: aws-deployment-prep, Property 4: Logger outputs valid JSON**
        **Validates: Requirements 5.1, 5.2, 5.3**
        
        For any log event with extra fields, all fields must be included in the JSON output.
        """
        stream = io.StringIO()
        logger = create_json_logger(stream)
        
        # Log with extra fields
        logger.info(message, extra={extra_key: extra_value})
        
        # Parse the output
        output = stream.getvalue().strip()
        parsed = json.loads(output)
        
        # Check that extra field is present
        assert extra_key in parsed, f"Extra field '{extra_key}' should be in log output"
        assert parsed[extra_key] == extra_value, f"Extra field value mismatch"
    
    @given(
        exc_message=safe_text,
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_error_log_with_exception(self, exc_message: str):
        """
        **Feature: aws-deployment-prep, Property 4: Logger outputs valid JSON**
        **Validates: Requirements 5.1, 5.2, 5.3**
        
        For any error log with exception info, the output must include stack trace.
        """
        stream = io.StringIO()
        logger = create_json_logger(stream)
        
        # Log an error with exception
        try:
            raise ValueError(exc_message)
        except ValueError:
            logger.exception("An error occurred")
        
        # Parse the output
        output = stream.getvalue().strip()
        parsed = json.loads(output)
        
        # Check required fields (check both possible field names)
        has_timestamp = "timestamp" in parsed or "asctime" in parsed
        has_level = "level" in parsed or "levelname" in parsed
        assert has_timestamp, "Error log must contain 'timestamp' or 'asctime'"
        assert has_level, "Error log must contain 'level' or 'levelname'"
        assert "message" in parsed, "Error log must contain 'message'"
        
        actual_level = parsed.get("level") or parsed.get("levelname")
        assert actual_level == "ERROR", f"Exception log should have ERROR level, got {actual_level}"
        
        # Check for exception info (stack trace)
        # The exc_info field contains the traceback
        assert "exc_info" in parsed, "Exception log must contain 'exc_info' (stack trace)"
        assert exc_message in parsed["exc_info"], "Stack trace should contain exception message"

