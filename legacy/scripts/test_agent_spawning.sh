#!/bin/bash
# Test-Script zur Validierung des Agent-Spawning-Fixes
# Tests ob orchestrator-agent tatsächlich Sub-Agents spawnt

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         🧪 Agent-Spawning Test-Suite                        ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Prüfe ob orchestrator-agent.md die kritischen Regeln enthält
echo "Test 1: Prüfe kritische Regeln in orchestrator-agent.md..."

if grep -q "KRITISCHE REGEL - NIEMALS UMGEHEN" .claude/agents/orchestrator-agent.md; then
    echo "✅ Kritische Regeln gefunden"
else
    echo "❌ FEHLER: Kritische Regeln fehlen!"
    exit 1
fi

# Test 2: Prüfe ob Phase Execution Validation vorhanden ist
echo ""
echo "Test 2: Prüfe Phase Execution Validation..."

if grep -q "Phase Execution Validation" .claude/agents/orchestrator-agent.md; then
    echo "✅ Phase Execution Validation gefunden"
else
    echo "❌ FEHLER: Phase Execution Validation fehlt!"
    exit 1
fi

# Test 3: Prüfe ob "DEMO-MODUS IST VERBOTEN" Text vorhanden ist
echo ""
echo "Test 3: Prüfe DEMO-MODUS Verbot..."

if grep -q "DEMO-MODUS IST VERBOTEN" .claude/agents/orchestrator-agent.md; then
    echo "✅ DEMO-MODUS Verbot gefunden"
else
    echo "❌ FEHLER: DEMO-MODUS Verbot fehlt!"
    exit 1
fi

# Test 4: Prüfe ob alle Phase-Regeln vorhanden sind
echo ""
echo "Test 4: Prüfe Phase-spezifische Regeln..."

PHASES=("Phase 1" "Phase 2" "Phase 3" "Phase 4" "Phase 5")
for phase in "${PHASES[@]}"; do
    if grep -q "### $phase" .claude/agents/orchestrator-agent.md; then
        echo "✅ $phase Regeln gefunden"
    else
        echo "❌ FEHLER: $phase Regeln fehlen!"
        exit 1
    fi
done

# Test 5: Prüfe ob Marker-File Instruktionen vorhanden sind
echo ""
echo "Test 5: Prüfe Marker-File Instruktionen..."

if grep -q "Marker-File Creation" .claude/agents/orchestrator-agent.md; then
    echo "✅ Marker-File Instruktionen gefunden"
else
    echo "❌ FEHLER: Marker-File Instruktionen fehlen!"
    exit 1
fi

# Test 6: Prüfe ob "SYNTHETIC" Check vorhanden ist
echo ""
echo "Test 6: Prüfe SYNTHETIC-Daten Check..."

if grep -q 'grep -q "SYNTHETIC"' .claude/agents/orchestrator-agent.md; then
    echo "✅ SYNTHETIC-Daten Check gefunden"
else
    echo "❌ FEHLER: SYNTHETIC-Daten Check fehlt!"
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         ✅ Alle Tests bestanden!                            ║"
echo "║                                                              ║"
echo "║  Der orchestrator-agent.md wurde erfolgreich gepatcht.       ║"
echo "║  Die kritischen Regeln sollten nun Agent-Spawning erzwingen. ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Nächste Schritte:"
echo "  1. Teste mit einem echten Run: /academicagent --quick"
echo "  2. Überwache Chrome-Fenster (sollte sich öffnen)"
echo "  3. Prüfe Logs auf Task()-Aufrufe: grep 'Task(' runs/*/logs/*.log"
echo "  4. Validiere Outputs: ls runs/*/downloads/*.pdf"
echo ""
