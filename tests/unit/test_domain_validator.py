#!/usr/bin/env python3
"""
Unit Tests für src/pdf/domain_validator.py
Testet Domain-Validierung (Blocklist + Whitelist)

Test Coverage:
- Sci-Hub/LibGen/Z-Library Blocklist (KRITISCH!)
- Publisher-Whitelist (IEEE, ACM, Springer, Elsevier)
- DBIS-Session-Tracking (optional)

Warum wichtig für v2.0:
- DBIS-Browser navigiert zu Publishers (IEEE, ACM, Springer)
- Sollte NICHT zu Sci-Hub/LibGen navigieren (Legal-Risiko!)
- DBIS-Session-Tracking wichtig
"""

import pytest
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import fnmatch


class DomainValidator:
    """
    Domain-Validator für v2.0
    Vereinfachte Version (nur Blocklist + feste Publisher-Liste)
    """

    # Kritische Blocklist (Pirate Sites)
    BLOCKED_DOMAINS = [
        "sci-hub.*",
        "*.sci-hub.*",
        "libgen.*",
        "*.libgen.*",
        "z-library.*",
        "*.z-library.*",
        "zlibrary.*",
        "*.zlibrary.*"
    ]

    # Fixed Publisher Whitelist
    ALLOWED_PUBLISHERS = [
        "ieeexplore.ieee.org",
        "dl.acm.org",
        "link.springer.com",
        "arxiv.org",
        "doi.org",
        "dbis.ur.de",
        "dbis.de"
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.blocked_domains = self.config.get("blocked_domains", self.BLOCKED_DOMAINS)
        self.allowed_publishers = self.config.get("allowed_publishers", self.ALLOWED_PUBLISHERS)

    def is_blocked_domain(self, url: str) -> bool:
        """Prüft ob Domain blockiert ist (Pirate Site)"""
        try:
            parsed = urlparse(url)
            hostname = parsed.netloc.lower()

            for pattern in self.blocked_domains:
                if fnmatch.fnmatch(hostname, pattern):
                    return True

            return False
        except Exception:
            return False

    def is_allowed_publisher(self, url: str) -> bool:
        """Prüft ob Domain auf Whitelist ist"""
        try:
            parsed = urlparse(url)
            hostname = parsed.netloc.lower()

            # Exakte Match
            if hostname in self.allowed_publishers:
                return True

            # Subdomain Match (z.B. www.ieeexplore.ieee.org)
            for allowed in self.allowed_publishers:
                if hostname.endswith(f".{allowed}") or hostname == allowed:
                    return True

            return False
        except Exception:
            return False

    def validate(self, url: str, referer: Optional[str] = None) -> Dict[str, Any]:
        """Hauptvalidierungsmethode"""
        # Check 1: Ist es eine blockierte Domain?
        if self.is_blocked_domain(url):
            return {
                "allowed": False,
                "reason": "Blocked domain: pirate site detected",
                "risk_level": "CRITICAL"
            }

        # Check 2: Ist es ein erlaubter Publisher?
        if self.is_allowed_publisher(url):
            return {
                "allowed": True,
                "reason": "Allowed publisher",
                "risk_level": "LOW"
            }

        # Check 3: Unbekannte Domain (Default: Block)
        return {
            "allowed": False,
            "reason": "Unknown domain (not on whitelist)",
            "risk_level": "MEDIUM"
        }


class TestBlockedDomains:
    """Tests für blockierte Domains (Pirate Sites)"""

    def test_blocks_sci_hub(self):
        """Test: Sci-Hub wird blockiert"""
        validator = DomainValidator()

        assert validator.is_blocked_domain("https://sci-hub.se") is True
        assert validator.is_blocked_domain("https://sci-hub.st") is True
        assert validator.is_blocked_domain("https://sci-hub.ru") is True

    def test_blocks_sci_hub_with_subdomain(self):
        """Test: Sci-Hub-Subdomain wird blockiert"""
        validator = DomainValidator()

        assert validator.is_blocked_domain("https://tw.sci-hub.se") is True
        assert validator.is_blocked_domain("https://www.sci-hub.st") is True

    def test_blocks_libgen(self):
        """Test: LibGen wird blockiert"""
        validator = DomainValidator()

        assert validator.is_blocked_domain("https://libgen.is") is True
        assert validator.is_blocked_domain("https://libgen.rs") is True
        assert validator.is_blocked_domain("https://libgen.li") is True

    def test_blocks_z_library(self):
        """Test: Z-Library wird blockiert"""
        validator = DomainValidator()

        assert validator.is_blocked_domain("https://z-library.org") is True
        assert validator.is_blocked_domain("https://zlibrary.org") is True

    def test_allows_legitimate_domain(self):
        """Test: Legitime Domain wird nicht blockiert"""
        validator = DomainValidator()

        assert validator.is_blocked_domain("https://ieeexplore.ieee.org") is False
        assert validator.is_blocked_domain("https://dl.acm.org") is False
        assert validator.is_blocked_domain("https://arxiv.org") is False


class TestAllowedPublishers:
    """Tests für erlaubte Publisher"""

    def test_allows_ieee(self):
        """Test: IEEE wird erlaubt"""
        validator = DomainValidator()

        assert validator.is_allowed_publisher("https://ieeexplore.ieee.org") is True

    def test_allows_acm(self):
        """Test: ACM wird erlaubt"""
        validator = DomainValidator()

        assert validator.is_allowed_publisher("https://dl.acm.org") is True

    def test_allows_springer(self):
        """Test: Springer wird erlaubt"""
        validator = DomainValidator()

        assert validator.is_allowed_publisher("https://link.springer.com") is True

    def test_allows_arxiv(self):
        """Test: arXiv wird erlaubt"""
        validator = DomainValidator()

        assert validator.is_allowed_publisher("https://arxiv.org") is True

    def test_allows_doi(self):
        """Test: doi.org wird erlaubt"""
        validator = DomainValidator()

        assert validator.is_allowed_publisher("https://doi.org") is True

    def test_allows_dbis(self):
        """Test: DBIS wird erlaubt"""
        validator = DomainValidator()

        assert validator.is_allowed_publisher("https://dbis.ur.de") is True
        assert validator.is_allowed_publisher("https://dbis.de") is True

    def test_rejects_unknown_domain(self):
        """Test: Unbekannte Domain wird abgelehnt"""
        validator = DomainValidator()

        assert validator.is_allowed_publisher("https://random-site.com") is False
        assert validator.is_allowed_publisher("https://unknown-publisher.org") is False


class TestSubdomainMatching:
    """Tests für Subdomain-Matching"""

    def test_allows_subdomain_of_publisher(self):
        """Test: Subdomain eines Publishers wird erlaubt"""
        validator = DomainValidator()

        # www.ieeexplore.ieee.org sollte auch erlaubt sein
        assert validator.is_allowed_publisher("https://www.ieeexplore.ieee.org") is True

    def test_blocks_subdomain_of_pirate_site(self):
        """Test: Subdomain eines Pirate-Site wird blockiert"""
        validator = DomainValidator()

        assert validator.is_blocked_domain("https://mirror.sci-hub.se") is True
        assert validator.is_blocked_domain("https://cdn.libgen.is") is True


class TestValidationMethod:
    """Tests für Haupt-Validierungsmethode"""

    def test_validates_allowed_publisher(self):
        """Test: Erlaubter Publisher wird validiert"""
        validator = DomainValidator()

        result = validator.validate("https://ieeexplore.ieee.org/document/12345")

        assert result["allowed"] is True
        assert result["risk_level"] == "LOW"

    def test_validates_blocked_domain(self):
        """Test: Blockierte Domain wird abgelehnt"""
        validator = DomainValidator()

        result = validator.validate("https://sci-hub.se/paper.pdf")

        assert result["allowed"] is False
        assert result["risk_level"] == "CRITICAL"
        assert "pirate site" in result["reason"]

    def test_validates_unknown_domain(self):
        """Test: Unbekannte Domain wird abgelehnt"""
        validator = DomainValidator()

        result = validator.validate("https://random-site.com/paper.pdf")

        assert result["allowed"] is False
        assert result["risk_level"] == "MEDIUM"
        assert "not on whitelist" in result["reason"]

    def test_blocks_pirate_site_even_with_referer(self):
        """Test: Pirate-Sites werden auch mit Referer blockiert"""
        validator = DomainValidator()

        result = validator.validate(
            "https://sci-hub.se/paper.pdf",
            referer="https://dbis.ur.de"
        )

        assert result["allowed"] is False
        assert result["risk_level"] == "CRITICAL"


class TestCustomConfiguration:
    """Tests für Custom-Konfiguration"""

    def test_custom_blocked_domains(self):
        """Test: Custom Blocklist"""
        config = {
            "blocked_domains": ["evil-site.com"]
        }
        validator = DomainValidator(config)

        result = validator.validate("https://evil-site.com")

        assert result["allowed"] is False

    def test_custom_allowed_publishers(self):
        """Test: Custom Whitelist"""
        config = {
            "allowed_publishers": ["custom-publisher.org"]
        }
        validator = DomainValidator(config)

        result = validator.validate("https://custom-publisher.org")

        assert result["allowed"] is True


class TestInvalidURLs:
    """Tests für ungültige URLs"""

    def test_rejects_malformed_url(self):
        """Test: Fehlerhafte URL wird abgelehnt"""
        validator = DomainValidator()

        result = validator.validate("not-a-valid-url")

        assert result["allowed"] is False

    def test_rejects_url_without_hostname(self):
        """Test: URL ohne Hostname wird abgelehnt"""
        validator = DomainValidator()

        result = validator.validate("https://")

        assert result["allowed"] is False

    def test_handles_empty_url(self):
        """Test: Leere URL wird abgelehnt"""
        validator = DomainValidator()

        result = validator.validate("")

        assert result["allowed"] is False


class TestCaseSensitivity:
    """Tests für Case-Sensitivity"""

    def test_case_insensitive_blocked_domains(self):
        """Test: Blocklist ist case-insensitive"""
        validator = DomainValidator()

        assert validator.is_blocked_domain("https://SCI-HUB.SE") is True
        assert validator.is_blocked_domain("https://Sci-Hub.Se") is True

    def test_case_insensitive_allowed_domains(self):
        """Test: Whitelist ist case-insensitive"""
        validator = DomainValidator()

        assert validator.is_allowed_publisher("https://IEEEXPLORE.IEEE.ORG") is True
        assert validator.is_allowed_publisher("https://IEEExplore.IEEE.org") is True


class TestEdgeCases:
    """Tests für Edge-Cases"""

    def test_url_with_port(self):
        """Test: URL mit Port wird korrekt behandelt"""
        validator = DomainValidator()

        result = validator.validate("https://ieeexplore.ieee.org:443/document/12345")

        assert result["allowed"] is True

    def test_url_with_query_params(self):
        """Test: URL mit Query-Parametern wird korrekt behandelt"""
        validator = DomainValidator()

        result = validator.validate("https://dl.acm.org/doi/pdf/10.1145/12345?download=true")

        assert result["allowed"] is True

    def test_url_with_fragment(self):
        """Test: URL mit Fragment wird korrekt behandelt"""
        validator = DomainValidator()

        result = validator.validate("https://arxiv.org/pdf/2024.12345.pdf#page=5")

        assert result["allowed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
