# 🚨 Error Recovery Guide - Quick Reference

**Version:** 2.0
**Für:** AcademicAgent Nutzer

---

## 📋 Quick Commands

### Resume nach Unterbrechung
```bash
bash scripts/resume_research.sh [ProjectName]
```

### State prüfen
```bash
python3 scripts/state_manager.py load projects/[ProjectName]
```

### CDP-Verbindung testen
```bash
curl http://localhost:9222/json/version
```

### Chrome neu starten
```bash
bash scripts/start_chrome_debug.sh
```

---

## 🔥 Häufige Fehler & Lösungen

### 1. CDP Connection Error

**Symptome:**
```
❌ CDP Connection Error
Chrome DevTools Protocol ist nicht erreichbar
```

**Lösung:**
```bash
# Schritt 1: Prüfe ob Chrome läuft
lsof -i:9222

# Schritt 2: Wenn nicht → Starte Chrome
bash scripts/start_chrome_debug.sh

# Schritt 3: Warte 5 Sekunden
sleep 5

# Schritt 4: Teste
curl http://localhost:9222/json/version
```

**Agent wird automatisch Retry versuchen!**

---

### 2. CAPTCHA Detected

**Symptome:**
```
🚨 CAPTCHA erkannt!
Screenshot: logs/captcha_23.png
```

**Lösung:**
1. **Wechsle zum Chrome-Fenster**
2. **Löse das CAPTCHA manuell**
3. **Drücke ENTER im Terminal**

**Agent setzt automatisch fort!**

**Tipp:** Nach CAPTCHA wartet Agent 30 Sekunden bevor nächster Request.

---

### 3. Login Required

**Symptome:**
```
🔐 Login erforderlich!
URL: https://ieeexplore.ieee.org
```

**Lösung:**
1. **Wechsle zum Chrome-Fenster**
2. **Logge dich ein** (Uni-Account, VPN)
3. **Drücke ENTER im Terminal**

**Session bleibt erhalten für alle folgenden Requests!**

---

### 4. Rate Limit Exceeded

**Symptome:**
```
⏸️  Rate Limit erreicht!
Wartezeit: 60 Sekunden
```

**Lösung:**
- **Automatisch!** Agent wartet 60 Sekunden
- Countdown wird angezeigt
- Danach automatischer Retry

**Kein User-Input nötig.**

---

### 5. Network Error

**Symptome:**
```
🌐 Netzwerk-Fehler
Verbindung zu https://... fehlgeschlagen
```

**Lösung:**
```bash
# Prüfe Internetverbindung
ping google.com

# Prüfe VPN (für Uni-DBs)
# → VPN reconnect falls nötig

# Drücke ENTER zum Retry
```

**Agent versucht automatisch Retry.**

---

### 6. Recherche unterbrochen (Absturz, Cmd+C)

**Symptome:**
- Agent hat gestoppt
- Terminal geschlossen
- Chrome gecrasht

**Lösung:**
```bash
# 1. Prüfe wo du warst
bash scripts/resume_research.sh DevOps

# Output:
# 🔄 Resume möglich!
# Last completed: Phase 2
# Resume from Phase 3?

# 2. Chrome starten
bash scripts/start_chrome_debug.sh

# 3. VS Code + Claude Code Chat öffnen

# 4. Im Chat sagen:
Lies agents/orchestrator.md und setze die Recherche fort
für ~/AcademicAgent/config/Config_DevOps.md

WICHTIG: Starte bei Phase 3
```

**Agent überspringt Phase 0-2 automatisch!**

---

### 7. File Missing/Corrupt

**Symptome:**
```
📁 File Error
File: metadata/candidates.json
Type: missing
```

**Lösung:**

**Variante A: Wiederhole Phase**
```bash
# Starte von früherer Phase
# Im Chat:
Lies agents/orchestrator.md und starte bei Phase 2
```

