# 🚀 Quick Start: Interaktiver TUI-Modus

## In 3 Schritten zur Recherche

### 1️⃣ Starte den Wrapper

```bash
cd /path/to/AcademicAgent
bash scripts/academicagent_wrapper.sh
```

### 2️⃣ Wähle "Interaktiver Modus"

```
Deine Wahl [1-3]: 1
```

### 3️⃣ Beantworte 3-4 Fragen

- **Forschungsfrage**: Deine Hauptfrage
- **Keywords**: (automatisch erkannt, optional editierbar)
- **Modus**: Quick / Standard / Deep
- **Start**: Bestätigen

**Das war's!** 🎉

---

## Noch schneller: Direkt-Start

```bash
bash scripts/academicagent_wrapper.sh --interactive
```

---

## Installation (einmalig)

Falls `questionary` nicht installiert ist:

```bash
pip3 install questionary
```

*(Der Wrapper installiert es automatisch beim ersten Start)*

---

## Beispiel-Session

```
╔══════════════════════════════════════════════════════════════╗
║           🎓 Academic Agent - Quick Setup (TUI)              ║
╚══════════════════════════════════════════════════════════════╝

? Was ist deine Forschungsfrage?
  → Wie beeinflussen Lean Governance Prinzipien DevOps-Teams?

🔍 Extrahiere Keywords...
✓ Erkannte Keywords: Lean, Governance, Prinzipien, DevOps, Teams

? Welchen Recherche-Modus möchtest du verwenden?
  → Quick (5 Zitate, empfohlen für Tests)

╔══════════════════════════════════════════════════════════════╗
║                   KONFIGURATION                              ║
╚══════════════════════════════════════════════════════════════╝
  Modus:           Quick
  Ziel-Zitate:     5
  Keywords:        5 erkannt
  Geschätzte Zeit: 30-45 Min

? Möchtest du jetzt starten? Yes

📝 Erstelle Run-Konfiguration...
✓ Run ID: 2026-02-22_14-30-00

🚀 Starte Recherche-Pipeline...
```

---

## Vergleich: Vorher vs. Nachher

### ❌ Vorher (Chat-Modus)

```
User: /academicagent
Agent: Willkommen! Was ist deine Forschungsfrage?
User: Wie beeinflussen Lean Governance Prinzipien DevOps-Teams?
Agent: Verstanden. Welche Keywords möchtest du verwenden?
User: Lean, Governance, DevOps
Agent: Wie viele Zitate benötigst du?
User: 5
Agent: Welcher Zeitraum?
User: 2019-2026
... (10+ weitere Messages)
```

**⏱️ Setup-Zeit**: 3-5 Minuten

### ✅ Nachher (TUI-Modus)

```bash
bash scripts/academicagent_wrapper.sh --interactive
```

1. Forschungsfrage eingeben ↵
2. Modus wählen ↑↓ ↵
3. Bestätigen ↵

**⏱️ Setup-Zeit**: 1-2 Minuten

**💾 Ersparnis**: 50-60% weniger Zeit, 80% weniger Tippen!

---

## Hilfe & Support

- **Vollständige Doku**: [docs/features/interactive-tui-mode.md](features/interactive-tui-mode.md)
- **Original-Konzept**: [docs/solutions/interactive-cli-tui.md](solutions/interactive-cli-tui.md)
- **Skill-Integration**: [.claude/skills/academicagent/SKILL.md](../.claude/skills/academicagent/SKILL.md)

**Probleme?**
```bash
# Test Syntax
bash -n scripts/academicagent_wrapper.sh
python3 -m py_compile scripts/interactive_setup.py

# Install Dependencies
pip3 install questionary

# Fallback: Chat-Modus
bash scripts/academicagent_wrapper.sh --cli
```

---

**Happy Researching!** 🎓📚
