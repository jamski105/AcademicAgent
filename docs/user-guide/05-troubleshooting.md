# 🔧 Probleme lösen (Troubleshooting)

In diesem Kapitel findest du Lösungen für häufige Probleme und lernst, wie du Recherchen fortsetzen kannst.

## Schnell-Diagnose

Wenn etwas nicht funktioniert, prüfe zuerst:

```bash
# 1. Chrome läuft und ist erreichbar?
curl http://localhost:9222/json/version

# 2. VPN-Verbindung aktiv?
# (Teste im Browser ob du auf IEEE/ACM zugreifen kannst)

# 3. API-Key konfiguriert?
echo $ANTHROPIC_API_KEY
# Sollte: sk-ant-... anzeigen
```

---

## Chrome-Verbindungsprobleme

### Problem: "CDP connection failed"

**Fehlermeldung:**
```
Error: Could not connect to Chrome DevTools Protocol
Target closed
Connection refused at localhost:9222
```

**Ursachen & Lösungen:**

#### Lösung 1: Chrome neu starten

```bash
# Chrome-Prozess beenden
pkill -f "Google Chrome.*remote-debugging-port"

# 3 Sekunden warten
sleep 3

# Chrome neu starten
bash scripts/start_chrome_debug.sh

# Warte 5 Sekunden bis Chrome bereit ist
sleep 5

# Verbindung testen
curl http://localhost:9222/json/version
```

**Erwartete Ausgabe:**
```json
{
   "Browser": "Chrome/121.0.6167.85",
   "Protocol-Version": "1.3",
   ...
}
```

#### Lösung 2: Port-Konflikt prüfen

Vielleicht blockiert ein anderer Prozess Port 9222:

```bash
# Prüfe welcher Prozess Port 9222 nutzt
lsof -i :9222

# Wenn ein anderer Prozess läuft (nicht Chrome), beende ihn:
kill -9 [PID]

# Dann Chrome neu starten
bash scripts/start_chrome_debug.sh
```

#### Lösung 3: Manueller Chrome-Start

Falls das Script nicht funktioniert:

```bash
# macOS:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --no-first-run \
  --no-default-browser-check \
  --user-data-dir="/tmp/chrome-debug" &

# Linux:
google-chrome \
  --remote-debugging-port=9222 \
  --no-first-run \
  --no-default-browser-check \
  --user-data-dir="/tmp/chrome-debug" &
```

### Problem: Chrome stürzt ab während der Recherche

**Symptome:**
- Recherche stoppt plötzlich in Phase 2
- "Target closed" Fehler
- Chrome-Fenster ist weg

**Ursachen:**
- Zu viele offene Tabs (Speicher voll)
- System-Sleep/Suspend
- Chrome-Update

**Lösung: Automatische Wiederherstellung**

AcademicAgent hat einen CDP-Health-Monitor der Chrome automatisch neu startet:

```bash
# Prüfe Health-Monitor-Logs
tail -f runs/[Timestamp]/logs/cdp_health.log
```

**Du siehst:**
```
[14:23:15] CDP health check: OK
[14:28:15] CDP health check: OK
[14:33:15] CDP health check: FAILED - Restarting Chrome...
[14:33:20] Chrome restarted successfully
[14:33:25] CDP health check: OK
```

**Manueller Restart während laufender Recherche:**

Wenn der Auto-Restart nicht funktioniert:

```bash
# 1. Chrome neu starten (in separatem Terminal)
bash scripts/start_chrome_debug.sh

# 2. Recherche wird automatisch fortgesetzt
# (Agent merkt nach ~30 Sekunden dass Chrome wieder da ist)
```

---

## VPN-Probleme

### Problem: "Access Denied" bei Datenbank-Zugriff

**Fehlermeldung:**
```
Error accessing IEEE Xplore:
403 Forbidden - Institutional access required
```

**Ursache:** VPN-Verbindung nicht aktiv oder falsch konfiguriert.

**Lösung:**

#### Schritt 1: VPN-Verbindung prüfen

```bash
# macOS: Prüfe VPN-Status in Systemeinstellungen
# Oder teste Zugriff im Browser:
open https://ieeexplore.ieee.org

# Kannst du auf Papers zugreifen?
# Ja → VPN funktioniert
# Nein → VPN-Verbindung herstellen
```

#### Schritt 2: VPN-Konfiguration für CLI

Manche VPN-Clients erlauben CLI-Zugriff nicht automatisch:

```bash
# Teste ob curl über VPN geht:
curl -I https://ieeexplore.ieee.org

# Wenn 403 → VPN-Split-Tunneling deaktivieren
# (In VPN-Client-Einstellungen)
```

#### Schritt 3: Alternative - Browser-basierte VPN

