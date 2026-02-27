"""
Run Directory Manager für Academic Agent v2.1

Verwaltet timestamped run directories für Research Sessions.
Alle Outputs (PDFs, Results, Logs) werden in runs/{timestamp}/ gespeichert.

Features:
- Timestamp-basierte Ordner-Erstellung
- Automatische Subdirectories (pdfs/, temp/)
- Get latest run
- CLI interface

Usage:
    from src.state.run_manager import RunManager

    manager = RunManager()
    run_dir = manager.create_run_directory()
    # Output: runs/2026-02-27_14-30-00/

    # CLI:
    python -m src.state.run_manager --create
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class RunManager:
    """Manages run directories for research sessions"""

    def __init__(self, base_dir: Path = Path("runs")):
        """
        Initialize Run Manager

        Args:
            base_dir: Base directory for all runs (default: "runs")
        """
        self.base_dir = base_dir
        self.base_dir.mkdir(exist_ok=True)
        logger.info(f"RunManager initialized: {self.base_dir}")

    def create_run_directory(self, timestamp: Optional[str] = None) -> Path:
        """
        Create timestamped run directory with subdirectories

        Args:
            timestamp: Optional custom timestamp (format: YYYY-MM-DD_HH-MM-SS)
                      If None, uses current datetime

        Returns:
            Path to created run directory

        Example:
            run_dir = manager.create_run_directory()
            # Returns: runs/2026-02-27_14-30-00/

            # With custom timestamp:
            run_dir = manager.create_run_directory("2026-02-27_12-00-00")
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        run_dir = self.base_dir / timestamp

        # Create main directory
        run_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (run_dir / "pdfs").mkdir(exist_ok=True)
        (run_dir / "temp").mkdir(exist_ok=True)

        logger.info(f"Created run directory: {run_dir}")

        return run_dir

    def get_latest_run(self) -> Optional[Path]:
        """
        Get path to latest run directory

        Returns:
            Path to latest run, or None if no runs exist

        Example:
            latest = manager.get_latest_run()
            if latest:
                print(f"Latest run: {latest}")
        """
        # Find all directories matching timestamp pattern (YYYY-MM-DD_HH-MM-SS)
        runs = sorted(
            [d for d in self.base_dir.glob("20*-*-*_*-*-*") if d.is_dir()],
            reverse=True
        )

        if runs:
            logger.info(f"Latest run: {runs[0]}")
            return runs[0]

        logger.warning("No runs found")
        return None

    def list_runs(self, limit: Optional[int] = None) -> List[Path]:
        """
        List all run directories (sorted by timestamp, newest first)

        Args:
            limit: Optional limit on number of runs to return

        Returns:
            List of run directory paths

        Example:
            runs = manager.list_runs(limit=10)
            for run in runs:
                print(run)
        """
        runs = sorted(
            [d for d in self.base_dir.glob("20*-*-*_*-*-*") if d.is_dir()],
            reverse=True
        )

        if limit:
            runs = runs[:limit]

        logger.info(f"Found {len(runs)} runs")
        return runs

    def run_exists(self, timestamp: str) -> bool:
        """
        Check if run directory exists

        Args:
            timestamp: Timestamp string (format: YYYY-MM-DD_HH-MM-SS)

        Returns:
            True if run exists, False otherwise
        """
        run_dir = self.base_dir / timestamp
        return run_dir.exists() and run_dir.is_dir()

    def get_run_directory(self, timestamp: str) -> Path:
        """
        Get path to specific run directory

        Args:
            timestamp: Timestamp string (format: YYYY-MM-DD_HH-MM-SS)

        Returns:
            Path to run directory

        Raises:
            FileNotFoundError: If run doesn't exist
        """
        run_dir = self.base_dir / timestamp

        if not run_dir.exists():
            raise FileNotFoundError(f"Run not found: {timestamp}")

        return run_dir


# ============================================
# CLI Interface
# ============================================

def main():
    """
    CLI Interface for Run Manager

    Usage:
        # Create new run directory
        python -m src.state.run_manager --create

        # Get latest run
        python -m src.state.run_manager --latest

        # List all runs
        python -m src.state.run_manager --list

        # List last 10 runs
        python -m src.state.run_manager --list --limit 10

        # Check if run exists
        python -m src.state.run_manager --exists 2026-02-27_14-30-00
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run Directory Manager")
    parser.add_argument('--create', action='store_true', help='Create new run directory')
    parser.add_argument('--latest', action='store_true', help='Get latest run directory')
    parser.add_argument('--list', action='store_true', help='List all run directories')
    parser.add_argument('--limit', type=int, help='Limit number of runs to list')
    parser.add_argument('--exists', metavar='TIMESTAMP', help='Check if run exists')
    parser.add_argument('--base-dir', default='runs', help='Base directory (default: runs)')

    args = parser.parse_args()

    # Initialize manager
    manager = RunManager(base_dir=Path(args.base_dir))

    try:
        if args.create:
            # Create new run
            run_dir = manager.create_run_directory()
            print(str(run_dir))
            sys.exit(0)

        elif args.latest:
            # Get latest run
            latest = manager.get_latest_run()
            if latest:
                print(str(latest))
                sys.exit(0)
            else:
                print("No runs found", file=sys.stderr)
                sys.exit(1)

        elif args.list:
            # List runs
            runs = manager.list_runs(limit=args.limit)
            for run in runs:
                print(str(run))
            sys.exit(0)

        elif args.exists:
            # Check if run exists
            exists = manager.run_exists(args.exists)
            if exists:
                print(f"Run exists: {args.exists}")
                sys.exit(0)
            else:
                print(f"Run not found: {args.exists}", file=sys.stderr)
                sys.exit(1)

        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