**Variante B: Manuell erstellen**
```bash
# Für candidates.json
echo '{"candidates": []}' > projects/[ProjectName]/metadata/candidates.json

# Dann Phase wiederholen
```

---

## 🔄 Resume Workflow (Schritt-für-Schritt)

### Situation: Agent wurde unterbrochen

1. **Terminal öffnen**
   ```bash
   cd ~/Repos/AcademicAgent
   ```

2. **Prüfe State**
   ```bash
   bash scripts/resume_research.sh DevOps
   ```

   **Output interpretieren:**
   ```
   📊 State Summary:
     Phase 0: completed  ← Fertig
     Phase 1: completed  ← Fertig
     Phase 2: in_progress ← Hier weitermachen!
     Phase 3: pending

   Ready to resume!
   Resume from Phase 2?
   ```

3. **Chrome starten (falls nicht läuft)**
   ```bash
   bash scripts/start_chrome_debug.sh
   ```

4. **VS Code öffnen**
   ```bash
   code .
   ```

5. **Claude Code Chat starten**
   - `Cmd+Shift+P`
   - "Claude Code: Start Chat"

6. **Agent instruieren**
   ```
   Lies agents/orchestrator.md und setze die Recherche fort
   für ~/AcademicAgent/config/Config_DevOps.md

   WICHTIG: Starte bei Phase 2
   Phase 0-1 sind bereits abgeschlossen.
   ```

7. **Agent überspringt automatisch Phase 0-1 ✅**

---

## 📊 State-File verstehen

**Location:** `projects/[ProjectName]/metadata/research_state.json`

**Struktur:**
```json
{
  "project_name": "DevOps",
  "started_at": "2026-02-16T14:00:00",
  "current_phase": 2,
  "last_updated": "2026-02-16T15:30:00",
  "phases": {
    "phase_0": {
      "status": "completed",
      "updated_at": "2026-02-16T14:15:00",
      "data": {"databases_count": 8}
    },
    "phase_1": {
      "status": "completed",
      "updated_at": "2026-02-16T14:25:00",
      "data": {"search_strings_count": 30}
    },
    "phase_2": {
      "status": "in_progress",
      "updated_at": "2026-02-16T15:30:00",
      "data": {"progress": "15/30", "candidates": 22}
    }
  }
}
```

**Status-Werte:**
- `pending` - Phase nicht gestartet
- `in_progress` - Phase läuft
- `completed` - Phase erfolgreich abgeschlossen
- `failed` - Phase fehlgeschlagen
- `paused` - Phase pausiert (z.B. CAPTCHA)

---

## 🛠️ Debugging

### Agent hängt bei CDP-Befehl

```bash
# 1. Prüfe ob Chrome responsive ist
curl http://localhost:9222/json

# 2. Screenshot vom aktuellen State
node scripts/browser_cdp_helper.js screenshot /tmp/debug.png
open /tmp/debug.png

# 3. Chrome neu starten
kill $(lsof -t -i:9222)
bash scripts/start_chrome_debug.sh
```

---

### State zurücksetzen (Nuclear Option)

```bash
# Sichere State
cp projects/[ProjectName]/metadata/research_state.json \
   projects/[ProjectName]/metadata/research_state.backup

# Lösche State → Agent startet von vorn
rm projects/[ProjectName]/metadata/research_state.json

# Oder: Nur einzelne Phase zurücksetzen
python3 scripts/state_manager.py save \
  projects/[ProjectName] 2 "pending"
```

---

## 📞 Support

**Wenn nichts hilft:**

1. **State exportieren:**
   ```bash
   python3 scripts/state_manager.py load projects/[ProjectName] > state.json
   ```

2. **Logs sammeln:**
   ```bash
   tar -czf debug.tar.gz projects/[ProjectName]/logs/
   ```

3. **Issue erstellen:**
   - State: `state.json`
   - Logs: `debug.tar.gz`
   - Error-Message kopieren
   - GitHub Issue: https://github.com/dein-user/AcademicAgent/issues

---

**Happy Researching! 🚀**
