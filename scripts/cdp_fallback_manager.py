#!/usr/bin/env python3
"""
CDP Fallback Manager - Auto-Recovery für Chrome CDP Failures

Zweck:
    - Prüft CDP-Verfügbarkeit (localhost:9222)
    - Startet Chrome automatisch falls nicht verfügbar
    - Fallback zu Playwright Headless bei kritischen Failures
    - Unified Interface für Browser-Operations

Verwendung:
    python3 scripts/cdp_fallback_manager.py check
    python3 scripts/cdp_fallback_manager.py start --fallback

Features:
    1. Health-Check (CDP-Port 9222)
    2. Auto-Start Chrome Debug Mode
    3. Playwright Headless Fallback
    4. Retry-Strategie mit Exponential Backoff
"""

import sys
import subprocess
import json
import time
import socket
import os
from pathlib import Path
from typing import Dict, Any, Optional


class CDPFallbackManager:
    """Managed Chrome CDP mit automatischem Fallback"""

    def __init__(self, cdp_port: int = 9222, max_retries: int = 3):
        self.cdp_port = cdp_port
        self.max_retries = max_retries
        self.mode = None  # "cdp" oder "playwright"

    def check_cdp_available(self) -> bool:
        """
        Prüft ob CDP verfügbar ist auf localhost:9222

        Returns:
            True wenn CDP antwortet, sonst False
        """
        try:
            # Versuche Socket-Connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', self.cdp_port))
            sock.close()

            if result == 0:
                # Port ist offen, prüfe ob es wirklich CDP ist
                import urllib.request
                try:
                    response = urllib.request.urlopen(f'http://localhost:{self.cdp_port}/json/version', timeout=2)
                    data = json.loads(response.read())
                    # Sollte Browser/Protocol enthalten
                    return 'Browser' in data and 'Protocol-Version' in data
                except:
                    return False
            return False

        except Exception as e:
            print(f"⚠️ CDP-Check fehlgeschlagen: {e}", file=sys.stderr)
            return False

    def start_chrome_debug(self) -> bool:
        """
        Startet Chrome im Debug-Mode

        Returns:
            True wenn erfolgreich gestartet, sonst False
        """
        try:
            # Prüfe Betriebssystem
            import platform
            os_type = platform.system()

            if os_type == "Darwin":  # macOS
                chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            elif os_type == "Linux":
                # Versuche verschiedene Chrome-Pfade
                possible_paths = [
                    "/usr/bin/google-chrome",
                    "/usr/bin/chromium",
                    "/usr/bin/chromium-browser"
                ]
                chrome_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        chrome_path = path
                        break

                if not chrome_path:
                    print("❌ Chrome/Chromium nicht gefunden", file=sys.stderr)
                    return False
            else:
                print(f"❌ Nicht unterstütztes OS: {os_type}", file=sys.stderr)
                return False

            # Starte Chrome mit Remote-Debugging
            print(f"⚙️ Starte Chrome Debug-Mode auf Port {self.cdp_port}...", file=sys.stderr)

            cmd = [
                chrome_path,
                f"--remote-debugging-port={self.cdp_port}",
                "--no-first-run",
                "--no-default-browser-check",
                f"--user-data-dir={os.path.expanduser('~/.claude-academic-agent-chrome')}"
            ]

            # Starte im Hintergrund
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # Warte auf CDP-Verfügbarkeit (max 10 Sekunden)
            for i in range(10):
                time.sleep(1)
                if self.check_cdp_available():
                    print("✅ Chrome CDP verfügbar", file=sys.stderr)
                    return True

            print("❌ Chrome gestartet aber CDP nicht erreichbar", file=sys.stderr)
            return False

        except Exception as e:
            print(f"❌ Chrome-Start fehlgeschlagen: {e}", file=sys.stderr)
            return False

    def start_playwright_fallback(self) -> bool:
        """
        Startet Playwright Chromium Headless als Fallback

        Returns:
            True wenn erfolgreich, sonst False
        """
        try:
            print("⚙️ Starte Playwright Headless Fallback...", file=sys.stderr)

            # Prüfe ob Playwright installiert ist
            try:
                import playwright
            except ImportError:
                print("❌ Playwright nicht installiert. Führe aus: npm install playwright", file=sys.stderr)
                return False

            # Erstelle Playwright-Launcher-Script
            launcher_script = Path(__file__).parent / "playwright_launcher.js"

            if not launcher_script.exists():
                print(f"❌ Playwright-Launcher nicht gefunden: {launcher_script}", file=sys.stderr)
                return False

            # Starte Playwright Chromium
            result = subprocess.run(
                ["node", str(launcher_script), "--port", str(self.cdp_port)],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                print("✅ Playwright Headless gestartet", file=sys.stderr)
                self.mode = "playwright"
                return True
            else:
                print(f"❌ Playwright-Start fehlgeschlagen: {result.stderr}", file=sys.stderr)
                return False

        except FileNotFoundError:
            print("❌ Node.js nicht verfügbar", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ Playwright-Fallback fehlgeschlagen: {e}", file=sys.stderr)
            return False

    def ensure_browser_available(self, use_fallback: bool = True) -> Dict[str, Any]:
        """
        Stellt sicher dass Browser verfügbar ist (CDP oder Playwright)

        Args:
            use_fallback: Falls True, nutze Playwright wenn CDP fehlschlägt

        Returns:
            Dict mit:
                - available: bool
                - mode: str ("cdp" oder "playwright")
                - message: str
        """
        result = {
            "available": False,
            "mode": None,
            "message": ""
        }

        # Strategie 1: CDP prüfen
        if self.check_cdp_available():
            result["available"] = True
            result["mode"] = "cdp"
            result["message"] = "Chrome CDP verfügbar"
            self.mode = "cdp"
            return result

        # Strategie 2: Chrome starten
        print("⚠️ CDP nicht verfügbar, versuche Chrome zu starten...", file=sys.stderr)
        if self.start_chrome_debug():
            result["available"] = True
            result["mode"] = "cdp"
            result["message"] = "Chrome CDP gestartet"
            self.mode = "cdp"
            return result

        # Strategie 3: Playwright Fallback
        if use_fallback:
            print("⚠️ Chrome-Start fehlgeschlagen, versuche Playwright Fallback...", file=sys.stderr)
            if self.start_playwright_fallback():
                result["available"] = True
                result["mode"] = "playwright"
                result["message"] = "Playwright Headless Fallback aktiv"
                return result

        # Alle Strategien fehlgeschlagen
        result["available"] = False
        result["message"] = "❌ Browser nicht verfügbar (CDP + Playwright fehlgeschlagen)"
        return result

    def get_status(self) -> Dict[str, Any]:
        """Gibt aktuellen Browser-Status zurück"""
        cdp_available = self.check_cdp_available()

        return {
            "cdp_available": cdp_available,
            "cdp_port": self.cdp_port,
            "current_mode": self.mode,
            "health": "healthy" if cdp_available else "unavailable"
        }


def main():
    """CLI-Entry-Point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="CDP Fallback Manager - Auto-Recovery für Chrome CDP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
    # Check CDP-Verfügbarkeit
    python3 scripts/cdp_fallback_manager.py check

    # Starte Browser (mit Fallback)
    python3 scripts/cdp_fallback_manager.py start --fallback

    # Status-Check
    python3 scripts/cdp_fallback_manager.py status --json

Commands:
    check     - Prüft ob CDP verfügbar ist
    start     - Startet Browser (CDP oder Playwright)
    status    - Zeigt aktuellen Status
        """
    )

    parser.add_argument(
        "command",
        choices=["check", "start", "status"],
        help="Command"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=9222,
        help="CDP Port (default: 9222)"
    )

    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Nutze Playwright Fallback wenn CDP fehlschlägt"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output als JSON"
    )

    args = parser.parse_args()

    manager = CDPFallbackManager(cdp_port=args.port)

    if args.command == "check":
        available = manager.check_cdp_available()
        if args.json:
            print(json.dumps({"available": available, "port": args.port}))
        else:
            if available:
                print(f"✅ CDP verfügbar auf Port {args.port}")
                sys.exit(0)
            else:
                print(f"❌ CDP nicht verfügbar auf Port {args.port}")
                sys.exit(1)

    elif args.command == "start":
        result = manager.ensure_browser_available(use_fallback=args.fallback)
        if args.json:
            print(json.dumps(result))
        else:
            print(result["message"])
            if result["available"]:
                print(f"Mode: {result['mode']}")
                sys.exit(0)
            else:
                sys.exit(1)

    elif args.command == "status":
        status = manager.get_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(f"CDP Port: {status['cdp_port']}")
            print(f"CDP Available: {'✅ Yes' if status['cdp_available'] else '❌ No'}")
            print(f"Current Mode: {status['current_mode'] or 'None'}")
            print(f"Health: {status['health']}")


if __name__ == "__main__":
    main()
