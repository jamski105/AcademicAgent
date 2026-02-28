"""
Comprehensive Session Logger für Academic Agent v2.3+

Enhanced logging with structured activity tracking:
- Agent spawning
- API calls
- Phase durations
- DBIS activity
- PDF downloads

Usage:
    from src.utils.logger import SessionLogger

    logger = SessionLogger(run_dir=Path("runs/2026-02-27_14-30-00"))
    logger.start()

    logger.log_phase_start(1, "Context Setup")
    logger.log_agent_spawn("query_generator", "haiku")
    logger.log_api_call("crossref", "search", 15, 0.8)
    logger.log_phase_end(1, "Context Setup")

    logger.stop()
"""

import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json


class SessionLogger:
    """Enhanced session logger with structured activity tracking"""

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

        # Activity tracking (v2.3+)
        self.phase_start_times: Dict[int, float] = {}
        self.api_call_counts: Dict[str, int] = {}
        self.agent_spawns: list = []
        self.pdf_downloads: Dict[str, Any] = {"success": 0, "failed": 0}

    def start(self) -> None:
        """Start logging"""
        # Create logger
        self.logger = logging.getLogger(f"session_{self.run_dir.name}")
        self.logger.setLevel(logging.DEBUG)

        # Clear existing handlers
        self.logger.handlers.clear()

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

    # ============================================
    # Phase Tracking (v2.3+)
    # ============================================

    def log_phase_start(self, phase_number: int, phase_name: str) -> None:
        """Log phase start"""
        self.phase_start_times[phase_number] = time.time()
        self.log(f"{'='*60}")
        self.log(f"Phase {phase_number}/6: {phase_name} - Started")
        self.log(f"{'='*60}")

    def log_phase_end(self, phase_number: int, phase_name: str, success: bool = True) -> None:
        """Log phase end with duration"""
        start_time = self.phase_start_times.get(phase_number)
        if start_time:
            duration = time.time() - start_time
            status = "✅ Completed" if success else "❌ Failed"
            self.log(f"{status}: Phase {phase_number}/6: {phase_name} ({duration:.1f}s)")

    # ============================================
    # Agent Tracking (v2.3+)
    # ============================================

    def log_agent_spawn(self, agent_type: str, model: str, description: str = "") -> None:
        """Log agent spawning"""
        self.agent_spawns.append({
            "agent_type": agent_type,
            "model": model,
            "timestamp": datetime.now().isoformat()
        })
        self.log(f"🤖 Spawning {agent_type} agent ({model.upper()})")
        if description:
            self.log(f"   {description}", level="DEBUG")

    def log_agent_complete(self, agent_type: str, duration: float, success: bool = True) -> None:
        """Log agent completion"""
        status = "✅" if success else "❌"
        self.log(f"{status} {agent_type} completed ({duration:.1f}s)")

    # ============================================
    # API Call Tracking (v2.3+)
    # ============================================

    def log_api_call(self, api_name: str, operation: str, results: int, duration: float) -> None:
        """Log API call"""
        if api_name not in self.api_call_counts:
            self.api_call_counts[api_name] = 0
        self.api_call_counts[api_name] += 1

        self.log(f"📡 {api_name.upper()}: {operation} → {results} results ({duration:.1f}s)")

    # ============================================
    # DBIS Tracking (v2.3+)
    # ============================================

    def log_dbis_discovery(self, discipline: str, databases_found: int, databases_selected: list) -> None:
        """Log DBIS discovery"""
        self.log(f"🗄️  DBIS Discovery ({discipline})")
        self.log(f"   Found: {databases_found} databases")
        self.log(f"   Selected: {', '.join(databases_selected[:5])}")

    def log_dbis_search(self, database: str, results: int, duration: float) -> None:
        """Log DBIS search"""
        self.log(f"🔍 {database}: {results} results ({duration:.1f}s)")

    # ============================================
    # PDF Tracking (v2.3+)
    # ============================================

    def log_pdf_download(self, doi: str, source: str, success: bool, size_mb: float = 0) -> None:
        """Log PDF download"""
        if success:
            self.pdf_downloads["success"] += 1
            self.log(f"📥 PDF: {doi} ({source}, {size_mb:.1f} MB)")
        else:
            self.pdf_downloads["failed"] += 1
            self.log(f"📥 PDF unavailable: {doi} ({source})", level="DEBUG")

    # ============================================
    # Summary (v2.3+)
    # ============================================

    def log_summary(self, stats: Dict[str, Any]) -> None:
        """Log session summary"""
        self.log(f"\n{'='*60}")
        self.log("📊 RESEARCH SESSION SUMMARY")
        self.log(f"{'='*60}")

        for key, value in stats.items():
            self.log(f"   {key.replace('_', ' ').title()}: {value}")

        if self.api_call_counts:
            self.log(f"\n   API Calls:")
            for api, count in self.api_call_counts.items():
                self.log(f"     - {api.upper()}: {count}")

        if self.agent_spawns:
            self.log(f"\n   Agents Spawned: {len(self.agent_spawns)}")

        self.log(f"{'='*60}\n")

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
