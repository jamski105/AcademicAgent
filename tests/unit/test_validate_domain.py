#!/usr/bin/env python3
"""
Unit-Tests für validate_domain.py
Testet Domain-Whitelist und DBIS-Proxy-Modus
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path

# Füge scripts/ zu Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from validate_domain import (
    validate_domain_proxy_mode,
    validate_domain_legacy,
    is_trusted_proxy,
    is_blocked_domain,
    load_whitelist
)


@pytest.fixture
def test_config():
    """Fixture für Test-Konfiguration"""
    return {
        "proxy_mode": "dbis_only",
        "trusted_proxies": [
            "dbis.ur.de",
            "dbis.de",
            "ezproxy.uni-regensburg.de"
        ],
        "proxy_redirect_policy": {
            "allow_redirects_from_trusted_proxies": True,
            "session_tracking_required": True,
            "direct_navigation_blocked": True
        },
        "allowed_domains": [
            "ieeexplore.ieee.org",
            "dl.acm.org",
            "arxiv.org",
            "doi.org"
        ],
        "blocked_domains": [
            "sci-hub.*",
            "*.sci-hub.*",
            "libgen.*",
            "z-library.*"
        ],
        "allowed_patterns": [
            "https://doi.org/*",
            "https://arxiv.org/pdf/*"
        ]
    }


class TestTrustedProxies:
    """Tests für Trusted-Proxy-Erkennung"""

    def test_recognizes_dbis_ur_de(self, test_config):
        """Testet ob dbis.ur.de als Proxy erkannt wird"""
        assert is_trusted_proxy("dbis.ur.de", test_config) is True

    def test_recognizes_subdomain_of_proxy(self, test_config):
        """Testet ob Subdomain eines Proxys erkannt wird"""
        assert is_trusted_proxy("www.dbis.ur.de", test_config) is True

    def test_rejects_non_proxy_domain(self, test_config):
        """Testet ob Nicht-Proxy-Domain abgelehnt wird"""
        assert is_trusted_proxy("example.com", test_config) is False


class TestBlockedDomains:
    """Tests für blockierte Domains"""

    def test_blocks_sci_hub(self, test_config):
        """Testet ob Sci-Hub blockiert wird"""
        assert is_blocked_domain("sci-hub.se", test_config) is True

    def test_blocks_sci_hub_with_subdomain(self, test_config):
        """Testet ob Sci-Hub-Subdomain blockiert wird"""
        assert is_blocked_domain("tw.sci-hub.se", test_config) is True

    def test_blocks_libgen(self, test_config):
        """Testet ob LibGen blockiert wird"""
        assert is_blocked_domain("libgen.is", test_config) is True

    def test_blocks_z_library(self, test_config):
        """Testet ob Z-Library blockiert wird"""
        assert is_blocked_domain("z-library.org", test_config) is True

    def test_allows_legitimate_domain(self, test_config):
        """Testet ob legitime Domain erlaubt wird"""
        assert is_blocked_domain("ieeexplore.ieee.org", test_config) is False


class TestProxyModeValidation:
    """Tests für DBIS-Proxy-Modus-Validierung"""

    def test_always_allows_dbis_domain(self, test_config):
        """Testet ob DBIS immer erlaubt ist"""
        result = validate_domain_proxy_mode(
            "https://dbis.ur.de/search",
            test_config
        )
        assert result["allowed"] is True
        assert result["is_proxy"] is True

    def test_blocks_direct_navigation_to_database(self, test_config):
        """Testet ob direkte Navigation zu DB blockiert wird"""
        result = validate_domain_proxy_mode(
            "https://ieeexplore.ieee.org/document/12345",
            test_config,
            referer=None,
            session_file=None
        )
        assert result["allowed"] is False
        assert "Direct database access blocked" in result["reason"]

    def test_allows_database_with_dbis_referer(self, test_config):
        """Testet ob DB-Zugriff mit DBIS-Referer erlaubt ist"""
        result = validate_domain_proxy_mode(
            "https://ieeexplore.ieee.org/document/12345",
            test_config,
            referer="https://dbis.ur.de/database-list",
            session_file=None
        )
        assert result["allowed"] is True
        assert result["via_proxy"] is True
        assert result["referer_is_dbis"] is True

    def test_allows_database_with_active_dbis_session(self, test_config):
        """Testet ob DB-Zugriff mit aktiver DBIS-Session erlaubt ist"""
        # Erstelle temporäre Session-Datei
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            session_data = {
                "session_active": True,
                "started_from_dbis": True,
                "navigation_count": 5
            }
            json.dump(session_data, f)
            session_file = f.name

        try:
            result = validate_domain_proxy_mode(
                "https://ieeexplore.ieee.org/document/12345",
                test_config,
                referer=None,
                session_file=session_file
            )
            assert result["allowed"] is True
            assert result["session_from_dbis"] is True
        finally:
            Path(session_file).unlink()

    def test_blocks_pirate_site_even_with_dbis_referer(self, test_config):
        """Testet ob Pirate-Sites auch mit DBIS-Referer blockiert werden"""
        result = validate_domain_proxy_mode(
            "https://sci-hub.se/paper.pdf",
            test_config,
            referer="https://dbis.ur.de"
        )
        assert result["allowed"] is False
        assert "pirate site" in result["reason"]
        assert result["risk_level"] == "CRITICAL"


class TestLegacyModeValidation:
    """Tests für Legacy-Whitelist-Modus"""

    def test_allows_whitelisted_domain(self, test_config):
        """Testet ob whitelisted Domain erlaubt wird"""
        result = validate_domain_legacy(
            "https://ieeexplore.ieee.org/document/12345",
            test_config
        )
        assert result["allowed"] is True

    def test_blocks_non_whitelisted_domain(self, test_config):
        """Testet ob nicht-whitelisted Domain blockiert wird"""
        result = validate_domain_legacy(
            "https://random-site.com/paper.pdf",
            test_config
        )
        assert result["allowed"] is False

    def test_blocks_pirate_sites(self, test_config):
        """Testet ob Pirate-Sites blockiert werden"""
        result = validate_domain_legacy(
            "https://sci-hub.se/paper",
            test_config
        )
        assert result["allowed"] is False
        assert result["risk_level"] == "CRITICAL"

    def test_allows_doi_org(self, test_config):
        """Testet ob doi.org erlaubt wird"""
        result = validate_domain_legacy(
            "https://doi.org/10.1109/example",
            test_config
        )
        assert result["allowed"] is True


class TestAllowedPatterns:
    """Tests für Allowed-Patterns"""

    def test_matches_doi_pattern(self, test_config):
        """Testet ob DOI-Pattern gematched wird"""
        result = validate_domain_legacy(
            "https://doi.org/10.1234/abcdef",
            test_config
        )
        assert result["allowed"] is True

    def test_matches_arxiv_pdf_pattern(self, test_config):
        """Testet ob arXiv-PDF-Pattern gematched wird"""
        result = validate_domain_legacy(
            "https://arxiv.org/pdf/2024.12345v1.pdf",
            test_config
        )
        assert result["allowed"] is True


class TestInvalidURLs:
    """Tests für ungültige URLs"""

    def test_rejects_malformed_url(self, test_config):
        """Testet ob fehlerhafte URL abgelehnt wird"""
        result = validate_domain_legacy(
            "not-a-valid-url",
            test_config
        )
        assert result["allowed"] is False
        assert "Invalid URL" in result["reason"]

    def test_rejects_url_without_hostname(self, test_config):
        """Testet ob URL ohne Hostname abgelehnt wird"""
        result = validate_domain_legacy(
            "https://",
            test_config
        )
        assert result["allowed"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
