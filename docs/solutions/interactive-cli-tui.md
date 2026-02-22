# Lösung: Interaktives CLI mit Pfeiltasten (TUI)

**Problem:** User muss viel Text tippen, Chat wird unübersichtlich

**Ziel:** Navigation mit ↑↓ und ENTER, keine Chat-Messages nötig

---

## Design

### Beispiel-Flow

```
╔══════════════════════════════════════════╗
║   ACADEMIC AGENT - QUICK SETUP           ║
╚══════════════════════════════════════════╝

❓ Was ist deine Forschungsfrage?

  > Wie beeinflussen Lean Governance Prinzipien DevOps?
  ────────────────────────────────────────────────────

  [ENTER zum Bestätigen] [ESC zum Abbrechen]


╔══════════════════════════════════════════╗
║   KEYWORDS ERKANNT                        ║
╚══════════════════════════════════════════╝

Automatisch extrahiert:
  ✓ Lean Governance
  ✓ DevOps
  ✓ Agile
  ✓ Process Management

[ENTER zum Fortfahren]


╔══════════════════════════════════════════╗
║   KONFIGURATION                          ║
╚══════════════════════════════════════════╝

  → Modus: Quick (5 Zitate, schnell)
    Zeitraum: 2019-2026 (aus Context)
    Qualität: Streng (Peer-Review + 5 Cit.)
    Strategie: Iterativ

  [↑↓ zum Ändern] [ENTER zum Starten]


╔══════════════════════════════════════════╗
║   BEREIT ZUM START                       ║
╚══════════════════════════════════════════╝

  → Jetzt starten
    Konfiguration bearbeiten
    Abbrechen

  [↑↓ Navigation] [ENTER Auswahl]
```

---

## Implementation

### Option A: Bash mit `dialog` (Einfach)

```bash
#!/bin/bash
# scripts/interactive_setup.sh

# Check if dialog installed
if ! command -v dialog &> /dev/null; then
    echo "Installing dialog..."
    brew install dialog  # oder apt-get install dialog
fi

# 1. Forschungsfrage
QUESTION=$(dialog --title "Academic Agent Setup" \
    --inputbox "Was ist deine Forschungsfrage?" 10 60 \
    3>&1 1>&2 2>&3)

if [ $? -ne 0 ]; then
    exit 1  # ESC gedrückt
fi

# 2. Keywords anzeigen (automatisch extrahiert)
KEYWORDS=$(python3 scripts/extract_keywords.py "$QUESTION")
dialog --title "Keywords erkannt" \
    --msgbox "Automatisch extrahiert:\n\n$KEYWORDS\n\n[Diese werden verwendet]" 15 60

# 3. Konfig-Überblick
dialog --title "Konfiguration" \
    --yesno "Modus: Quick (5 Zitate)\nZeitraum: 2019-2026\nQualität: Streng\n\nJetzt starten?" 12 50

if [ $? -eq 0 ]; then
    # Start!
    /academicagent --quick --question "$QUESTION"
else
    # Custom Mode
    /academicagent --custom --question "$QUESTION"
fi
```

**Vorteile:**
- ✅ Native TUI
- ✅ Pfeiltasten, ENTER, ESC
- ✅ 50 Zeilen Code

**Nachteile:**
- ❌ Extra Dependency (dialog)
- ❌ Einfaches UI

---

### Option B: Python mit `questionary` (Modern)

```python
#!/usr/bin/env python3
# scripts/interactive_setup.py

import questionary
from questionary import Style

# Custom Style
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#0e639c bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('selected', 'fg:#0e639c'),
])

def main():
    print("╔══════════════════════════════════════════╗")
    print("║   ACADEMIC AGENT - QUICK SETUP           ║")
    print("╚══════════════════════════════════════════╝\n")

    # 1. Forschungsfrage
    question = questionary.text(
        "Was ist deine Forschungsfrage?",
        style=custom_style
    ).ask()

    if not question:
        return  # ESC gedrückt

    # 2. Keywords extrahieren und anzeigen
    keywords = extract_keywords(question)
    print(f"\n✓ Erkannt: {', '.join(keywords)}\n")

    # 3. Modus wählen (Optional)
    mode = questionary.select(
        "Modus wählen?",
        choices=[
            "Quick (5 Zitate, empfohlen)",
            "Standard (20 Zitate)",
            "Deep (50 Zitate)",
            "Custom (Alle Optionen)"
        ],
        default="Quick (5 Zitate, empfohlen)",
        style=custom_style
    ).ask()

    # 4. Zusammenfassung
    print("\n╔══════════════════════════════════════════╗")
    print("║   KONFIGURATION                          ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  Modus: {mode.split()[0]}")
    print(f"  Zeitraum: 2019-2026 (aus Context)")
    print(f"  Keywords: {len(keywords)} erkannt")
    print()

    # 5. Start bestätigen
    start = questionary.confirm(
        "Jetzt starten?",
        default=True,
        style=custom_style
    ).ask()

    if start:
        # Run orchestrator
        import subprocess
        subprocess.run([
            "claude", "code", "task",
            "--agent", "orchestrator-agent",
            "--prompt", f"Execute research for: {question}"
        ])

if __name__ == "__main__":
    main()
```

