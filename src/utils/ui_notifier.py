"""
Web UI Notifier for Academic Agent v2.3+

Sends live progress updates to Web UI via HTTP API.

Usage:
    from src.utils.ui_notifier import UINotifier

    ui = UINotifier(session_id="abc123", enabled=True)
    ui.phase_start(1, "Context Setup")
    ui.papers_found(47)
    ui.phase_complete(1, "Context Setup")
"""

import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class UINotifier:
    """Sends progress updates to Web UI"""

    def __init__(self, session_id: str, base_url: str = "http://localhost:8000", enabled: bool = True):
        """
        Initialize UI Notifier

        Args:
            session_id: Current research session ID
            base_url: Web UI server URL (default: http://localhost:8000)
            enabled: Whether to send updates (disable for CLI-only mode)
        """
        self.session_id = session_id
        self.base_url = base_url
        self.enabled = enabled
        self.update_url = f"{base_url}/api/update/{session_id}"

    def register_session(self, query: str = "Research", mode: str = "standard") -> bool:
        """
        Register this session with the Web UI server.
        Call once at the start of Phase 1.

        Args:
            query: Research query
            mode: Research mode (quick/standard/deep)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return True

        try:
            response = requests.post(
                f"{self.base_url}/api/start-research",
                json={"session_id": self.session_id, "query": query, "mode": mode},
                timeout=2
            )
            response.raise_for_status()
            logger.info(f"Session {self.session_id} registered with Web UI")
            return True
        except requests.RequestException as e:
            logger.debug(f"Session registration failed (server may not be running): {e}")
            return False

    def _send(self, data: Dict[str, Any]) -> bool:
        """
        Send update to Web UI

        Args:
            data: Update data dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return True

        try:
            response = requests.post(
                self.update_url,
                json=data,
                timeout=2
            )
            response.raise_for_status()
            logger.debug(f"UI update sent: {data}")
            return True
        except requests.RequestException as e:
            logger.debug(f"UI update failed (server may not be running): {e}")
            return False
        except Exception as e:
            logger.error(f"UI update error: {e}")
            return False

    # ============================================
    # Phase Updates
    # ============================================

    def phase_start(self, phase_number: int, phase_name: str) -> bool:
        """Notify phase start"""
        return self._send({
            "current_phase": phase_number,
            "status": "running",
            "log_message": f"Phase {phase_number}/7: {phase_name} - Started"
        })

    def phase_complete(self, phase_number: int, phase_name: str) -> bool:
        """Notify phase completion"""
        return self._send({
            "current_phase": phase_number,
            "log_message": f"✅ Phase {phase_number}/7: {phase_name} - Complete"
        })

    def phase_error(self, phase_number: int, phase_name: str, error: str) -> bool:
        """Notify phase error"""
        return self._send({
            "current_phase": phase_number,
            "status": "error",
            "log_message": f"❌ Phase {phase_number}/7: {phase_name} - Error: {error}"
        })

    # ============================================
    # Progress Updates
    # ============================================

    def progress(self, percent: int) -> bool:
        """Update progress bar (0-100)"""
        return self._send({
            "progress": max(0, min(100, percent))
        })

    def papers_found(self, count: int) -> bool:
        """Update papers found counter"""
        return self._send({
            "papers_found": count,
            "log_message": f"📄 Found {count} papers"
        })

    def pdfs_downloaded(self, count: int) -> bool:
        """Update PDFs downloaded counter"""
        return self._send({
            "pdfs_downloaded": count,
            "log_message": f"📥 Downloaded {count} PDFs"
        })

    # ============================================
    # Status Updates
    # ============================================

    def status(self, status: str, message: str = "") -> bool:
        """
        Update session status

        Args:
            status: One of: running, completed, error, paused
            message: Optional status message
        """
        data = {"status": status}
        if message:
            data["log_message"] = message
        return self._send(data)

    def log(self, message: str) -> bool:
        """Send log message to UI"""
        return self._send({
            "log_message": message
        })

    def error(self, message: str, phase: Optional[int] = None) -> bool:
        """Send error notification to UI"""
        data: Dict[str, Any] = {
            "status": "error",
            "log_message": f"❌ ERROR: {message}"
        }
        if phase is not None:
            data["current_phase"] = phase
        return self._send(data)

    # ============================================
    # Convenience Methods
    # ============================================

    def agent_spawn(self, agent_type: str, model: str) -> bool:
        """Notify agent spawning"""
        return self.log(f"🤖 Spawning {agent_type} agent ({model.upper()})")

    def agent_complete(self, agent_type: str, duration: float) -> bool:
        """Notify agent completion"""
        return self.log(f"✅ {agent_type} completed ({duration:.1f}s)")

    def api_call(self, api_name: str, results: int) -> bool:
        """Notify API call result"""
        return self.log(f"📡 {api_name.upper()}: {results} results")

    def complete(self, papers: int, pdfs: int, quotes: int) -> bool:
        """Notify research completion"""
        self.status("completed", f"✅ Research Complete! {papers} papers, {pdfs} PDFs, {quotes} quotes")
        return self.progress(100)


