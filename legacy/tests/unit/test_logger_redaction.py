#!/usr/bin/env python3
"""
Unit Tests for Logger PII/Secret Redaction

Tests the redact_sensitive() function in scripts/logger.py to ensure:
- API keys, tokens, and credentials are masked
- Email addresses are partially redacted
- Private keys are removed
- Non-sensitive data remains intact
- Redaction never crashes (safe_by_default=True)
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from logger import redact_sensitive


class TestAPIKeyRedaction:
    """Test redaction of API keys and tokens"""

    def test_openai_key_redaction(self):
        """OpenAI API keys (sk-...) should be redacted"""
        text = "Using API key: sk-1234567890abcdefghijklmnopqrstuvwxyz"
        result = redact_sensitive(text)
        assert "sk-1234567890" not in result
        assert "[REDACTED_API_KEY]" in result

    def test_aws_key_redaction(self):
        """AWS access keys (AKIA...) should be redacted"""
        text = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        result = redact_sensitive(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "[REDACTED_AWS_KEY]" in result

    def test_google_api_key_redaction(self):
        """Google API keys (AIza...) should be redacted"""
        text = "GOOGLE_API_KEY=AIzaSyDaGmWKa4JsXZ-HjGw7ISLn_3namBGewQe"
        result = redact_sensitive(text)
        assert "AIzaSyDaGmWKa4JsXZ" not in result
        assert "[REDACTED_GOOGLE_KEY]" in result

    def test_bearer_token_redaction(self):
        """Bearer tokens (JWT format) should be redacted"""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = redact_sensitive(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "[REDACTED_JWT]" in result


class TestSessionTokenRedaction:
    """Test redaction of session tokens and cookies"""

    def test_session_token_redaction(self):
        """Session tokens should be redacted"""
        text = 'session_token: "abc123def456ghi789jkl012mno345"'
        result = redact_sensitive(text)
        assert "abc123def456ghi789jkl012mno345" not in result
        assert "[REDACTED_TOKEN]" in result

    def test_cookie_redaction(self):
        """Cookie values should be redacted"""
        text = "Cookie: sessionid=1234567890abcdefghijklmnopqrstuvwxyz;"
        result = redact_sensitive(text)
        assert "1234567890abcdefghijklmnopqrstuvwxyz" not in result
        assert "[REDACTED_COOKIE]" in result


class TestPrivateKeyRedaction:
    """Test redaction of private key blocks"""

    def test_rsa_private_key_redaction(self):
        """RSA private key blocks should be completely removed"""
        text = """
        -----BEGIN RSA PRIVATE KEY-----
        MIIEpAIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyz
        -----END RSA PRIVATE KEY-----
        """
        result = redact_sensitive(text)
        assert "MIIEpAIBAAKCAQEA1234567890" not in result
        assert "[REDACTED_PRIVATE_KEY]" in result


class TestEmailRedaction:
    """Test partial email address redaction"""

    def test_email_partial_redaction(self):
        """Email addresses should be partially masked (keep domain for debugging)"""
        text = "User email: john.doe@example.com"
        result = redact_sensitive(text)
        assert "john.doe" not in result  # Local part masked
        assert "@example.com" in result  # Domain preserved
        assert "jo***@example.com" in result

    def test_email_short_username(self):
        """Short usernames should still be masked"""
        text = "Support: a@test.org"
        result = redact_sensitive(text)
        assert "a@test.org" not in result
        assert "***@test.org" in result or "a***@test.org" in result


class TestDictRedaction:
    """Test redaction in dict/JSON structures"""

    def test_dict_with_api_key(self):
        """Dicts with 'api_key' field should be redacted"""
        data = {"api_key": "sk-1234567890abcdefghij", "status": "ok"}
        result = redact_sensitive(data)
        assert result["api_key"] == "[REDACTED]"
        assert result["status"] == "ok"

    def test_dict_with_password(self):
        """Dicts with 'password' field should be redacted"""
        data = {"username": "admin", "password": "secret123"}
        result = redact_sensitive(data)
        assert result["password"] == "[REDACTED]"
        assert result["username"] == "admin"

    def test_nested_dict_redaction(self):
        """Nested dicts should be recursively redacted"""
        data = {
            "config": {
                "db": {
                    "host": "localhost",
                    "password": "dbpass123"
                }
            }
        }
        result = redact_sensitive(data)
        assert result["config"]["db"]["password"] == "[REDACTED]"
        assert result["config"]["db"]["host"] == "localhost"

    def test_dict_with_string_containing_secret(self):
        """String values in dicts should be pattern-redacted"""
        data = {"log_message": "API call failed with key sk-test123456789012345"}
        result = redact_sensitive(data)
        assert "sk-test123456789012345" not in result["log_message"]
        assert "[REDACTED_API_KEY]" in result["log_message"]


class TestListRedaction:
    """Test redaction in list structures"""

    def test_list_of_strings(self):
        """Lists with sensitive strings should be redacted"""
        data = ["normal text", "secret: sk-abcdefghijklmnopqrst", "more text"]
        result = redact_sensitive(data)
        assert "sk-abcdefghijklmnopqrst" not in str(result)
        assert "[REDACTED_API_KEY]" in result[1]

    def test_list_of_dicts(self):
        """Lists of dicts should be recursively redacted"""
        data = [
            {"id": 1, "token": "secret123"},
            {"id": 2, "token": "secret456"}
        ]
        result = redact_sensitive(data)
        assert all(item["token"] == "[REDACTED]" for item in result)


class TestNonSensitiveData:
    """Test that non-sensitive data is NOT redacted"""

    def test_normal_text_unchanged(self):
        """Normal text without secrets should pass through"""
        text = "This is a normal log message with numbers 12345 and words."
        result = redact_sensitive(text)
        assert result == text

    def test_urls_unchanged(self):
        """URLs and domains should not be redacted"""
        text = "Fetching https://example.com/api/v1/users"
        result = redact_sensitive(text)
        assert result == text

    def test_short_strings_unchanged(self):
        """Short strings that don't match patterns should be unchanged"""
        text = "key: abc"
        result = redact_sensitive(text)
        assert result == text

    def test_numbers_unchanged(self):
        """Numeric values should not be redacted"""
        data = {"count": 42, "duration_ms": 1234.56}
        result = redact_sensitive(data)
        assert result == data


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_string(self):
        """Empty strings should be handled"""
        result = redact_sensitive("")
        assert result == ""

    def test_none_value(self):
        """None should be handled"""
        result = redact_sensitive(None)
        assert result is None

    def test_empty_dict(self):
        """Empty dicts should be handled"""
        result = redact_sensitive({})
        assert result == {}

    def test_empty_list(self):
        """Empty lists should be handled"""
        result = redact_sensitive([])
        assert result == []

    def test_mixed_types(self):
        """Mixed types should be handled"""
        data = {
            "string": "text",
            "number": 123,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }
        result = redact_sensitive(data)
        assert result["string"] == "text"
        assert result["number"] == 123
        assert result["bool"] is True
        assert result["null"] is None


class TestSafeByDefault:
    """Test that redaction never crashes (safe_by_default=True)"""

    def test_circular_reference_safe(self):
        """Circular references should not crash (returns error marker)"""
        data = {"key": "value"}
        data["self"] = data  # Circular reference
        result = redact_sensitive(data, safe_by_default=True)
        # Should either succeed or return error marker without crashing
        assert result is not None


# Run tests
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
