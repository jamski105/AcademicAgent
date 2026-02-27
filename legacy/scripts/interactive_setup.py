#!/usr/bin/env python3
"""
Interactive TUI Setup für Academic Agent
Verwendet questionary für moderne, benutzerfreundliche Eingaben
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import questionary
    from questionary import Style
except ImportError:
    print("❌ questionary nicht installiert!")
    print("\nInstalliere mit:")
    print("  pip3 install questionary")
    sys.exit(1)

# Custom Style für Academic Agent
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),          # Fragezeichen
    ('question', 'bold'),                   # Frage-Text
    ('answer', 'fg:#0e639c bold'),         # Gewählte Antwort
    ('pointer', 'fg:#673ab7 bold'),        # Pfeil-Pointer
    ('selected', 'fg:#0e639c'),            # Ausgewähltes Item
    ('highlighted', 'fg:#673ab7 bold'),    # Hervorgehobenes Item
])


def print_header():
    """Zeige Welcome-Header"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║           🎓 Academic Agent - Quick Setup (TUI)              ║")
    print("║                                                              ║")
    print("║                        Version 4.0                           ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")


def load_academic_context():
    """Lade academic_context.md wenn vorhanden"""
    context_path = Path("config/academic_context.md")

    if not context_path.exists():
        return None

    try:
        with open(context_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Einfaches Parsing - extrahiere Keywords
        context = {
            'has_context': True,
            'keywords': [],
            'field': None
        }

        # Suche nach Keywords-Sektion
        for line in content.split('\n'):
            if 'Keywords:' in line or 'keywords:' in line:
                # Extrahiere Keywords nach dem Doppelpunkt
                keywords_part = line.split(':', 1)[1].strip()
                context['keywords'] = [k.strip() for k in keywords_part.split(',') if k.strip()]
            elif 'Fachgebiet:' in line or 'Field:' in line:
                context['field'] = line.split(':', 1)[1].strip()

        return context
    except Exception as e:
        print(f"⚠️  Fehler beim Laden von academic_context.md: {e}")
        return None


def extract_keywords_from_question(question):
    """
    Einfache Keyword-Extraktion aus der Forschungsfrage
    Entfernt Stopwords und extrahiert relevante Begriffe
    """
    # Deutsche und englische Stopwords
    stopwords = {
        'wie', 'was', 'der', 'die', 'das', 'und', 'oder', 'aber',
        'in', 'auf', 'für', 'mit', 'zu', 'von', 'ist', 'sind',
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'for',
        'with', 'to', 'from', 'is', 'are', 'how', 'what', 'does'
    }

    # Entferne Fragezeichen und teile in Wörter
    words = question.replace('?', '').split()

    # Extrahiere Begriffe (länger als 3 Zeichen, keine Stopwords)
    keywords = []
    for word in words:
        cleaned = word.strip('.,;:!()[]{}').lower()
        if len(cleaned) > 3 and cleaned not in stopwords:
            # Großschreibung beibehalten wenn Original großgeschrieben
            if word[0].isupper():
                keywords.append(word.strip('.,;:!()[]{}'))
            else:
                keywords.append(cleaned)

    return keywords[:8]  # Maximal 8 Keywords


def get_mode_config(mode_choice):
    """Gebe Konfig-Parameter basierend auf gewähltem Modus zurück"""
    mode_configs = {
        "Quick": {
            "citations_target": 5,
            "databases_count": 3,
            "estimated_time": "30-45 Min",
            "quality_threshold": 5
        },
        "Standard": {
            "citations_target": 20,
            "databases_count": 5,
            "estimated_time": "1-2 Stunden",
            "quality_threshold": 10
        },
        "Deep": {
            "citations_target": 50,
            "databases_count": 8,
            "estimated_time": "3-5 Stunden",
            "quality_threshold": 20
        }
    }

    mode_name = mode_choice.split()[0]  # "Quick (5 Zitate)" -> "Quick"
    return mode_configs.get(mode_name, mode_configs["Quick"])


def create_run_config(question, keywords, mode, context):
    """Erstelle run_config.json basierend auf User-Inputs"""

    # Generiere Run-ID
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = Path(f"runs/{run_id}")
    run_dir.mkdir(parents=True, exist_ok=True)

    # Hole Mode-Config
    mode_config = get_mode_config(mode)

    # Baue Konfig
    config = {
        "run_id": run_id,
        "research_question": question,
        "keywords": keywords,
        "mode": mode.split()[0],
        "citations_target": mode_config["citations_target"],
        "databases": {
            "max_count": mode_config["databases_count"],
            "selection_strategy": "iterative",
            "initial_batch": 5
        },
        "quality": {
            "min_citations": mode_config["quality_threshold"],
            "peer_review_required": True
        },
        "time_range": {
            "start_year": 2019,
            "end_year": datetime.now().year
        },
        "strategy": "iterative",
        "created_at": datetime.now().isoformat(),
        "academic_context": context.get('field', 'General') if context else 'General'
    }

    # Speichere Konfig
    config_path = run_dir / "run_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return run_id, config_path


def spawn_orchestrator(run_id):
    """Starte den orchestrator-agent via claude code task"""
    print(f"\n🚀 Starte Recherche-Pipeline für Run: {run_id}\n")

    try:
        # Rufe claude code task auf
        cmd = [
            "claude", "code", "task",
            "--subagent-type", "orchestrator-agent",
            "--description", f"Run research pipeline for {run_id}",
            "--prompt", f"""Führe die vollständige Recherche-Pipeline aus.

Run ID: {run_id}
Konfig: runs/{run_id}/run_config.json

Verwende die iterative Datenbanksuche-Strategie aus der Konfig.

Phasenablauf:
1. Datenbank-Identifikation (oder überspringe falls bereits ausgewählt)
2. Suchstring-Generierung
3. Iterative Datenbanksuche
4. Screening & Ranking
5. PDF-Download
6. Zitat-Extraktion
7. Finalisierung

WICHTIG:
- Verwende run_config.json als Wahrheitsquelle
- Implementiere iterative Suche mit vorzeitiger Terminierung
- Speichere State nach jeder Iteration
"""
        ]

        result = subprocess.run(cmd, check=True)
        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Fehler beim Starten des Orchestrators: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ 'claude code' Befehl nicht gefunden!")
        print("Bitte stelle sicher, dass Claude Code CLI installiert ist.")
        return False


def main():
    """Hauptfunktion - Interaktiver Setup-Flow"""

    print_header()

    # Lade Context wenn vorhanden
    context = load_academic_context()

    if context and context.get('has_context'):
        print("✓ Akademischer Kontext gefunden")
        if context.get('field'):
            print(f"  Fachgebiet: {context['field']}")
        if context.get('keywords'):
            print(f"  Basis-Keywords: {', '.join(context['keywords'][:3])}")
        print()

    # 1. Forschungsfrage
    question = questionary.text(
        "Was ist deine Forschungsfrage?",
        style=custom_style,
        validate=lambda text: len(text.strip()) > 10 or "Bitte gib eine aussagekräftige Forschungsfrage ein (min. 10 Zeichen)"
    ).ask()

    if not question:
        print("\n❌ Setup abgebrochen.")
        return 1

    # 2. Keywords automatisch extrahieren
    print("\n🔍 Extrahiere Keywords...")
    auto_keywords = extract_keywords_from_question(question)

    # Kombiniere mit Context-Keywords wenn vorhanden
    if context and context.get('keywords'):
        auto_keywords = list(set(auto_keywords + context['keywords']))

    print(f"\n✓ Erkannte Keywords: {', '.join(auto_keywords[:5])}")
    if len(auto_keywords) > 5:
        print(f"  (+ {len(auto_keywords) - 5} weitere)")
    print()

    # Optional: Nutzer kann Keywords anpassen
    edit_keywords = questionary.confirm(
        "Möchtest du die Keywords bearbeiten?",
        default=False,
        style=custom_style
    ).ask()

    keywords = auto_keywords
    if edit_keywords:
        keywords_str = questionary.text(
            "Keywords (komma-separiert):",
            default=", ".join(auto_keywords),
            style=custom_style
        ).ask()
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]

    # 3. Modus wählen
    mode = questionary.select(
        "Welchen Recherche-Modus möchtest du verwenden?",
        choices=[
            "Quick (5 Zitate, empfohlen für Tests)",
            "Standard (20 Zitate, für normale Recherchen)",
            "Deep (50 Zitate, für umfassende Literaturreviews)"
        ],
        default="Quick (5 Zitate, empfohlen für Tests)",
        style=custom_style
    ).ask()

    if not mode:
        print("\n❌ Setup abgebrochen.")
        return 1

    # 4. Zusammenfassung anzeigen
    mode_config = get_mode_config(mode)

    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║                   KONFIGURATION                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"  Modus:           {mode.split()[0]}")
    print(f"  Ziel-Zitate:     {mode_config['citations_target']}")
    print(f"  Datenbanken:     ~{mode_config['databases_count']}")
    print(f"  Keywords:        {len(keywords)} erkannt")
    print(f"  Zeitraum:        2019-{datetime.now().year}")
    print(f"  Geschätzte Zeit: {mode_config['estimated_time']}")
    print()

    # 5. Start bestätigen
    start = questionary.confirm(
        "Möchtest du jetzt starten?",
        default=True,
        style=custom_style
    ).ask()

    if not start:
        print("\n❌ Setup abgebrochen.")
        return 1

    # 6. Konfig erstellen
    print("\n📝 Erstelle Run-Konfiguration...")
    run_id, config_path = create_run_config(question, keywords, mode, context)

    print(f"✓ Konfiguration gespeichert: {config_path}")
    print(f"✓ Run ID: {run_id}")

    # 7. Orchestrator starten
    success = spawn_orchestrator(run_id)

    if success:
        print("\n✅ Recherche erfolgreich abgeschlossen!")
        print(f"\n📁 Ergebnisse unter: runs/{run_id}/")
        return 0
    else:
        print("\n⚠️  Recherche mit Fehlern beendet.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Setup durch User abgebrochen (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