# Convenience function for CLI usage
def create_notifier(session_id: str, enabled: bool = True) -> UINotifier:
    """
    Create UI notifier instance

    Args:
        session_id: Session ID
        enabled: Enable/disable UI updates (auto-detect if Web UI is running)

    Returns:
        UINotifier instance
    """
    # Auto-detect if Web UI is running
    if enabled:
        try:
            response = requests.get("http://localhost:8000/health", timeout=1)
            if response.status_code == 200:
                logger.info("✅ Web UI detected - Live updates enabled")
                return UINotifier(session_id, enabled=True)
        except:
            pass

        logger.info("⚠️  Web UI not detected - Updates disabled")
        return UINotifier(session_id, enabled=False)

    return UINotifier(session_id, enabled=False)


# CLI for testing
def main():
    import argparse
    import time
    import sys

    parser = argparse.ArgumentParser(description="UI Notifier CLI")
    parser.add_argument('--session-id', required=True, help='Session ID')
    parser.add_argument('--test', action='store_true', help='Run test sequence')
    parser.add_argument('--message', help='Send log message')
    parser.add_argument('--phase', type=int, help='Phase number')
    parser.add_argument('--papers', type=int, help='Papers found')
    parser.add_argument('--pdfs', type=int, help='PDFs downloaded')

    args = parser.parse_args()

    notifier = create_notifier(args.session_id)

    if args.test:
        print("🧪 Running UI Notifier Test Sequence...\n")

        # Test Phase Updates
        print("Phase 1: Context Setup")
        notifier.phase_start(1, "Context Setup")
        notifier.progress(10)
        time.sleep(1)
        notifier.phase_complete(1, "Context Setup")

        print("Phase 2: Query Generation")
        notifier.phase_start(2, "Query Generation")
        notifier.progress(25)
        notifier.agent_spawn("query_generator", "haiku")
        time.sleep(1)
        notifier.agent_complete("query_generator", 2.3)
        notifier.phase_complete(2, "Query Generation")

        print("Phase 3: API Search")
        notifier.phase_start(3, "API Search")
        notifier.progress(40)
        time.sleep(0.5)
        notifier.api_call("crossref", 20)
        notifier.papers_found(20)
        time.sleep(0.5)
        notifier.api_call("openalex", 15)
        notifier.papers_found(35)
        time.sleep(0.5)
        notifier.api_call("semantic_scholar", 12)
        notifier.papers_found(47)
        notifier.phase_complete(3, "API Search")

        print("Phase 4: Ranking")
        notifier.phase_start(4, "Ranking")
        notifier.progress(60)
        notifier.agent_spawn("llm_relevance_scorer", "haiku")
        time.sleep(1)
        notifier.agent_complete("llm_relevance_scorer", 3.8)
        notifier.phase_complete(4, "Ranking")

        print("Phase 5: PDF Download")
        notifier.phase_start(5, "PDF Download")
        notifier.progress(75)
        for i in range(1, 23):
            time.sleep(0.1)
            notifier.pdfs_downloaded(i)
        notifier.phase_complete(5, "PDF Download")

        print("Phase 6: Quote Extraction")
        notifier.phase_start(6, "Quote Extraction")
        notifier.progress(90)
        notifier.agent_spawn("quote_extractor", "haiku")
        time.sleep(1)
        notifier.agent_complete("quote_extractor", 5.2)
        notifier.phase_complete(6, "Quote Extraction")

        print("Phase 7: Export")
        notifier.phase_start(7, "Export")
        notifier.progress(95)
        time.sleep(0.5)
        notifier.phase_complete(7, "Export")

        print("Complete!")
        notifier.complete(papers=47, pdfs=22, quotes=45)

        print("\n✅ Test sequence complete!")
        sys.exit(0)

    # Single updates
    if args.message:
        notifier.log(args.message)
        print(f"✅ Sent log: {args.message}")

    if args.phase:
        notifier.phase_start(args.phase, f"Phase {args.phase}")
        print(f"✅ Sent phase update: {args.phase}")

    if args.papers:
        notifier.papers_found(args.papers)
        print(f"✅ Sent papers count: {args.papers}")

    if args.pdfs:
        notifier.pdfs_downloaded(args.pdfs)
        print(f"✅ Sent PDFs count: {args.pdfs}")


if __name__ == "__main__":
    main()
