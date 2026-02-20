#!/usr/bin/env python3
"""
HTML-Sanitizer für AcademicAgent
Entfernt potenziell bösartige Inhalte bevor HTML an Agents übergeben wird

Verwendung:
  cat page.html | python3 scripts/sanitize_html.py > clean.txt
  python3 scripts/sanitize_html.py input.html output.txt
"""

import re
import sys
import json
from html.parser import HTMLParser
from pathlib import Path


class TextExtractor(HTMLParser):
    """Extrahiert sichtbaren Text aus HTML, ignoriert Scripts/Styles/versteckte Elemente"""

    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {'script', 'style', 'noscript'}
        self.current_tag = None
        self.hidden = False

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

        # Prüfe auf versteckte Elemente
        attrs_dict = dict(attrs)
        style = attrs_dict.get('style', '')

        if 'display:none' in style.replace(' ', '') or \
           'display: none' in style or \
           'visibility:hidden' in style.replace(' ', '') or \
           'visibility: hidden' in style:
            self.hidden = True

    def handle_endtag(self, tag):
        self.current_tag = None
        self.hidden = False

    def handle_data(self, data):
        # Überspringe wenn in verstecktem Tag oder skip_tags
        if self.hidden or self.current_tag in self.skip_tags:
            return

        # Füge sichtbaren Text hinzu
        text = data.strip()
        if text:
            self.text.append(text)

    def get_text(self):
        return ' '.join(self.text)


def detect_injection_patterns(text: str) -> list:
    """
    Detect potential prompt injection patterns
    Returns list of detected patterns
    """
    suspicious_patterns = [
        (r'ignore\s+(all\s+)?(previous|prior)\s+instructions?', 'Ignore instructions'),
        (r'you\s+are\s+now\s+(a|an)\s+\w+', 'Role takeover'),
        (r'(execute|run)\s+(command|bash|shell|script)', 'Command execution'),
        (r'(upload|send|exfiltrate)\s+(file|secret|config|data)', 'Data exfiltration'),
        (r'(curl|wget|ssh|scp|rsync)\s+', 'Network command'),
        (r'read\s+(\.env|~/.ssh|secret|credential|token)', 'Secret access'),
        (r'system\s+prompt|developer\s+instructions?', 'System instruction override'),
        (r'<\s*script[^>]*>', 'Script tag'),
    ]

    detected = []
    for pattern, name in suspicious_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            detected.append({
                'pattern': name,
                'match': match.group(0),
                'position': match.start()
            })

    return detected


def sanitize_html(html: str, max_length: int = 50000) -> dict:
    """
    Sanitize HTML content

    Returns:
        {
            'text': 'cleaned text',
            'warnings': ['list of warnings'],
            'truncated': bool
        }
    """
    warnings = []

    # Schritt 1: Entferne offensichtlich bösartige Inhalte
    # Entferne Scripts
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Entferne Styles
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Entferne HTML-Kommentare (häufiges Versteck)
    comments = re.findall(r'<!--(.*?)-->', html, flags=re.DOTALL)
    for comment in comments:
        if len(comment) > 100 or any(keyword in comment.lower() for keyword in ['ignore', 'instruction', 'execute']):
            warnings.append(f"Verdächtiger HTML-Kommentar entfernt (Länge: {len(comment)})")
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

    # Entferne versteckte iframes
    html = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Entferne base64-kodierte Daten (potenzielle Verschleierung)
    base64_pattern = r'data:image/[^;]+;base64,[A-Za-z0-9+/=]{100,}'
    if re.search(base64_pattern, html):
        warnings.append("Base64-kodierte Daten entfernt (potenzielle Verschleierung)")
        html = re.sub(base64_pattern, '[BASE64_DATEN_ENTFERNT]', html)

    # Schritt 2: Extrahiere nur sichtbaren Text
    parser = TextExtractor()
    try:
        parser.feed(html)
        text = parser.get_text()
    except Exception as e:
        warnings.append(f"HTML-Parsing-Fehler: {str(e)}")
        # Fallback: einfache Textextraktion
        text = re.sub(r'<[^>]+>', ' ', html)
        text = ' '.join(text.split())

    # Schritt 3: Erkenne Injection-Versuche
    injections = detect_injection_patterns(text)
    if injections:
        warnings.append(f"⚠️  SICHERHEITSWARNUNG: {len(injections)} potenzielle Injection-Pattern erkannt")
        for inj in injections[:5]:  # Zeige erste 5
            warnings.append(f"  - {inj['pattern']}: '{inj['match'][:50]}...'")

    # Schritt 4: Begrenze Länge (verhindere Token-Flooding)
    truncated = False
    if len(text) > max_length:
        text = text[:max_length]
        truncated = True
        warnings.append(f"Text gekürzt auf {max_length} Zeichen")

    # Schritt 5: Entferne extrem lange Zeilen (potenzielles Flooding)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if len(line) > 1000:
            warnings.append(f"Lange Zeile gekürzt (Länge: {len(line)})")
            line = line[:1000] + "..."
        cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)

    return {
        'text': text,
        'warnings': warnings,
        'truncated': truncated,
        'injections_detected': len(injections)
    }


def main():
    """Haupt-Einstiegspunkt"""

    # Parse Argumente
    if len(sys.argv) == 1:
        # Lese von stdin
        html = sys.stdin.read()
        output_file = None
    elif len(sys.argv) == 2:
        # Lese von Datei, Ausgabe nach stdout
        input_file = Path(sys.argv[1])
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
        output_file = None
    elif len(sys.argv) == 3:
        # Lese von Datei, Ausgabe in Datei
        input_file = Path(sys.argv[1])
        output_file = Path(sys.argv[2])
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
    else:
        print("Verwendung:", file=sys.stderr)
        print("  cat page.html | python3 sanitize_html.py", file=sys.stderr)
        print("  python3 sanitize_html.py input.html", file=sys.stderr)
        print("  python3 sanitize_html.py input.html output.txt", file=sys.stderr)
        sys.exit(1)

    # Sanitisieren
    result = sanitize_html(html)

    # Gebe Warnungen nach stderr aus
    if result['warnings']:
        print("=== Sanitisierungs-Warnungen ===", file=sys.stderr)
        for warning in result['warnings']:
            print(warning, file=sys.stderr)
        print("", file=sys.stderr)

    # Gebe Result aus
    if output_file:
        # Schreibe Text in output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result['text'])
        print(f"✅ Sanitisierter Text geschrieben nach: {output_file}", file=sys.stderr)

        # Schreibe Metadaten
        metadata_file = output_file.with_suffix('.meta.json')
        with open(metadata_file, 'w') as f:
            json.dump({
                'warnings': result['warnings'],
                'truncated': result['truncated'],
                'injections_detected': result['injections_detected'],
                'output_length': len(result['text'])
            }, f, indent=2)
    else:
        # Output JSON to stdout
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
