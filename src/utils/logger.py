"""
Session Logger für Academic Agent v2.1

Loggt Workflow-Execution zu runs/{timestamp}/session_log.txt

Usage:
    from src.utils.logger import SessionLogger

    logger = SessionLogger(run_dir=Path("runs/2026-02-27_14-30-00"))
    logger.start()
    logger.log("Phase 1: Context Setup")
    logger.log("Found 25 papers", level="INFO")
    logger.stop()
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


class SessionLogger:
    """Logs session execution to run directory"""

    def __init__(self, run_dir: Path, log_file: str = "session_log.txt"):
        """
        Initialize Session Logger

        Args:
            run_dir: Run directory (e.g. runs/2026-02-27_14-30-00/)
            log_file: Log filename (default: session_log.txt)
        """
        self.run_dir = run_dir
        self.log_path = run_dir / log_file
        self.logger = None

    def start(self) -> None:
        """Start logging"""
        # Create logger
        self.logger = logging.getLogger(f"session_{self.run_dir.name}")
        self.logger.setLevel(logging.DEBUG)

        # File handler
        file_handler = logging.FileHandler(self.log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Formatter with timestamp
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

        # Log session start
        self.logger.info("=" * 60)
        self.logger.info(f"Session started: {self.run_dir.name}")
        self.logger.info("=" * 60)

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log message

        Args:
            message: Log message
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        if not self.logger:
            raise RuntimeError("Logger not started. Call start() first.")

        level_upper = level.upper()
        if level_upper == "DEBUG":
            self.logger.debug(message)
        elif level_upper == "INFO":
            self.logger.info(message)
        elif level_upper == "WARNING":
            self.logger.warning(message)
        elif level_upper == "ERROR":
            self.logger.error(message)
        else:
            self.logger.info(message)

    def stop(self) -> None:
        """Stop logging"""
        if self.logger:
            self.logger.info("=" * 60)
            self.logger.info(f"Session ended")
            self.logger.info("=" * 60)

            # Close handlers
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)


# CLI
def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Session Logger")
    parser.add_argument('--run-dir', help='Run directory')
    parser.add_argument('--start', action='store_true', help='Start logging')
    parser.add_argument('--stop', action='store_true', help='Stop logging')
    parser.add_argument('--message', help='Log message')
    parser.add_argument('--level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    parser.add_argument('--test', action='store_true', help='Run test')

    args = parser.parse_args()

    if args.test:
        from tempfile import mkdtemp
        test_dir = Path(mkdtemp())

        logger = SessionLogger(run_dir=test_dir)
        logger.start()
        logger.log("Phase 1: Context Setup")
        logger.log("Phase 2: Query Generation")
        logger.log("Found 25 papers", level="INFO")
        logger.log("Downloaded 22 PDFs", level="INFO")
        logger.stop()

        print(f"✅ Session Logger test complete!")
        print(f"\n📄 Log Preview:")
        print((test_dir / "session_log.txt").read_text())

        # Cleanup
        import shutil
        shutil.rmtree(test_dir)

        sys.exit(0)

    if not args.run_dir:
        parser.error("--run-dir required (unless --test)")

    run_dir = Path(args.run_dir)
    logger = SessionLogger(run_dir=run_dir)

    if args.start:
        logger.start()
        print(f"✅ Logging started: {logger.log_path}")
    elif args.stop:
        logger.stop()
        print(f"✅ Logging stopped: {logger.log_path}")
    elif args.message:
        logger.log(args.message, level=args.level)
        print(f"✅ Logged: {args.message}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