Falls VPN-Client problematisch:
1. Nutze Browser-Extension (z.B. Cisco AnyConnect Browser)
2. Stelle sicher Chrome im Debug-Modus nutzt die Extension

### Problem: VPN-Verbindung bricht während Recherche ab

**Symptome:**
- Recherche läuft, dann plötzlich 403-Fehler
- Nur bei lizenzierten Datenbanken

**Lösung: VPN-Keepalive**

```bash
# macOS: Verhindere Standby während Recherche
caffeinate -d -i -m -u &

# Linux: Ähnlich mit systemd-inhibit
systemd-inhibit --what=idle:sleep --who="AcademicAgent" --why="Research running" &
```

**VPN-Reconnect Script:**

Erstelle ein Script das VPN automatisch reconnected:

```bash
# vpn_keepalive.sh
#!/bin/bash
while true; do
  sleep 300  # Alle 5 Minuten
  # Teste VPN-Verbindung
  if ! curl -s -I https://ieeexplore.ieee.org | grep -q "200 OK"; then
    echo "VPN down, reconnecting..."
    # Passe an deinen VPN-Client an:
    # /opt/cisco/anyconnect/bin/vpn connect [PROFIL]
  fi
done
```

---

## Login-Anforderungen

### Problem: Datenbank verlangt Login

**Symptome:**
- Browser zeigt Shibboleth/SAML Login-Seite
- "Authentication required" Fehler
- Recherche pausiert

**Lösung: Manuelles Login**

AcademicAgent kann Login-Flows nicht automatisch handhaben (Sicherheit!).

**Vorgehen:**

1. **Recherche pausiert automatisch** und zeigt:
   ```
   ⚠️  Login required for: SpringerLink

   Bitte:
   1. Öffne das Chrome-Debug-Fenster
   2. Logge dich manuell ein
   3. Wenn eingeloggt, tippe 'continue' hier
   ```

2. **Wechsle zum Chrome-Fenster**
   - Das Chrome-Debug-Fenster sollte offen sein
   - Du siehst die Login-Seite

3. **Logge dich ein**
   - Nutze deine Uni-Credentials
   - Shibboleth/SAML durchlaufen
   - Warte bis du die Datenbank-Startseite siehst

4. **Fortsetzung bestätigen**
   - Zurück zum VS Code Chat
   - Tippe: `continue`
   - Recherche läuft weiter

**Tipp:** Login bleibt für die Session aktiv (mehrere Datenbanken).

### Problem: Multi-Factor Authentication (MFA)

**Symptome:**
- Login verlangt 2FA-Code
- SMS/App-Bestätigung nötig

**Lösung:**

Wie oben, aber:
1. Recherche pausiert bei Login-Seite
2. Du gibst 2FA-Code im Chrome-Fenster ein
3. Nach erfolgreichem Login → `continue` tippen

**Wichtig:** AcademicAgent kann 2FA nicht umgehen (das ist gut so!).

---

## CAPTCHA-Handling

### Problem: CAPTCHA erscheint

**Symptome:**
- "Please verify you are human"
- reCAPTCHA-Challenge
- Cloudflare-Check

**Ursache:** Datenbank erkennt automatisierten Zugriff (Rate-Limiting).

**Lösung: Manuelle CAPTCHA-Lösung**

1. **Recherche pausiert automatisch:**
   ```
   ⚠️  CAPTCHA detected on: Google Scholar

   Bitte löse das CAPTCHA im Chrome-Fenster
   und tippe dann 'continue'
   ```

2. **Wechsle zu Chrome** und löse das CAPTCHA

3. **Tippe `continue`** im VS Code Chat

**Prävention:**

```markdown
## In deiner Konfig: Aggressive Datenbanken ausschließen

### Ausgeschlossene Datenbanken
Google Scholar
```

Google Scholar hat strenge Rate Limits → oft CAPTCHAs.

---

## Recherche fortsetzen nach Unterbrechung

### Problem: Terminal geschlossen / Crash / Neustart

**Symptome:**
- Recherche war bei Phase 3
- Jetzt ist alles weg
- Du möchtest nicht von vorne anfangen

**Lösung: State-basierte Fortsetzung**

AcademicAgent speichert automatisch den State nach jeder Phase!

#### Schritt 1: State validieren

```bash
# Finde dein Run-Verzeichnis
ls -lt runs/
# Neuestes = deine unterbrochene Recherche

# Prüfe State
python3 scripts/validate_state.py runs/2026-02-18_14-30-00/metadata/research_state.json
```

**Ausgabe:**
```
✅ State valid!

Current state:
- Last completed phase: Phase 2 (Database Search)
- Next pending phase: Phase 3 (Scoring & Ranking)
- Candidates found: 52
- Checksum: Valid
- Can resume: YES
```

#### Schritt 2: Chrome neu starten

