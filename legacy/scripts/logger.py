#!/usr/bin/env python3

"""
Structured Logger - AcademicAgent
JSON-based logging with levels, timestamps, and metadata
Includes PII/secret redaction for secure logging
"""

import json
import re
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Union


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ============================================================================
# PII/SECRET REDACTION (SECURITY: Prevent credential/PII leaks in logs)
# ============================================================================

# Patterns for sensitive data detection
_SENSITIVE_PATTERNS = [
    # API Keys and tokens (common prefixes)
    (re.compile(r'\b(sk-[a-zA-Z0-9]{15,})\b'), '[REDACTED_API_KEY]'),
    (re.compile(r'\b(AKIA[0-9A-Z]{16})\b'), '[REDACTED_AWS_KEY]'),
    (re.compile(r'\b(AIza[0-9A-Za-z_-]{35})\b'), '[REDACTED_GOOGLE_KEY]'),
    (re.compile(r'\bBearer\s+[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'), 'Bearer [REDACTED_JWT]'),

    # Session tokens and cookies
    (re.compile(r'\b(session_token|sessionid|auth_token)["\':\s=]+([a-zA-Z0-9_-]{20,})', re.IGNORECASE), r'\1=[REDACTED_TOKEN]'),
    (re.compile(r'\b(cookie)["\':\s=]+([^;\s]{20,})', re.IGNORECASE), r'\1=[REDACTED_COOKIE]'),

    # Private key blocks
    (re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----[\s\S]+?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----', re.IGNORECASE), '[REDACTED_PRIVATE_KEY]'),

    # Email addresses (partial masking: keep domain for debugging)
    (re.compile(r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'), lambda m: f'{m.group(1)[:2]}***@{m.group(2)}'),
]


def redact_sensitive(data: Union[str, Dict, Any], safe_by_default: bool = True) -> Union[str, Dict, Any]:
    """
    Redact sensitive data (API keys, tokens, PII) from logs.

    Args:
        data: String, dict, or any JSON-serializable data
        safe_by_default: If True, never raises exceptions (returns original on error)

    Returns:
        Data with sensitive fields redacted

    Examples:
        >>> redact_sensitive("API key: sk-1234567890abcdefghij")
        "API key: [REDACTED_API_KEY]"

        >>> redact_sensitive({"email": "user@example.com", "key": "sk-secret"})
        {"email": "us***@example.com", "key": "[REDACTED_API_KEY]"}
    """
    try:
        if isinstance(data, str):
            return _redact_string(data)
        elif isinstance(data, dict):
            return _redact_dict(data)
        elif isinstance(data, list):
            return [redact_sensitive(item, safe_by_default) for item in data]
        else:
            # Primitive types (int, float, bool, None) pass through
            return data
    except Exception as e:
        if safe_by_default:
            # Never crash logging due to redaction errors
            return f"[REDACTION_ERROR: {type(data).__name__}]"
        raise


def _redact_string(text: str) -> str:
    """Apply regex-based redaction to string."""
    if not text:
        return text

    result = text
    for pattern, replacement in _SENSITIVE_PATTERNS:
        if callable(replacement):
            result = pattern.sub(replacement, result)
        else:
            result = pattern.sub(replacement, result)

    return result


def _redact_dict(data: dict) -> dict:
    """Recursively redact sensitive fields in dict."""
    redacted = {}

    # Known sensitive field names (case-insensitive)
    sensitive_keys = {
        'password', 'passwd', 'pwd', 'secret', 'api_key', 'apikey', 'access_token',
        'auth_token', 'session_token', 'token', 'private_key', 'encryption_key', 'cookie'
    }

    for key, value in data.items():
        key_lower = str(key).lower()

        # Redact by field name
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            redacted[key] = '[REDACTED]'
        # Recursively redact nested structures
        elif isinstance(value, dict):
            redacted[key] = _redact_dict(value)
        elif isinstance(value, list):
            redacted[key] = [redact_sensitive(item) for item in value]
        elif isinstance(value, str):
            redacted[key] = _redact_string(value)
        else:
            redacted[key] = value

    return redacted


# ============================================================================


class StructuredLogger:
    """Structured logger with JSON output"""

    def __init__(
        self,
        name: str,
        log_file: Optional[Path] = None,
        console: bool = True,
        level: LogLevel = LogLevel.INFO,
    ):
        self.name = name
        self.log_file = log_file
        self.console = console
        self.level = level

        # Create log file if specified
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if level should be logged"""
        levels_order = [
            LogLevel.DEBUG,
            LogLevel.INFO,
            LogLevel.WARNING,
            LogLevel.ERROR,
            LogLevel.CRITICAL,
        ]
        return levels_order.index(level) >= levels_order.index(self.level)

    def _format_log(
        self,
        level: LogLevel,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Format log entry as JSON with PII/secret redaction"""
        # Redact message and metadata BEFORE formatting
        safe_message = redact_sensitive(message)
        safe_metadata = redact_sensitive(metadata) if metadata else None

        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.value,
            "logger": self.name,
            "message": safe_message,
        }

        if safe_metadata:
            log_entry["metadata"] = safe_metadata

        return log_entry

    def _write_log(self, log_entry: Dict[str, Any]):
        """Write log to file and/or console"""
        log_json = json.dumps(log_entry)

        # Console output (pretty)
        if self.console:
            level = log_entry["level"]
            timestamp = log_entry["timestamp"].split("T")[1].split(".")[0]

            # Color codes
            colors = {
                "DEBUG": "\033[0;36m",  # Cyan
                "INFO": "\033[0;32m",  # Green
                "WARNING": "\033[1;33m",  # Yellow
                "ERROR": "\033[0;31m",  # Red
                "CRITICAL": "\033[1;31m",  # Bold Red
            }
            reset = "\033[0m"

            color = colors.get(level, "")
            console_output = (
                f"{color}[{timestamp}] {level:8s}{reset} | "
                f"{log_entry['message']}"
            )

            if "metadata" in log_entry and log_entry["metadata"]:
                console_output += f" | {json.dumps(log_entry['metadata'])}"

            print(console_output, file=sys.stderr)

        # File output (JSON)
        if self.log_file:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_json + "\n")

    def debug(self, message: str, **metadata):
        """Log debug message"""
        if self._should_log(LogLevel.DEBUG):
            log_entry = self._format_log(LogLevel.DEBUG, message, metadata)
            self._write_log(log_entry)

    def info(self, message: str, **metadata):
        """Log info message"""
        if self._should_log(LogLevel.INFO):
            log_entry = self._format_log(LogLevel.INFO, message, metadata)
            self._write_log(log_entry)

    def warning(self, message: str, **metadata):
        """Log warning message"""
        if self._should_log(LogLevel.WARNING):
            log_entry = self._format_log(LogLevel.WARNING, message, metadata)
            self._write_log(log_entry)

    def error(self, message: str, **metadata):
        """Log error message"""
        if self._should_log(LogLevel.ERROR):
            log_entry = self._format_log(LogLevel.ERROR, message, metadata)
            self._write_log(log_entry)

    def critical(self, message: str, **metadata):
        """Log critical message"""
        if self._should_log(LogLevel.CRITICAL):
            log_entry = self._format_log(
                LogLevel.CRITICAL, message, metadata
            )
            self._write_log(log_entry)

    def phase_start(self, phase: int, phase_name: str):
        """Log phase start"""
        self.info(
            f"Phase {phase} started: {phase_name}",
            phase=phase,
            phase_name=phase_name,
            event="phase_start",
        )

    def phase_end(self, phase: int, phase_name: str, duration_seconds: float):
        """Log phase end"""
        self.info(
            f"Phase {phase} completed: {phase_name}",
            phase=phase,
            phase_name=phase_name,
            duration_seconds=duration_seconds,
            event="phase_end",
        )

    def phase_error(self, phase: int, phase_name: str, error: str):
        """Log phase error"""
        self.error(
            f"Phase {phase} failed: {phase_name}",
            phase=phase,
            phase_name=phase_name,
            error=error,
            event="phase_error",
        )

    def metric(self, metric_name: str, value: Any, unit: Optional[str] = None):
        """Log metric"""
        metadata = {"metric": metric_name, "value": value}
        if unit:
            metadata["unit"] = unit

        self.info(f"Metric: {metric_name} = {value}", **metadata)


# Factory function
def get_logger(
    name: str,
    project_dir: Optional[Path] = None,
    console: bool = True,
    level: str = "INFO",
) -> StructuredLogger:
    """
    Get logger instance

    Args:
        name: Logger name (e.g., "orchestrator", "browser_agent")
        project_dir: Project directory (logs will be in project_dir/logs/)
        console: Enable console output
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_file = None
    if project_dir:
        log_dir = Path(project_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{name}_{timestamp}.jsonl"

    log_level = LogLevel[level.upper()]

    return StructuredLogger(
        name=name, log_file=log_file, console=console, level=log_level
    )


# Example usage
if __name__ == "__main__":
    # Demo
    logger = get_logger("demo", console=True, level="DEBUG")

    logger.debug("Debug message", extra_field="value")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message", error_code=500)
    logger.critical("Critical message")

    logger.phase_start(0, "DBIS Navigation")
    logger.metric("databases_found", 8, unit="count")
    logger.phase_end(0, "DBIS Navigation", duration_seconds=123.45)

    print("\n✅ Logger demo complete")
