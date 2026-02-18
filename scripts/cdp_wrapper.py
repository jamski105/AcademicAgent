#!/usr/bin/env python3
"""
CDP-Wrapper für AcademicAgent Browser-Agent
Kapselt alle Chrome-DevTools-Protocol-Operationen

Zweck:
    - Reduziert Browser-Agent-Privilegien (kein direkter Bash-Zugriff nötig)
    - Bietet sichere, validierte CDP-Operationen
    - Zentrale Error-Handling und Logging

Verwendung:
    from scripts.cdp_wrapper import CDP Client

    cdp = CDPClient()
    cdp.navigate("https://ieeexplore.ieee.org")
    html = cdp.get_html()
    cdp.screenshot("output.png")
    cdp.close()
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class NavigationResult:
    """Resultat einer Navigation"""
    success: bool
    url: str
    error: Optional[str] = None
    status_code: Optional[int] = None


@dataclass
class SearchResult:
    """Resultat einer Datenbank-Suche"""
    success: bool
    papers_found: int
    results: List[Dict[str, Any]]
    error: Optional[str] = None


class CDPClient:
    """
    CDP-Client für sichere Browser-Automatisierung

    Kapselt alle Browser-Operationen hinter einer sauberen API
    """

    def __init__(self, port: int = 9222, timeout: int = 30):
        """
        Initialisiert CDP-Client

        Args:
            port: Chrome-CDP-Port (default: 9222)
            timeout: Timeout für Operationen in Sekunden (default: 30)
        """
        self.port = port
        self.timeout = timeout
        self.cdp_helper_path = Path(__file__).parent / "browser_cdp_helper.js"

        # Prüfe ob CDP-Helper existiert
        if not self.cdp_helper_path.exists():
            raise FileNotFoundError(
                f"CDP-Helper nicht gefunden: {self.cdp_helper_path}"
            )

        # Prüfe Chrome-Verbindung
        self._check_connection()

    def _check_connection(self) -> bool:
        """
        Prüft CDP-Verbindung zu Chrome

        Returns:
            True wenn verbunden

        Raises:
            ConnectionError: Wenn Chrome nicht erreichbar
        """
        try:
            result = subprocess.run(
                ["curl", "-s", f"http://localhost:{self.port}/json/version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                raise ConnectionError(
                    f"Chrome CDP nicht erreichbar auf Port {self.port}. "
                    "Bitte starte Chrome mit: bash scripts/start_chrome_debug.sh"
                )

            return True

        except subprocess.TimeoutExpired:
            raise ConnectionError("Chrome CDP Timeout")
        except Exception as e:
            raise ConnectionError(f"CDP-Verbindungsfehler: {str(e)}")

    def _call_helper(self, command: str, *args) -> Dict[str, Any]:
        """
        Ruft browser_cdp_helper.js auf

        Args:
            command: Kommando (z.B. "navigate", "screenshot")
            *args: Argumente für Kommando

        Returns:
            Dict mit Resultat

        Raises:
            RuntimeError: Bei Fehler
        """
        cmd = ["node", str(self.cdp_helper_path), command] + list(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"CDP-Helper Fehler: {result.stderr}\n"
                    f"Command: {' '.join(cmd)}"
                )

            # Parse JSON-Output
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # Falls kein JSON, gib raw output zurück
                return {"success": True, "output": result.stdout}

        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"CDP-Operation Timeout nach {self.timeout}s\n"
                f"Command: {command}"
            )
        except Exception as e:
            raise RuntimeError(f"CDP-Helper Fehler: {str(e)}")

    def navigate(self, url: str, wait_seconds: int = 3) -> NavigationResult:
        """
        Navigiert zu URL

        Args:
            url: Ziel-URL
            wait_seconds: Wartezeit nach Navigation (default: 3)

        Returns:
            NavigationResult
        """
        try:
            result = self._call_helper("navigate", url)

            # Warte auf Page-Load
            time.sleep(wait_seconds)

            return NavigationResult(
                success=True,
                url=url,
                status_code=result.get("status_code")
            )

        except Exception as e:
            return NavigationResult(
                success=False,
                url=url,
                error=str(e)
            )

    def get_html(self) -> Optional[str]:
        """
        Holt HTML-Inhalt der aktuellen Seite

        Returns:
            HTML-String oder None bei Fehler
        """
        try:
            result = self._call_helper("getHTML")
            return result.get("html")
        except Exception as e:
            print(f"❌ Fehler beim HTML-Abruf: {e}", file=sys.stderr)
            return None

    def screenshot(self, output_path: str) -> bool:
        """
        Erstellt Screenshot der aktuellen Seite

        Args:
            output_path: Pfad für Screenshot (z.B. "output.png")

        Returns:
            True bei Erfolg
        """
        try:
            self._call_helper("screenshot", output_path)
            return True
        except Exception as e:
            print(f"❌ Screenshot-Fehler: {e}", file=sys.stderr)
            return False

    def search_database(
        self,
        database_name: str,
        search_string: str,
        patterns_file: Optional[str] = None
    ) -> SearchResult:
        """
        Führt Datenbank-Suche aus

        Args:
            database_name: Name der Datenbank (z.B. "IEEE Xplore")
            search_string: Suchstring (Boolean Query)
            patterns_file: Pfad zu database_patterns.json (optional)

        Returns:
            SearchResult
        """
        try:
            # Standard-Pattern-Datei falls nicht angegeben
            if patterns_file is None:
                patterns_file = str(Path(__file__).parent / "database_patterns.json")

            result = self._call_helper(
                "search",
                patterns_file,
                database_name,
                search_string
            )

            return SearchResult(
                success=result.get("success", False),
                papers_found=len(result.get("results", [])),
                results=result.get("results", []),
                error=result.get("error")
            )

        except Exception as e:
            return SearchResult(
                success=False,
                papers_found=0,
                results=[],
                error=str(e)
            )

    def click_element(self, selector: str) -> bool:
        """
        Klickt auf Element (via Selektor)

        Args:
            selector: CSS-Selektor

        Returns:
            True bei Erfolg
        """
        try:
            self._call_helper("click", selector)
            return True
        except Exception as e:
            print(f"❌ Click-Fehler: {e}", file=sys.stderr)
            return False

    def type_text(self, selector: str, text: str) -> bool:
        """
        Tippt Text in Element

        Args:
            selector: CSS-Selektor
            text: Einzugebender Text

        Returns:
            True bei Erfolg
        """
        try:
            self._call_helper("type", selector, text)
            return True
        except Exception as e:
            print(f"❌ Type-Fehler: {e}", file=sys.stderr)
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Holt Browser-Status

        Returns:
            Dict mit Status-Informationen
        """
        try:
            return self._call_helper("status")
        except Exception as e:
            return {"error": str(e)}

    def wait_for_selector(self, selector: str, timeout: int = 10) -> bool:
        """
        Wartet auf Selektor

        Args:
            selector: CSS-Selektor
            timeout: Timeout in Sekunden

        Returns:
            True wenn Element gefunden
        """
        try:
            self._call_helper("waitForSelector", selector, str(timeout))
            return True
        except Exception:
            return False

    def close(self):
        """Schließt CDP-Verbindung (optional, da Chrome weiterläuft)"""
        pass