```bash
bash scripts/start_chrome_debug.sh
```

#### Schritt 3: Recherche fortsetzen

In VS Code Claude Code Chat:

```
/academicagent
```

Agent erkennt den State automatisch:

```
Agent: Ich habe einen unterbrochenen Recherche-State gefunden:

Run: 2026-02-18_14-30-00
Zuletzt abgeschlossen: Phase 2 (Database Search)
52 Kandidaten gefunden

Möchtest du fortsetzen? (ja/nein)
```

Antworte mit **"ja"** und die Recherche startet bei Phase 3!

### Problem: State ist korrumpiert

**Fehlermeldung:**
```
❌ State corrupted!
Checksum mismatch
```

**Ursache:** Datei wurde während Schreibvorgang unterbrochen.

**Lösung: Backup-State wiederherstellen**

```bash
# AcademicAgent erstellt Backups nach jeder Phase
ls runs/2026-02-18_14-30-00/metadata/

# Du siehst:
# research_state.json
# research_state.json.backup_phase_2
# research_state.json.backup_phase_1

# Stelle letztes gültiges Backup wieder her
cp runs/2026-02-18_14-30-00/metadata/research_state.json.backup_phase_2 \
   runs/2026-02-18_14-30-00/metadata/research_state.json

# Validiere
python3 scripts/validate_state.py runs/2026-02-18_14-30-00/metadata/research_state.json
```

---

## Fehler in spezifischen Phasen

### Phase 0: DBIS-Navigation schlägt fehl

**Fehler:**
```
Error navigating DBIS portal
Could not find database search field
```

**Ursachen:**
1. DBIS-Website hat sich geändert (UI-Update)
2. Netzwerk-Problem
3. DBIS ist offline

**Lösung:**

#### Option 1: Retry

```
# Im Chat tippe:
retry phase 0
```

#### Option 2: Manuelle Datenbank-Liste

Überspringe DBIS und nutze nur kuratierte Liste:

```markdown
# In deiner Konfig setze:

## Datenbank-Präferenzen
Skip DBIS Discovery: Yes
```

Dann starte erneut mit `/academicagent`.

### Phase 2: Datenbank-Suche langsam / hängt

**Symptome:**
- Iteration 1 dauert > 2 Stunden
- Eine Datenbank hängt
- Fortschritt stoppt

**Lösung: Timeout & Skip**

AcademicAgent hat automatische Timeouts:
- **Pro Datenbank:** 15 Minuten
- **Pro Iteration:** 2 Stunden

**Manueller Skip:**

Wenn eine Datenbank länger als 15 Min hängt:

```
# Im Chat tippe:
skip current database
```

Agent springt zur nächsten Datenbank.

**Datenbank permanent ausschließen:**

Nach der Recherche (falls eine DB immer problematisch):

```markdown
# Für zukünftige Recherchen in Konfig:

### Ausgeschlossene Datenbanken
[Problematische DB]
```

### Phase 4: PDF-Download schlägt fehl

**Fehler:**
```
Failed to download PDF: Smith_2023_Lean_Governance.pdf
Error 404: Not Found
```

**Ursachen:**
1. PDF-Link ist tot (Paper wurde verschoben)
2. Paywall (VPN nicht aktiv)
3. Datenbank temporär down

**Lösung: Manueller Download & Ergänzung**

1. **Finde das Paper** auf Google Scholar:
   ```
   Suche: "Smith 2023 Lean Governance"
   ```

2. **Lade PDF manuell** herunter

3. **Lege es in Downloads-Ordner:**
   ```bash
   cp ~/Downloads/smith_paper.pdf \
      runs/2026-02-18_14-30-00/downloads/Smith_2023_Lean_Governance.pdf
   ```

4. **Recherche wird automatisch fortgesetzt**
   (Agent prüft ob PDF jetzt da ist)

**Oder: Überspringe dieses Paper**

```
# Im Chat tippe:
skip this paper
```

Agent nimmt stattdessen Platz 19 aus der Kandidatenliste.

### Phase 5: Zitat-Extraktion schlägt fehl

**Fehler:**
```
Error extracting quotes from: Smith_2023_Lean_Governance.pdf
PDF is image-based (no text layer)
```

**Ursache:** PDF ist ein eingescanntes Bild (kein maschinenlesbarer Text).

**Lösung: OCR verwenden**

```bash
# Installiere OCR-Tool (falls nicht vorhanden)
# macOS:
brew install tesseract

# Extrahiere Text mit OCR
tesseract runs/2026-02-18_14-30-00/downloads/Smith_2023_Lean_Governance.pdf \
          runs/2026-02-18_14-30-00/downloads/Smith_2023_Lean_Governance.txt

# Dann retry
# Im Chat:
retry phase 5
```

