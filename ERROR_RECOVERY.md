# 🚨 Error Recovery Guide

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
# 1. State prüfen
bash scripts/resume_research.sh

# Output:
# 🔄 Resume möglich!
# Last completed: Phase 2
# Resume from Phase 3?

# 2. Chrome starten
bash scripts/start_chrome_debug.sh

# 3. VS Code öffnen
code .

# 4. Im Claude Code Chat:
/orchestrator

# Agent fragt nach Config
# Agent erkennt State und überspringt Phase 0-2 automatisch
```

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
# State laden
python3 scripts/state_manager.py load runs/[Timestamp]

# State zurücksetzen (Nuclear Option)
rm runs/[Timestamp]/metadata/research_state.json
```

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
