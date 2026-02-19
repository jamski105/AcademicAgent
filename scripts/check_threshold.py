#!/usr/bin/env python3
"""
Metrics Threshold Checker

Checks if metric values exceed defined thresholds and logs appropriately.

Usage:
    from check_threshold import check_threshold, THRESHOLDS

    status = check_threshold("candidates_collected", 8, logger)
    if status == "critical":
        # Handle critical threshold
"""

# Threshold definitions
THRESHOLDS = {
    "candidates_collected": {
        "normal_min": 80,
        "normal_max": 150,
        "warning": 30,
        "critical": 10,
        "direction": "low"  # Alert if BELOW threshold
    },
    "phase_duration": {
        "normal_min": 1800,
        "normal_max": 3600,
        "warning": 5400,
        "critical": 7200,
        "direction": "high"  # Alert if ABOVE threshold
    },
    "candidates_after_screening": {
        "normal_min": 25,
        "normal_max": 40,
        "warning": 15,
        "critical": 8,
        "direction": "low"
    },
    "pdfs_downloaded": {
        "normal_min": 15,
        "normal_max": 18,
        "warning": 12,
        "critical": 8,
        "direction": "low"
    },
    "quotes_extracted": {
        "normal_min": 35,
        "normal_max": 50,
        "warning": 20,
        "critical": 10,
        "direction": "low"
    },
    "consecutive_empty_searches": {
        "normal_max": 1,
        "warning": 2,
        "critical": 3,
        "direction": "high"
    },
    "budget_percent_used": {
        "normal_max": 80,
        "warning": 80,
        "critical": 95,
        "direction": "high"
    },
    "iteration_duration": {
        "normal_min": 600,
        "normal_max": 1200,
        "warning": 1800,
        "critical": 2400,
        "direction": "high"
    }
}


def check_threshold(metric_name, value, logger=None):
    """
    Check if metric value exceeds thresholds.

    Args:
        metric_name: Name of metric (must be in THRESHOLDS)
        value: Current value
        logger: Optional logger instance (from scripts.logger)

    Returns:
        str: "ok" | "warning" | "critical"
    """
    if metric_name not in THRESHOLDS:
        # No thresholds defined for this metric
        return "ok"

    t = THRESHOLDS[metric_name]

    if t["direction"] == "low":
        # Alert if value is TOO LOW
        if value <= t["critical"]:
            if logger:
                logger.critical(f"{metric_name} CRITICAL threshold",
                    value=value,
                    threshold=t["critical"],
                    action="Immediate intervention required")
            return "critical"
        elif value <= t["warning"]:
            if logger:
                logger.warning(f"{metric_name} warning threshold",
                    value=value,
                    threshold=t["warning"],
                    action="Review and consider adjustments")
            return "warning"

    elif t["direction"] == "high":
        # Alert if value is TOO HIGH
        if value >= t["critical"]:
            if logger:
                logger.critical(f"{metric_name} CRITICAL threshold exceeded",
                    value=value,
                    threshold=t["critical"],
                    action="Stop and review")
            return "critical"
        elif value >= t["warning"]:
            if logger:
                logger.warning(f"{metric_name} warning threshold exceeded",
                    value=value,
                    threshold=t["warning"],
                    action="Monitor closely")
            return "warning"

    return "ok"


def get_threshold_info(metric_name):
    """
    Get threshold information for a metric.

    Args:
        metric_name: Name of metric

    Returns:
        dict: Threshold config or None if not found
    """
    return THRESHOLDS.get(metric_name)


def list_all_metrics():
    """
    List all metrics with defined thresholds.

    Returns:
        list: List of metric names
    """
    return list(THRESHOLDS.keys())


if __name__ == "__main__":
    # CLI usage for testing
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Check metric threshold")
    parser.add_argument("metric", help="Metric name")
    parser.add_argument("value", type=float, help="Metric value")
    parser.add_argument("--list", action="store_true", help="List all metrics")

    args = parser.parse_args()

    if args.list:
        print("Available metrics:")
        for metric in list_all_metrics():
            info = get_threshold_info(metric)
            print(f"  {metric}: {info['direction']} threshold")
        sys.exit(0)

    status = check_threshold(args.metric, args.value)

    if status == "critical":
        print(f"❌ CRITICAL: {args.metric} = {args.value}")
        sys.exit(2)
    elif status == "warning":
        print(f"⚠️  WARNING: {args.metric} = {args.value}")
        sys.exit(1)
    else:
        print(f"✅ OK: {args.metric} = {args.value}")
        sys.exit(0)