**Oder: Überspringe dieses Paper**

```
skip Smith_2023_Lean_Governance.pdf
```

---

## Performance-Probleme

### Problem: Recherche ist sehr langsam

**Symptome:**
- Phase 2 dauert > 3 Stunden
- Agent antwortet langsam

**Diagnose:**

```bash
# Prüfe Chrome-Speichernutzung
ps aux | grep Chrome

# Wenn > 2GB → Chrome neu starten
```

**Optimierungen:**

#### 1. Weniger Datenbanken pro Iteration

In deiner Konfig:
```markdown
## Iterative Suchparameter
Databases Per Iteration: 3  # Statt 5
```

#### 2. Niedrigere Target Candidates

```markdown
Target Candidates: 30  # Statt 50
```

#### 3. Aggressive Datenbanken ausschließen

```markdown
### Ausgeschlossene Datenbanken
Google Scholar, Semantic Scholar
```

Diese Datenbanken haben strenge Rate-Limits.

### Problem: Hohe API-Kosten

**Symptome:**
- Recherche kostet > $5
- Viele Claude API-Aufrufe

**Lösung: Kosten-Tracking & Optimierung**

```bash
# Prüfe Kosten-Breakdown
python3 scripts/cost_tracker.py runs/2026-02-18_14-30-00/metadata/llm_costs.jsonl
```

**Ausgabe:**
```
📊 Kostenübersicht
Gesamt: $4.85

Nach Agent:
- browser-agent: $2.10 (43%)
- scoring-agent: $1.20 (25%)
- extraction-agent: $0.95 (20%)
- search-agent: $0.60 (12%)

Nach Phase:
- Phase 2: $2.10 (43%)
- Phase 5: $0.95 (20%)
- Phase 3: $0.90 (19%)
...
```

**Optimierungen:**

1. **Reduziere Datenbanken:**
   Mehr Datenbanken = mehr browser-agent Kosten

2. **Reduziere Zielanzahl:**
   Weniger Papers = weniger extraction-agent Kosten

3. **Nutze günstigeres Modell:**
   ```markdown
   # In Agent-Configs (für Fortgeschrittene):
   Model: claude-haiku-4  # Statt claude-sonnet-4
   ```

---

## Logging & Debugging

### Logs für detaillierte Fehlersuche

Alle Phasen loggen detailliert:

```bash
# Haupt-Logs
tail -f runs/[Timestamp]/logs/phase_2.log

# CDP-Health
tail -f runs/[Timestamp]/logs/cdp_health.log

# Fehler-Logs
grep ERROR runs/[Timestamp]/logs/*.log
```

### Debug-Modus aktivieren

Für sehr detaillierte Logs:

```bash
# Umgebungsvariable setzen
export ACADEMIC_AGENT_DEBUG=1

# Dann Recherche starten
/academicagent
```

**Warnung:** Debug-Modus generiert VIELE Logs (mehrere MB).

---

## Wo finde ich Hilfe?

### 1. Dokumentation

- **[ERROR_RECOVERY.md](../../ERROR_RECOVERY.md)** - Umfassender Fehlerbehandlungs-Guide
- **[SECURITY.md](../../SECURITY.md)** - Sicherheitsdokumentation
- **[Developer Guide](../developer-guide/README.md)** - Für technische Details

### 2. Community

- **GitHub Issues:** [github.com/jamski105/AcademicAgent/issues](https://github.com/jamski105/AcademicAgent/issues)
  - Suche nach ähnlichen Problemen
  - Erstelle ein neues Issue mit Logs

- **GitHub Discussions:** [github.com/jamski105/AcademicAgent/discussions](https://github.com/jamski105/AcademicAgent/discussions)
  - Stelle Fragen
  - Teile Erfahrungen

### 3. Issue erstellen

Wenn du ein Issue erstellst, inkludiere:

```markdown
### Problembeschreibung
[Was ist passiert?]

### Erwartetes Verhalten
[Was sollte passieren?]

### Schritte zur Reproduktion
1. [Schritt 1]
2. [Schritt 2]
...

### Umgebung
- OS: [macOS 14.1, Ubuntu 22.04, etc.]
- Chrome Version: [chrome://version/]
- AcademicAgent Version: [git rev-parse HEAD]

### Logs
```
[Relevante Log-Auszüge]
```

### Screenshots
[Falls relevant]
```

---

## Nächste Schritte

Jetzt kannst du die meisten Probleme selbst lösen! Als nächstes:

- **[Best Practices](06-best-practices.md)** - Tipps für bessere Recherchen
- **[Zurück zum Inhaltsverzeichnis](README.md)**

---

**[← Zurück zu: Ergebnisse verstehen](04-understanding-results.md) | [Weiter zu: Best Practices →](06-best-practices.md)**
