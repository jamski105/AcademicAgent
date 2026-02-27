"""
Unit Tests for Error Formatter - Academic Agent v2.0

Tests for:
- ErrorFormatter class
- Error type handling
- Suggestions system
- Convenience functions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.ui.error_formatter import ErrorFormatter, print_error, print_warning


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def error_formatter():
    """Create ErrorFormatter instance"""
    return ErrorFormatter()


# ============================================
# ErrorFormatter Init Tests
# ============================================

class TestErrorFormatterInit:
    """Test ErrorFormatter initialization"""

    def test_init_creates_console(self, error_formatter):
        """Test that console is created"""
        assert error_formatter.console is not None

    def test_init_has_error_types(self, error_formatter):
        """Test that error types are defined"""
        assert "API_ERROR" in error_formatter.error_types
        assert "PDF_ERROR" in error_formatter.error_types
        assert "EXTRACTION_ERROR" in error_formatter.error_types

    def test_init_has_suggestions(self, error_formatter):
        """Test that suggestions are defined"""
        assert "API_ERROR" in error_formatter.suggestions
        assert len(error_formatter.suggestions["API_ERROR"]) > 0


# ============================================
# format_error Tests
# ============================================

class TestFormatError:
    """Test format_error method"""

    def test_format_error_basic(self, error_formatter):
        """Test basic error formatting"""
        # Should not raise error
        error_formatter.format_error("API_ERROR", "Connection failed")

    def test_format_error_with_phase(self, error_formatter):
        """Test error with phase"""
        error_formatter.format_error(
            "PDF_ERROR",
            "Download failed",
            phase="Phase 4"
        )

    def test_format_error_with_session_id(self, error_formatter):
        """Test error with session ID"""
        error_formatter.format_error(
            "API_ERROR",
            "Timeout",
            session_id="abc123"
        )

    def test_format_error_with_context(self, error_formatter):
        """Test error with context"""
        context = {"api": "CrossRef", "status": 503}
        error_formatter.format_error(
            "API_ERROR",
            "Service unavailable",
            context=context
        )

    def test_format_error_all_parameters(self, error_formatter):
        """Test error with all parameters"""
        error_formatter.format_error(
            error_type="NETWORK_ERROR",
            error_message="Connection timeout",
            phase="Phase 2: Search",
            session_id="xyz789",
            context={"timeout": "30s", "retries": 3}
        )

    def test_format_error_unknown_type(self, error_formatter):
        """Test error with unknown type"""
        # Should use default "Error" title
        error_formatter.format_error("UNKNOWN_TYPE", "Some error")


class TestFormatWarning:
    """Test format_warning method"""

    def test_format_warning_basic(self, error_formatter):
        """Test basic warning"""
        error_formatter.format_warning("This is a warning")

    def test_format_warning_with_context(self, error_formatter):
        """Test warning with context"""
        context = {"failed": 3, "total": 15}
        error_formatter.format_warning("Some PDFs failed", context=context)


class TestFormatCriticalError:
    """Test format_critical_error method"""

    def test_format_critical_basic(self, error_formatter):
        """Test basic critical error"""
        error_formatter.format_critical_error("Critical system error")

    def test_format_critical_with_traceback(self, error_formatter):
        """Test critical error with traceback"""
        traceback = "Traceback (most recent call last):\n  File..."
        error_formatter.format_critical_error("Fatal error", traceback=traceback)


class TestFormatValidationErrors:
    """Test format_validation_errors method"""

    def test_format_validation_errors_single(self, error_formatter):
        """Test single validation error"""
        errors = [
            {"field": "api_key", "message": "Missing API key"}
        ]
        error_formatter.format_validation_errors(errors)

    def test_format_validation_errors_multiple(self, error_formatter):
        """Test multiple validation errors"""
        errors = [
            {"field": "api_config.yaml", "message": "Missing anthropic_api_key"},
            {"field": "research_modes.yaml", "message": "Invalid mode"},
            {"field": "query", "message": "Query too short"}
        ]
        error_formatter.format_validation_errors(errors)

    def test_format_validation_errors_empty(self, error_formatter):
        """Test with empty errors list"""
        error_formatter.format_validation_errors([])


class TestPrintHelpMessage:
    """Test print_help_message method"""

    def test_help_api_keys(self, error_formatter):
        """Test API keys help"""
        error_formatter.print_help_message("api_keys")

    def test_help_pdf_download(self, error_formatter):
        """Test PDF download help"""
        error_formatter.print_help_message("pdf_download")

    def test_help_resume(self, error_formatter):
        """Test resume help"""
        error_formatter.print_help_message("resume")

    def test_help_unknown_topic(self, error_formatter):
        """Test unknown help topic"""
        error_formatter.print_help_message("unknown_topic")


# ============================================
# Convenience Functions Tests
# ============================================

class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_print_error_function(self):
        """Test print_error convenience function"""
        print_error("API_ERROR", "Connection failed")

    def test_print_error_with_parameters(self):
        """Test print_error with all parameters"""
        print_error(
            "PDF_ERROR",
            "Download failed",
            phase="Phase 4",
            session_id="test123"
        )

    def test_print_warning_function(self):
        """Test print_warning convenience function"""
        print_warning("Warning message")

    def test_print_warning_with_context(self):
        """Test print_warning with context"""
        print_warning("Some warning", context={"key": "value"})


# ============================================
# Suggestions System Tests
# ============================================

class TestSuggestions:
    """Test suggestions system"""

    def test_all_error_types_have_suggestions(self, error_formatter):
        """Test that all error types have suggestions"""
        for error_type in error_formatter.error_types.keys():
            assert error_type in error_formatter.suggestions
            assert len(error_formatter.suggestions[error_type]) > 0

    def test_api_error_suggestions(self, error_formatter):
        """Test API error suggestions"""
        suggestions = error_formatter.suggestions["API_ERROR"]
        assert any("internet" in s.lower() for s in suggestions)
        assert any("api key" in s.lower() for s in suggestions)

    def test_pdf_error_suggestions(self, error_formatter):
        """Test PDF error suggestions"""
        suggestions = error_formatter.suggestions["PDF_ERROR"]
        assert any("doi" in s.lower() for s in suggestions)

    def test_auth_error_suggestions(self, error_formatter):
        """Test auth error suggestions"""
        suggestions = error_formatter.suggestions["AUTH_ERROR"]
        assert any("api key" in s.lower() or "credential" in s.lower() for s in suggestions)


# ============================================
# Error Types Tests
# ============================================

class TestErrorTypes:
    """Test error types mapping"""

    def test_all_error_types_mapped(self, error_formatter):
        """Test that all error types are mapped"""
        required_types = [
            "API_ERROR", "PDF_ERROR", "EXTRACTION_ERROR",
            "VALIDATION_ERROR", "CONFIG_ERROR", "NETWORK_ERROR",
            "TIMEOUT_ERROR", "AUTH_ERROR"
        ]
        for error_type in required_types:
            assert error_type in error_formatter.error_types

    def test_error_type_friendly_names(self, error_formatter):
        """Test that error types have friendly names"""
        assert error_formatter.error_types["API_ERROR"] == "API Connection Error"
        assert error_formatter.error_types["PDF_ERROR"] == "PDF Download Error"


# ============================================
# Integration Tests
# ============================================

class TestErrorFormatterIntegration:
    """Test integration scenarios"""

    def test_workflow_error_scenario(self, error_formatter):
        """Test typical workflow error"""
        error_formatter.format_error(
            error_type="API_ERROR",
            error_message="CrossRef API returned 503",
            phase="Phase 2: Search",
            session_id="session_001",
            context={"api": "CrossRef", "status_code": 503, "retries": 3}
        )

    def test_pdf_error_scenario(self, error_formatter):
        """Test PDF download error"""
        error_formatter.format_error(
            error_type="PDF_ERROR",
            error_message="Unable to download PDF from publisher",
            phase="Phase 4: Fetch PDFs",
            session_id="session_002",
            context={"doi": "10.1234/example", "source": "publisher"}
        )

    def test_multiple_errors_sequence(self, error_formatter):
        """Test handling multiple errors in sequence"""
        error_formatter.format_error("API_ERROR", "First error")
        error_formatter.format_warning("Warning message")
        error_formatter.format_error("PDF_ERROR", "Second error")
        # Should handle multiple calls without issues
