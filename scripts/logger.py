#!/usr/bin/env python3

"""
Structured Logger - AcademicAgent
JSON-based logging with levels, timestamps, and metadata
"""

import json
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


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
        """Format log entry as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.value,
            "logger": self.name,
            "message": message,
        }

        if metadata:
            log_entry["metadata"] = metadata

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
