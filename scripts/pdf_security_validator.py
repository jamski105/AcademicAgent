#!/usr/bin/env python3
"""
PDF Security Validator - Deep Analysis für Prompt-Injection-Schutz

Zweck:
    - Prüft PDFs auf potenzielle Injection-Versuche
    - Entfernt/bereinigt Metadaten
    - Erkennt verdächtige Patterns (Redundanz, embedded JS, etc.)
    - Erzeugt sicheren Plain-Text-Output

Verwendung:
    python3 scripts/pdf_security_validator.py input.pdf output.txt
    python3 scripts/pdf_security_validator.py input.pdf output.txt --report report.json

Features:
    1. Metadata Stripping (Author/Title/Keywords entfernen)
    2. Redundancy Detection (wiederholte Injection-Strings)
    3. PDF Structure Validation (JS, Forms, Actions)
    4. Injection Pattern Detection
"""

import sys
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import Counter


class PDFSecurityValidator:
    """Validiert PDFs auf Security-Risiken"""

    # Injection-Patterns (aus sanitize_html.py übernommen + erweitert)
    INJECTION_PATTERNS = [
        (r'ignore\s+(all\s+)?(previous|prior)\s+instructions?', 'Ignore instructions'),
        (r'you\s+are\s+now\s+(a|an)\s+\w+', 'Role takeover'),
        (r'(execute|run)\s+(command|bash|shell|script)', 'Command execution'),
        (r'(upload|send|exfiltrate)\s+(file|secret|config|data)', 'Data exfiltration'),
        (r'(curl|wget|ssh|scp|rsync)\s+', 'Network command'),
        (r'read\s+(\.env|~/.ssh|secret|credential|token)', 'Secret access'),
        (r'system\s+prompt|developer\s+instructions?', 'System instruction override'),
        (r'<\s*script[^>]*>', 'Script tag (HTML in PDF)'),
        (r'(cat|rm|mv)\s+[-/~]', 'File system commands'),
    ]

    def __init__(self, pdf_path: str, output_path: str, report_path: str = None):
        self.pdf_path = Path(pdf_path)
        self.output_path = Path(output_path)
        self.report_path = Path(report_path) if report_path else None
        self.warnings = []
        self.metadata = {}
        self.structure_info = {}

    def validate(self) -> Dict[str, Any]:
        """
        Führt vollständige Validierung durch

        Returns:
            Dict mit:
                - safe: bool (PDF ist sicher)
                - warnings: List[str] (Warnungen)
                - risk_level: str (LOW/MEDIUM/HIGH/CRITICAL)
                - cleaned_text: str (Bereinigter Text)
        """
        result = {
            "safe": True,
            "warnings": [],
            "risk_level": "LOW",
            "checks_performed": [],
            "metadata_stripped": False,
            "text_length": 0
        }

        # Check 1: PDF existiert?
        if not self.pdf_path.exists():
            result["safe"] = False
            result["risk_level"] = "CRITICAL"
            result["warnings"].append(f"PDF not found: {self.pdf_path}")
            return result

        # Check 2: Metadata analysieren
        result["checks_performed"].append("metadata_analysis")
        metadata_warnings = self._analyze_metadata()
        result["warnings"].extend(metadata_warnings)

        # Check 3: PDF-Struktur prüfen
        result["checks_performed"].append("structure_validation")
        structure_warnings = self._validate_structure()
        result["warnings"].extend(structure_warnings)

        # Check 4: Text extrahieren (ohne Metadata)
        result["checks_performed"].append("text_extraction")
        text = self._extract_clean_text()
        result["text_length"] = len(text)

        # Check 5: Redundancy Detection
        result["checks_performed"].append("redundancy_detection")
        redundancy_warnings = self._detect_redundancy(text)
        result["warnings"].extend(redundancy_warnings)

        # Check 6: Injection Pattern Detection
        result["checks_performed"].append("injection_detection")
        injection_warnings = self._detect_injections(text)
        result["warnings"].extend(injection_warnings)

        # Check 7: Risiko-Level bestimmen
        result["risk_level"] = self._calculate_risk_level(result["warnings"])

        # Check 8: Sicheren Text schreiben
        if result["risk_level"] in ["LOW", "MEDIUM"]:
            self._write_clean_text(text)
            result["safe"] = True
        else:
            result["safe"] = False
            result["warnings"].append("⚠️ PDF nicht extrahiert - Risiko zu hoch")

        # Check 9: Report schreiben (falls gewünscht)
        if self.report_path:
            self._write_report(result)

        return result

    def _analyze_metadata(self) -> List[str]:
        """Analysiert PDF-Metadaten auf verdächtige Inhalte"""
        warnings = []

        try:
            # Verwende pdfinfo für Metadata-Extraktion
            result = subprocess.run(
                ["pdfinfo", str(self.pdf_path)],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                warnings.append("⚠️ pdfinfo fehlgeschlagen - Metadata nicht analysierbar")
                return warnings

            # Parse Metadata
            metadata = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

            self.metadata = metadata

            # Check verdächtige Metadata-Felder
            suspicious_fields = ['Author', 'Title', 'Subject', 'Keywords']
            for field in suspicious_fields:
                if field in metadata and metadata[field]:
                    value = metadata[field]

                    # Check auf Injection-Patterns in Metadata
                    for pattern, name in self.INJECTION_PATTERNS:
                        if re.search(pattern, value, re.IGNORECASE):
                            warnings.append(f"🚨 Injection in Metadata [{field}]: {name}")

                    # Check auf ungewöhnlich lange Metadata-Werte
                    if len(value) > 200:
                        warnings.append(f"⚠️ Ungewöhnlich langes Metadata-Feld [{field}]: {len(value)} chars")

        except FileNotFoundError:
            warnings.append("⚠️ pdfinfo nicht verfügbar - installiere poppler-utils")
        except subprocess.TimeoutExpired:
            warnings.append("⚠️ pdfinfo Timeout - PDF evtl. korrupt")
        except Exception as e:
            warnings.append(f"⚠️ Metadata-Analyse-Fehler: {str(e)}")

        return warnings

    def _validate_structure(self) -> List[str]:
        """Validiert PDF-Struktur auf eingebettete Scripts/Forms"""
        warnings = []

        try:
            # Verwende pdftotext mit -nopgbrk um Raw-Stream zu bekommen
            result = subprocess.run(
                ["pdftotext", "-nopgbrk", str(self.pdf_path), "-"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                warnings.append("⚠️ PDF-Struktur-Validierung fehlgeschlagen")
                return warnings

            raw_content = result.stdout

            # Check auf eingebettetes JavaScript
            js_patterns = [
                r'/JavaScript',
                r'/JS\s*<<',
                r'/OpenAction',
                r'/AA\s*<<'  # Automatic Action
            ]

            for pattern in js_patterns:
                if re.search(pattern, raw_content, re.IGNORECASE):
                    warnings.append(f"🚨 CRITICAL: Eingebettetes JavaScript gefunden ({pattern})")
                    self.structure_info["has_javascript"] = True

            # Check auf Forms
            if re.search(r'/AcroForm', raw_content, re.IGNORECASE):
                warnings.append("⚠️ PDF enthält Formular-Elemente")
                self.structure_info["has_forms"] = True

            # Check auf URIs/Launch-Actions
            if re.search(r'/Launch|/URI', raw_content, re.IGNORECASE):
                warnings.append("⚠️ PDF enthält externe Links/Launch-Actions")
                self.structure_info["has_external_links"] = True

        except FileNotFoundError:
            warnings.append("⚠️ pdftotext nicht verfügbar")
        except subprocess.TimeoutExpired:
            warnings.append("⚠️ pdftotext Timeout - PDF evtl. sehr groß oder korrupt")
        except Exception as e:
            warnings.append(f"⚠️ Struktur-Validierungs-Fehler: {str(e)}")

        return warnings

    def _extract_clean_text(self) -> str:
        """Extrahiert Text OHNE Metadata-Pollution"""
        try:
            # Verwende -layout für besseres Layout
            result = subprocess.run(
                ["pdftotext", "-layout", str(self.pdf_path), "-"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                return ""

            text = result.stdout

            # Truncate bei 100,000 chars (wie in browser-agent dokumentiert)
            if len(text) > 100000:
                self.warnings.append(f"⚠️ PDF-Text gekürzt (Original: {len(text)} → 100,000 chars)")
                text = text[:100000]

            return text

        except Exception as e:
            self.warnings.append(f"⚠️ Text-Extraktion fehlgeschlagen: {str(e)}")
            return ""

    def _detect_redundancy(self, text: str) -> List[str]:
        """Erkennt wiederholte Phrases (potenzielle Injection-Flooding)"""
        warnings = []

        # Split in Phrases (5-word-windows)
        words = text.split()
        phrases = []

        window_size = 5
        for i in range(len(words) - window_size + 1):
            phrase = ' '.join(words[i:i+window_size]).lower()
            phrases.append(phrase)

        # Zähle Häufigkeiten
        phrase_counts = Counter(phrases)

        # Check auf excessive Repetition
        for phrase, count in phrase_counts.most_common(10):
            if count > 10:  # Threshold: >10 Wiederholungen
                # Prüfe ob es eine Injection-Phrase ist
                is_injection = False
                for pattern, name in self.INJECTION_PATTERNS:
                    if re.search(pattern, phrase, re.IGNORECASE):
                        is_injection = True
                        warnings.append(f"🚨 FLOODING DETECTED: '{phrase[:50]}...' wiederholt {count}x (Injection-Pattern: {name})")
                        break

                if not is_injection and count > 50:
                    # Auch normale Phrases mit >50 Wiederholungen sind suspekt
                    warnings.append(f"⚠️ Excessive Repetition: '{phrase[:50]}...' wiederholt {count}x")

        return warnings

    def _detect_injections(self, text: str) -> List[str]:
        """Erkennt Injection-Patterns im Text"""
        warnings = []
        detected_patterns = []

        for pattern, name in self.INJECTION_PATTERNS:
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
            if matches:
                detected_patterns.append(name)
                # Zeige erste 3 Matches
                for i, match in enumerate(matches[:3]):
                    context_start = max(0, match.start() - 30)
                    context_end = min(len(text), match.end() + 30)
                    context = text[context_start:context_end].replace('\n', ' ')
                    warnings.append(f"🚨 Injection-Pattern [{name}]: '...{context}...' (Match {i+1}/{len(matches)})")

                if len(matches) > 3:
                    warnings.append(f"   ... und {len(matches)-3} weitere Matches")

        if detected_patterns:
            warnings.insert(0, f"🚨 INJECTION DETECTED: {len(detected_patterns)} Pattern-Typen gefunden")

        return warnings

    def _calculate_risk_level(self, warnings: List[str]) -> str:
        """Berechnet Risiko-Level basierend auf Warnungen"""
        # Count kritische Warnungen
        critical_count = sum(1 for w in warnings if '🚨' in w)
        warning_count = sum(1 for w in warnings if '⚠️' in w)

        if critical_count >= 3:
            return "CRITICAL"
        elif critical_count >= 1:
            return "HIGH"
        elif warning_count >= 5:
            return "MEDIUM"
        else:
            return "LOW"

    def _write_clean_text(self, text: str):
        """Schreibt bereinigten Text zu Output-Datei"""
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            self.warnings.append(f"⚠️ Schreiben fehlgeschlagen: {str(e)}")

    def _write_report(self, result: Dict[str, Any]):
        """Schreibt JSON-Report"""
        try:
            with open(self.report_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "pdf_path": str(self.pdf_path),
                    "output_path": str(self.output_path),
                    "result": result,
                    "metadata": self.metadata,
                    "structure_info": self.structure_info
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️ Report-Schreiben fehlgeschlagen: {str(e)}", file=sys.stderr)


def main():
    """CLI-Entry-Point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="PDF Security Validator - Deep Analysis für Prompt-Injection-Schutz",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
    # Einfache Validierung
    python3 scripts/pdf_security_validator.py input.pdf output.txt

    # Mit JSON-Report
    python3 scripts/pdf_security_validator.py input.pdf output.txt --report report.json

    # JSON-Output für Scripting
    python3 scripts/pdf_security_validator.py input.pdf output.txt --json
        """
    )

    parser.add_argument("pdf_path", help="Pfad zur Input-PDF")
    parser.add_argument("output_path", help="Pfad für bereinigten Text-Output")
    parser.add_argument("--report", help="Pfad für JSON-Report (optional)")
    parser.add_argument("--json", action="store_true", help="Output als JSON")

    args = parser.parse_args()

    # Validiere
    validator = PDFSecurityValidator(
        pdf_path=args.pdf_path,
        output_path=args.output_path,
        report_path=args.report
    )

    result = validator.validate()

    # Output
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        # Human-readable Output
        print(f"PDF Security Validation: {args.pdf_path}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Safe: {'✅ YES' if result['safe'] else '❌ NO'}")
        print(f"Text Length: {result['text_length']} chars")
        print(f"\nWarnings ({len(result['warnings'])}):")
        for warning in result['warnings']:
            print(f"  {warning}")

    # Exit code basierend auf Risk-Level
    if result['risk_level'] == "CRITICAL":
        sys.exit(2)
    elif result['risk_level'] == "HIGH":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
