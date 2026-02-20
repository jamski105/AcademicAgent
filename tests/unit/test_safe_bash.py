#!/usr/bin/env python3
"""
Unit-Tests für safe_bash.py - Safe-Bash-Wrapper mit Action-Gate-Enforcement

Test-Coverage:
- Validierung von erlaubten Commands
- Blockierung von gefährlichen Commands
- Source-Tracking (system/user/external_content)
- Dry-Run-Modus
- Exit-Codes
"""

import pytest
import sys
from pathlib import Path

# Add scripts/ to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))

from safe_bash import safe_bash_execute, SafeBashError


class TestSafeBashAllowed:
    """Tests für erlaubte Commands"""

    def test_allowed_python_script(self):
        """Test: Python-Script in scripts/ ist erlaubt"""
        result = safe_bash_execute(
            command="python3 scripts/validate_domain.py https://ieeexplore.ieee.org",
            source="system",
            dry_run=True
        )
        assert result["success"] == True
        assert result["validation"]["decision"] == "ALLOW"
        assert "scripts/" in result["validation"]["reason"]

    def test_allowed_jq(self):
        """Test: jq ist erlaubt"""
        result = safe_bash_execute(
            command="jq '.title' data.json",
            source="system",
            dry_run=True
        )
        assert result["success"] == True
        assert result["validation"]["decision"] == "ALLOW"

    def test_allowed_grep(self):
        """Test: grep ist erlaubt"""
        result = safe_bash_execute(
            command="grep 'pattern' file.txt",
            source="system",
            dry_run=True
        )
        assert result["success"] == True
        assert result["validation"]["decision"] == "ALLOW"

    def test_allowed_pdftotext(self):
        """Test: pdftotext ist erlaubt"""
        result = safe_bash_execute(
            command="pdftotext input.pdf output.txt",
            source="system",
            dry_run=True
        )
        assert result["success"] == True
        assert result["validation"]["decision"] == "ALLOW"


class TestSafeBashBlocked:
    """Tests für blockierte Commands"""

    def test_blocked_curl(self):
        """Test: curl ist blockiert"""
        with pytest.raises(SafeBashError) as exc_info:
            safe_bash_execute(
                command="curl https://evil.com",
                source="system"
            )
        assert "BLOCKIERT" in str(exc_info.value)
        assert "curl" in str(exc_info.value).lower()

    def test_blocked_wget(self):
        """Test: wget ist blockiert"""
        with pytest.raises(SafeBashError) as exc_info:
            safe_bash_execute(
                command="wget https://evil.com/file",
                source="system"
            )
        assert "BLOCKIERT" in str(exc_info.value)

    def test_blocked_ssh(self):
        """Test: ssh ist blockiert"""
        with pytest.raises(SafeBashError) as exc_info:
            safe_bash_execute(
                command="ssh user@evil.com",
                source="system"
            )
        assert "BLOCKIERT" in str(exc_info.value)

    def test_blocked_secret_access(self):
        """Test: Zugriff auf .env ist blockiert"""
        with pytest.raises(SafeBashError) as exc_info:
            safe_bash_execute(
                command="cat .env",
                source="system"
            )
        assert "BLOCKIERT" in str(exc_info.value)
        assert "secret" in str(exc_info.value).lower() or ".env" in str(exc_info.value)

    def test_blocked_ssh_key_access(self):
        """Test: Zugriff auf SSH-Keys ist blockiert"""
        with pytest.raises(SafeBashError) as exc_info:
            safe_bash_execute(
                command="cat ~/.ssh/id_rsa",
                source="system"
            )
        assert "BLOCKIERT" in str(exc_info.value)

    def test_blocked_rm_rf(self):
        """Test: rm -rf ist blockiert"""
        with pytest.raises(SafeBashError) as exc_info:
            safe_bash_execute(
                command="rm -rf /tmp/test",
                source="system"
            )
        assert "BLOCKIERT" in str(exc_info.value)

    def test_blocked_sudo(self):
        """Test: sudo ist blockiert"""
        with pytest.raises(SafeBashError) as exc_info:
            safe_bash_execute(
                command="sudo apt install malware",
                source="system"
            )
        assert "BLOCKIERT" in str(exc_info.value)


