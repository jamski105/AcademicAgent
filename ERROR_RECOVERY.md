# 🚨 Fehlerbehandlungs-Anleitung

Quick-Referenz für Fehlerbehandlung und Resume-Funktionalität.

---

## 🔥 Häufige Fehler & Schnelllösungen

### 1. CDP Connection Error

**Symptom:** `❌ Chrome DevTools Protocol ist nicht erreichbar`

**Lösung:**

```bash
# Chrome neu starten
bash scripts/start_chrome_debug.sh

# Teste Verbindung
curl http://localhost:9222/json/version
```

---

### 2. CAPTCHA Detected

**Symptom:** Agent zeigt CAPTCHA-Screenshot

**Lösung:**
1. Wechsle zum Chrome-Fenster
2. Löse das CAPTCHA manuell
3. Drücke ENTER im Chat/Terminal

→ Agent setzt automatisch fort!

---

### 3. Login Required

**Symptom:** `🔐 Login erforderlich`

**Lösung:**
1. Wechsle zum Chrome-Fenster
2. Logge dich ein (Uni-Account, VPN)
3. Drücke ENTER

→ Session bleibt für alle folgenden Requests erhalten!

---

### 4. Rate Limit Exceeded

**Symptom:** `⏸️  Rate Limit erreicht!`

**Lösung:** Automatisch! Agent wartet 60 Sekunden und versucht Retry.

---

### 5. Network Error

**Symptom:** `🌐 Netzwerk-Fehler`

**Lösung:**

```bash
# Prüfe Internetverbindung
ping google.com

# Prüfe VPN (für Uni-DBs)
# → VPN reconnect falls nötig

# Drücke ENTER zum Retry
```

---

### 6. Recherche unterbrochen

**Symptom:** Agent gestoppt, Terminal geschlossen, Chrome gecrasht

**Lösung:**

```bash
# 1. State validieren (zeigt letzte abgeschlossene Phase)
python3 scripts/validate_state.py runs/[Timestamp]/metadata/research_state.json

# Output:
# ✅ State valid
# Last completed: Phase 2 (completed)
# Next: Phase 3 (pending)
# Checksum: OK

# 2. Chrome starten
bash scripts/start_chrome_debug.sh

# 3. VS Code öffnen
code .

# 4. Im Claude Code Chat:
/academicagent

# Agent fragt nach Config → gib Pfad zum run-Ordner an
# Agent validiert State automatisch und überspringt Phase 0-2
```

**Alternative: Schnellcheck ohne Details**

```bash
# Zeigt nur ob Resume möglich ist
bash scripts/resume_research.sh
```

---

## 🩺 CDP Health Monitor

Der Orchestrator startet automatisch einen Background-Monitor während der Recherche:

### Was macht der Monitor?

```bash
# Automatisch gestartet vom Orchestrator (läuft im Hintergrund)
bash scripts/cdp_health_check.sh monitor 300 --run-dir runs/[Timestamp]

# Alle 5 Minuten:
# 1. Prüft CDP-Verbindung (localhost:9222)
# 2. Prüft Chrome-Memory (warnt bei >2GB)
# 3. Startet Chrome neu bei Crash
# 4. Loggt Status in runs/[Timestamp]/logs/cdp_health.log
```

### Manuell nutzen

**Status prüfen:**

```bash
# Einmalige Prüfung
bash scripts/cdp_health_check.sh check

# Output:
# ✅ CDP ist erreichbar
# Chrome PID: 12345
# Memory: 850 MB
```

**Chrome neu starten:**

```bash
# Stoppt Chrome und startet neu mit CDP
bash scripts/cdp_health_check.sh restart
```

**Monitor manuell starten:**

```bash
# Überwachung im Hintergrund (alle 5 Min)
bash scripts/cdp_health_check.sh monitor 300 &

# Monitor beenden
pkill -f "cdp_health_check.sh monitor"
```

### Troubleshooting

| Problem | Lösung |
|---------|--------|
| Monitor läuft nicht | Agent startet automatisch - kein manueller Start nötig |
| Chrome startet nicht neu | `bash scripts/start_chrome_debug.sh` manuell ausführen |
| Memory-Warnung | Chrome neu starten: `bash scripts/cdp_health_check.sh restart` |

---

## 🔄 Resume Workflow

### State-File verstehen

**Location:** `runs/[Timestamp]/metadata/research_state.json`

**Struktur:**

```json
{
  "current_phase": 2,
  "phases": {
    "phase_0": {"status": "completed"},
    "phase_1": {"status": "completed"},
    "phase_2": {"status": "in_progress"}
  }
}
```

**Status-Werte:**
- `pending` - Nicht gestartet
- `in_progress` - Läuft
- `completed` - Erfolgreich
- `failed` - Fehlgeschlagen

---

## 🛠️ Debug Commands

### Chrome-Status prüfen

```bash
# CDP-Verbindung testen
curl http://localhost:9222/json/version

# Chrome-Prozesse finden
lsof -i:9222

# Screenshot vom aktuellen State
node scripts/browser_cdp_helper.js screenshot /tmp/debug.png
open /tmp/debug.png
```

### State-Management

```bash
# State validieren (zeigt Details + prüft Integrität)
python3 scripts/validate_state.py runs/[Timestamp]/metadata/research_state.json

# Checksum hinzufügen (für Integritätsprüfung)
python3 scripts/validate_state.py runs/[Timestamp]/metadata/research_state.json --add-checksum

# State laden (zeigt nur Phasen-Status)
python3 scripts/state_manager.py load runs/[Timestamp]

# State manuell speichern (wird normalerweise automatisch gemacht)
python3 scripts/state_manager.py save runs/[Timestamp] <phase> <status>
# Beispiel:
python3 scripts/state_manager.py save runs/2026-02-17_14-30-00 2 completed

# State zurücksetzen (Nuclear Option - nur bei Korruption)
rm runs/[Timestamp]/metadata/research_state.json
# Dann: /academicagent neu starten (startet von Phase 0)
```

**Wichtig:** `validate_state.py` ist primär für Resume - prüft Integrität und zeigt nächste Phase!

---

## 📊 Error Recovery Strategien

Der Agent wendet automatisch diese Strategien an:

| Error Type | Strategie | User-Action |
|------------|-----------|-------------|
| CDP Connection | Chrome neu starten → Retry | Keine |
| CAPTCHA | Pause → User löst → Retry | CAPTCHA lösen |
| Login | Pause → User loggt ein → Retry | Einloggen |
| Rate Limit | Warten 60s → Retry | Keine |
| Network | User prüft VPN → Retry | VPN prüfen |

---

## 🆘 Wenn nichts hilft

1. **State exportieren:**
   ```bash
   python3 scripts/state_manager.py load runs/[Timestamp] > state.json
   ```

2. **Logs sammeln:**
   ```bash
   tar -czf debug.tar.gz runs/[Timestamp]/logs/
   ```

3. **Issue erstellen:**
   - Anhängen: `state.json` + `debug.tar.gz`
   - Error-Message kopieren
   - GitHub Issues: [Link]

---

**Happy Researching! 🚀**