**Installation:**
```bash
pip3 install questionary
```

**Vorteile:**
- ✅ Modernes UI
- ✅ Farbig, schön formatiert
- ✅ Select, Confirm, Text, Multi-Select
- ✅ Einfach zu erweitern

**Nachteile:**
- ❌ Python Dependency

---

### Option C: Bash Pure (Kein Dependency)

```bash
#!/bin/bash
# scripts/interactive_setup_pure.sh

# Navigation mit Raw Terminal Input
select_option() {
    local options=("$@")
    local selected=0
    local key

    # Save terminal state
    exec < /dev/tty
    old_stty_cfg=$(stty -g)
    stty raw -echo

    while true; do
        # Clear and redraw
        clear
        echo "╔══════════════════════════════════════════╗"
        echo "║   Wähle eine Option (↑↓ + ENTER)        ║"
        echo "╚══════════════════════════════════════════╝"
        echo ""

        for i in "${!options[@]}"; do
            if [ $i -eq $selected ]; then
                echo "  → ${options[$i]}"
            else
                echo "    ${options[$i]}"
            fi
        done

        # Read key
        read -n 3 key

        case "$key" in
            $'\x1b[A')  # Up arrow
                ((selected--))
                [ $selected -lt 0 ] && selected=$((${#options[@]} - 1))
                ;;
            $'\x1b[B')  # Down arrow
                ((selected++))
                [ $selected -ge ${#options[@]} ] && selected=0
                ;;
            '')  # ENTER
                break
                ;;
        esac
    done

    # Restore terminal
    stty $old_stty_cfg
    echo "${options[$selected]}"
}

# Main Flow
clear
echo "╔══════════════════════════════════════════╗"
echo "║   ACADEMIC AGENT - SETUP                 ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. Forschungsfrage (normaler Input)
read -p "❓ Was ist deine Forschungsfrage? " QUESTION
echo ""

# 2. Keywords anzeigen
KEYWORDS=$(python3 -c "import sys; print('Lean Governance, DevOps, Agile')")
echo "✓ Keywords erkannt: $KEYWORDS"
echo ""
sleep 1

# 3. Modus wählen mit Pfeiltasten
MODE=$(select_option \
    "Quick (5 Zitate, empfohlen)" \
    "Standard (20 Zitate)" \
    "Deep (50 Zitate)")

echo ""
echo "✓ Gewählt: $MODE"
echo ""

# 4. Start bestätigen
START=$(select_option \
    "Jetzt starten" \
    "Konfiguration bearbeiten" \
    "Abbrechen")

if [[ "$START" == "Jetzt starten" ]]; then
    echo "🚀 Starte Recherche..."
    # Run orchestrator
else
    echo "Abgebrochen."
fi
```

**Vorteile:**
- ✅ Keine Dependencies
- ✅ Pure Bash
- ✅ Funktioniert überall

**Nachteile:**
- ❌ Komplex (Terminal-Handling)
- ❌ Weniger robust

---

## Integration in academicagent Skill

```bash
#!/bin/bash
# Integration in .claude/skills/academicagent/skill.sh (falls vorhanden)
# oder als Wrapper-Script

# Check if interactive mode requested
if [[ "$*" == *"--interactive"* ]] || [ -z "$*" ]; then
    # Use TUI - Starte Python Interactive Setup
    python3 scripts/interactive_setup.py
    exit $?
else
    # CLI mode - Direkt zum Setup-Agent delegieren
    # Das academicagent Skill übernimmt die normale Verarbeitung
    exit 0
fi
```

**Nutzung:**

```bash
# Interaktiv (TUI):
/academicagent

# CLI (alt):
/academicagent --cli --quick

# Direct:
/academicagent --question "..." --quick
```

---

## Empfehlung

**Option B: Python + questionary**

**Warum:**
- ✅ Modern und schön
- ✅ Einfach zu erweitern
- ✅ Robuster als Bash-Raw-Input
- ✅ Nur 1 Dependency (pip install)

**Implementation-Zeit:** 2-3 Stunden

**Quick Start:**

```bash
# 1. Install
pip3 install questionary

# 2. Create script
# (siehe Option B Code oben)

# 3. Test
python3 scripts/interactive_setup.py

# 4. Integration in Skill
# (siehe Integration oben)
```

---

## Features

### Must-Have
- ✅ Text-Input (Forschungsfrage)
- ✅ Select-Menu (Modus, Start/Abbruch)
- ✅ Auto-Preview (Keywords, Config)

### Nice-to-Have
- Multi-Select für Keywords (manuell hinzufügen/entfernen)
- Progress-Bar während Execution
- Live-Log-Tail im Terminal
- Resume-Menu (alte Runs anzeigen)

---

**Siehe auch:**
- [setup-agent-optimization.md](./setup-agent-optimization.md)
- [fix-permission-prompts.md](./fix-permission-prompts.md)