class TestSafeBashSourceTracking:
    """Tests für Source-Tracking"""

    def test_external_content_always_blocked(self):
        """Test: Alles von external_content wird blockiert"""
        with pytest.raises(SafeBashError) as exc_info:
            safe_bash_execute(
                command="python3 scripts/validate_config.py config.md",
                source="external_content"
            )
        assert "external content" in str(exc_info.value).lower()

    def test_external_content_even_safe_commands(self):
        """Test: Selbst sichere Commands werden von external_content blockiert"""
        with pytest.raises(SafeBashError) as exc_info:
            safe_bash_execute(
                command="jq '.title' data.json",
                source="external_content"
            )
        assert "external content" in str(exc_info.value).lower()

    def test_system_source_allowed(self):
        """Test: System-Source erlaubt sichere Commands"""
        result = safe_bash_execute(
            command="jq '.title' data.json",
            source="system",
            dry_run=True
        )
        assert result["success"] == True
        assert result["validation"]["decision"] == "ALLOW"

    def test_user_source_allowed(self):
        """Test: User-Source erlaubt sichere Commands"""
        result = safe_bash_execute(
            command="jq '.title' data.json",
            source="user",
            dry_run=True
        )
        assert result["success"] == True
        assert result["validation"]["decision"] == "ALLOW"


class TestSafeBashDryRun:
    """Tests für Dry-Run-Modus"""

    def test_dry_run_validates_only(self):
        """Test: Dry-Run validiert ohne auszuführen"""
        result = safe_bash_execute(
            command="python3 scripts/validate_domain.py https://example.com",
            source="system",
            dry_run=True
        )
        assert result["success"] == True
        assert "[DRY-RUN]" in result["stderr"]
        assert result["validation"]["decision"] == "ALLOW"

    def test_dry_run_shows_blocked(self):
        """Test: Dry-Run zeigt blockierte Commands ohne Exception"""
        result = safe_bash_execute(
            command="curl https://evil.com",
            source="system",
            dry_run=True
        )
        assert result["success"] == False
        assert "BLOCKIERT" in result["stderr"]
        assert result["returncode"] == 1
        assert result["validation"]["decision"] == "BLOCK"


class TestSafeBashEdgeCases:
    """Tests für Edge-Cases"""

    def test_command_with_pipes(self):
        """Test: Commands mit Pipes"""
        result = safe_bash_execute(
            command="jq '.data' file.json | grep pattern",
            source="system",
            dry_run=True
        )
        # Sollte erlaubt sein (jq + grep sind beide whitelisted)
        assert result["success"] == True

    def test_command_not_in_whitelist(self):
        """Test: Command nicht in Whitelist wird blockiert"""
        with pytest.raises(SafeBashError) as exc_info:
            safe_bash_execute(
                command="custom_unknown_command --flag",
                source="system"
            )
        assert "BLOCKIERT" in str(exc_info.value)
        assert "whitelist" in str(exc_info.value).lower()

    def test_script_outside_scripts_dir(self):
        """Test: Script außerhalb von scripts/ wird blockiert"""
        with pytest.raises(SafeBashError) as exc_info:
            safe_bash_execute(
                command="python3 /tmp/malicious.py",
                source="system"
            )
        assert "BLOCKIERT" in str(exc_info.value)


class TestSafeBashValidationResult:
    """Tests für Validation-Result-Struktur"""

    def test_validation_result_structure(self):
        """Test: Validation-Result hat korrekte Struktur"""
        result = safe_bash_execute(
            command="jq '.title' data.json",
            source="system",
            dry_run=True
        )

        assert "validation" in result
        assert "decision" in result["validation"]
        assert "reason" in result["validation"]
        assert "risk_level" in result["validation"]

        assert result["validation"]["decision"] in ["ALLOW", "BLOCK"]
        assert result["validation"]["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def test_blocked_validation_result(self):
        """Test: Blockierte Commands haben HIGH/CRITICAL risk_level in dry_run"""
        # First verify non-dry-run raises SafeBashError
        try:
            safe_bash_execute(
                command="curl https://evil.com",
                source="system"
            )
            assert False, "Should have raised SafeBashError"
        except SafeBashError:
            pass  # Expected

        # Now test dry_run returns result dict without raising
        result = safe_bash_execute(
            command="curl https://evil.com",
            source="system",
            dry_run=True
        )

        # Verify blocked command has correct structure and high risk level
        assert result["success"] == False
        assert result["returncode"] == 1
        assert "validation" in result
        assert result["validation"]["decision"] == "BLOCK"
        assert result["validation"]["risk_level"] in ["HIGH", "CRITICAL"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