# ============================================
# Convenience-Funktionen
# ============================================

def create_cdp_client(port: int = 9222) -> CDPClient:
    """
    Erstellt CDP-Client mit Error-Handling

    Args:
        port: Chrome-CDP-Port

    Returns:
        CDPClient-Instanz

    Raises:
        ConnectionError: Falls Chrome nicht erreichbar
    """
    return CDPClient(port=port)


def safe_navigate(cdp: CDPClient, url: str, max_retries: int = 2) -> NavigationResult:
    """
    Navigiert mit Retry-Logik

    Args:
        cdp: CDPClient-Instanz
        url: Ziel-URL
        max_retries: Maximale Retries

    Returns:
        NavigationResult
    """
    for attempt in range(max_retries + 1):
        result = cdp.navigate(url)

        if result.success:
            return result

        if attempt < max_retries:
            wait_time = 2 ** attempt  # Exponential Backoff
            print(f"⚠️  Navigation fehlgeschlagen, Retry in {wait_time}s...", file=sys.stderr)
            time.sleep(wait_time)

    return result


# ============================================
# Beispiel-Verwendung
# ============================================

if __name__ == "__main__":
    print("🧪 Teste CDP-Wrapper...\n")

    try:
        # Erstelle Client
        cdp = create_cdp_client()
        print("✅ CDP-Client erstellt\n")

        # Teste Navigation
        print("Test 1: Navigation zu example.com")
        result = cdp.navigate("https://example.com")
        if result.success:
            print(f"  ✅ Navigation erfolgreich: {result.url}")
        else:
            print(f"  ❌ Navigation fehlgeschlagen: {result.error}")

        # Teste HTML-Abruf
        print("\nTest 2: HTML-Abruf")
        html = cdp.get_html()
        if html:
            print(f"  ✅ HTML abgerufen ({len(html)} Zeichen)")
        else:
            print("  ❌ HTML-Abruf fehlgeschlagen")

        # Teste Screenshot
        print("\nTest 3: Screenshot")
        screenshot_path = "/tmp/cdp_test_screenshot.png"
        if cdp.screenshot(screenshot_path):
            print(f"  ✅ Screenshot erstellt: {screenshot_path}")
        else:
            print("  ❌ Screenshot fehlgeschlagen")

        # Teste Status
        print("\nTest 4: Browser-Status")
        status = cdp.get_status()
        print(f"  ✅ Status: {json.dumps(status, indent=2)}")

        print("\n✅ Alle Tests abgeschlossen!")

    except ConnectionError as e:
        print(f"\n❌ CDP-Verbindungsfehler: {e}")
        print("\n💡 Starte Chrome mit: bash scripts/start_chrome_debug.sh")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        sys.exit(1)
