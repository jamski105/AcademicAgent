#!/usr/bin/env python3
"""
Config Loader für Academic Agent v2.0
Lädt und validiert Konfiguration für Recherche-Runs
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ResearchConfig:
    """Recherche-Konfiguration"""
    mode: str  # quick, standard, deep
    max_papers: int
    max_sources: int
    estimated_duration_min: int
    pdf_download_enabled: bool
    api_sources: list[str]


class ConfigLoader:
    """Lädt und validiert Konfigurationsdateien"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_dir = project_root / "config"

    def load_research_modes(self) -> Dict[str, ResearchConfig]:
        """Lädt research_modes.yaml"""
        modes_file = self.config_dir / "research_modes.yaml"

        if not modes_file.exists():
            raise FileNotFoundError(
                f"research_modes.yaml nicht gefunden: {modes_file}\n"
                f"Erstelle die Datei mit Quick/Standard/Deep Mode Definitionen."
            )

        with open(modes_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        modes = {}
        for mode_name, config in data.get('modes', {}).items():
            modes[mode_name] = ResearchConfig(
                mode=mode_name,
                max_papers=config['max_papers'],
                max_sources=config['max_sources'],
                estimated_duration_min=config['estimated_duration_min'],
                pdf_download_enabled=config.get('pdf_download_enabled', True),
                api_sources=config.get('api_sources', ['crossref', 'openalex', 'semantic_scholar'])
            )

        return modes

    def load_academic_context(self) -> Optional[Dict]:
        """Lädt academic_context.md (optional)"""
        context_file = self.config_dir / "academic_context.md"

        if not context_file.exists():
            return None

        with open(context_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse Markdown für strukturierte Daten
        context = {
            'raw_content': content,
            'discipline': self._extract_field(content, 'Disziplin'),
            'keywords': self._extract_keywords(content),
            'preferred_databases': self._extract_databases(content)
        }

        return context

    def load_api_config(self) -> Dict:
        """Lädt api_config.yaml"""
        api_config_file = self.config_dir / "api_config.yaml"

        if not api_config_file.exists():
            # Default-Config zurückgeben
            return self._get_default_api_config()

        with open(api_config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def validate_research_input(self, query: str, mode: str) -> tuple[bool, Optional[str]]:
        """
        Validiert User-Input

        Returns:
            (is_valid, error_message)
        """
        # Query validieren
        if not query or len(query.strip()) < 3:
            return False, "Forschungsthema muss mindestens 3 Zeichen lang sein"

        if len(query) > 500:
            return False, "Forschungsthema ist zu lang (max. 500 Zeichen)"

        # Mode validieren
        modes = self.load_research_modes()
        if mode not in modes:
            available = ', '.join(modes.keys())
            return False, f"Unbekannter Modus '{mode}'. Verfügbar: {available}"

        return True, None

    def _extract_field(self, content: str, field_name: str) -> Optional[str]:
        """Extrahiert ein Feld aus Markdown"""
        for line in content.split('\n'):
            if line.startswith(f'**{field_name}:**') or line.startswith(f'## {field_name}'):
                # Nächste Zeile mit Inhalt finden
                idx = content.find(line)
                rest = content[idx + len(line):].strip()
                return rest.split('\n')[0].strip()
        return None

    def _extract_keywords(self, content: str) -> list[str]:
        """Extrahiert Keywords aus Markdown"""
        keywords = []
        in_keywords_section = False

        for line in content.split('\n'):
            if 'Keywords' in line or 'Schlüsselwörter' in line:
                in_keywords_section = True
                continue

            if in_keywords_section:
                if line.startswith('#') or line.startswith('**'):
                    break
                if line.strip().startswith('-'):
                    keyword = line.strip().lstrip('- ').strip()
                    if keyword:
                        keywords.append(keyword)

        return keywords

    def _extract_databases(self, content: str) -> list[str]:
        """Extrahiert bevorzugte Datenbanken"""
        databases = []
        in_db_section = False

        for line in content.split('\n'):
            if 'Datenbanken' in line or 'Databases' in line:
                in_db_section = True
                continue

            if in_db_section:
                if line.startswith('#') or line.startswith('**'):
                    break
                if line.strip().startswith('-'):
                    db = line.strip().lstrip('- ').strip()
                    if db:
                        databases.append(db)

        return databases

    def _get_default_api_config(self) -> Dict:
        """Default API-Konfiguration"""
        return {
            'rate_limits': {
                'crossref': {'requests_per_second': 50},
                'openalex': {'requests_per_second': 10},
                'semantic_scholar': {'requests_per_second': 10},
                'unpaywall': {'requests_per_second': 100},
                'core': {'requests_per_second': 10}
            },
            'timeouts': {
                'api_request': 30,
                'pdf_download': 60
            },
            'retry': {
                'max_attempts': 3,
                'backoff_factor': 2
            }
        }


def main():
    """Test-Funktion"""
    loader = ConfigLoader(Path.cwd())

    print("=== Research Modes ===")
    modes = loader.load_research_modes()
    for name, config in modes.items():
        print(f"{name}: {config.max_papers} papers, ~{config.estimated_duration_min} min")

    print("\n=== Academic Context ===")
    context = loader.load_academic_context()
    if context:
        print(f"Discipline: {context.get('discipline')}")
        print(f"Keywords: {context.get('keywords')}")
    else:
        print("Kein academic_context.md gefunden")

    print("\n=== API Config ===")
    api_config = loader.load_api_config()
    print(f"Rate Limits: {list(api_config['rate_limits'].keys())}")


if __name__ == '__main__':
    main()