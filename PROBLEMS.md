Es gibt erhebliche Fehler im Agent System ich habe dir 3 Berichte mitgebracht die diverse Probleme erläutern.
Berricht 1Kurzfazit zur Architektur
Die AcademicAgent‑Plattform besteht aus einem Verbund aus LLM‑gesteuerten Teilagenten und Shell‑/Node‑Hilfsskripten. Die Laufzeitumgebung ist streng abgeschottet: Zugriffe auf Datei‑/Netzwerkressourcen durch die Agenten werden über scripts/auto_permissions.py und scripts/action_gate.py validiert. Die Systemarchitektur sieht wie folgt aus:
* .claude/agents enthält die Prompt‑Definitionen für die „intelligenten“ Agenten (setup‑agent, orchestrator, browser, search, scoring, extraction). Diese Dateien definieren den Dialog, die Ein‑/Ausgabe‑Verträge, Security‑Regeln und die CLI‑UI. Der Code der Agenten liegt nicht im Repository – sie werden vom LLM anhand dieser Prompts erzeugt.
* scripts/ enthält „Back‑Office“‑Utilities: die Auto‑Permission‑Logik, das Action‑Gate (Blockieren unsicherer Bash‑Befehle), State‑Management, Chrome‑Debug‑Starter, Browser‑CDP‑Helper usw. Es gibt auch eine interaktive TUI (interactive_setup.py) und einen Shell‑Wrapper (academicagent_wrapper.sh) für den Start der Pipeline.
* runs/<run_id> wird zur Laufzeit erstellt. Laut Projektdokumentation enthält jedes Run‑Verzeichnis Unterordner für Konfiguration, Zwischenstände, Downloads, finale Ergebnisse und Logs. Für Setup‑ und Orchestrator‑Agenten existieren Auto‑Permission‑Regeln, die das Schreiben bestimmter Dateien in runs/<run_id>/… ohne Nachfrage erlauben.
Die Orchestrierung läuft typischerweise so ab: Der User startet /academicagent, worauf der setup‑agent die Frage, Keywords und den Modus erfasst, create_run_structure.sh ausführt (erzeugt Run‑Verzeichnis mit Dateien) und run_config.jsonschreibt. Anschließend startet der orchestrator‑agent (per Task) die sieben Phasen: Datenbankidentifikation, Suchstring‑Generierung (search‑agent), DB‑Suche & Kandidatensammlung (browser‑agent), Scoring, PDF‑Download (browser‑agent), Quote‑Extraktion (extraction‑agent) und Finalisierung. Zwischenstände werden im Run‑Verzeichnis abgelegt und durch den state_manager.py verfolgt.
Architekturdiagramm (Textform)

User /interactive_setup.py
    │  (TUI oder /academicagent Kommando)
    ▼
setup‑agent  ──────────┐  – fragt Forschungsfrage, extrahiert Keywords, wählt Modus
    │                 │
    │ (write run_config.json)
    ▼                 │
create_run_structure.sh ──▶ Run‑Verzeichnis `runs/<run_id>` anlegen (metadata, downloads, logs, output)
    ▼                 │
(orchestrator-agent)   │
    │   Phase 0 – DB‑Identifikation (browser-agent)
    │   Phase 1 – Suchstring‑Generierung (search-agent)
    │   Phase 2 – DB‑Suche & Kandidaten (browser-agent)
    │   Phase 3 – Scoring (scoring-agent)
    │   Phase 4 – PDF‑Download (browser-agent)
    │   Phase 5 – Quote‑Extraktion (extraction-agent)
    │   Phase 6 – Finalisierung (orchestrator schreibt quote_library.json, bibliography.bib)
    ▼
Auto‑Permissions / Action‑Gate
    │   – validiert Lese/Schreib‑Zugriffe in den Phasen
    │
state_manager.py
    │   – speichert Phase‑Status in runs/<run_id>/metadata/research_state.json
    ▼
User
Datenflüsse: Die Agenten arbeiten strikt dateibasiert. Der setup‑agent schreibt run_config.json; der search‑agent liest database.json und schreibt search_strings.json; der browser‑agent liest Search‑Strings und Datenbank‑Patterns und füllt candidates.json und später downloads/; der scoring‑agent liest Kandidaten und erzeugt ranked_candidates.json; der extraction‑agent liest PDFs aus downloads/ und erzeugt quotes.json und quote_library.json. Der orchestrator‑agent koordiniert über Phase‑Marker‑Dateien und ruft nach jeder Phase den nächsten Agenten per Task auf.
Problemanalyse je Punkt
1 Setup‑Agent nutzt keine TUI / zu viele Fragen
Der Setup‑Agent (Chat‑basierter Prompt) führt einen langen Dialog: Forschungsfrage, Keyword‑Bestätigung, Moduswahl, Datenbanksuche, Validierung usw. Dies entspricht dem iterativen Setup‑Flow im Prompt. Obwohl ein Python‑TUI (interactive_setup.py) existiert, wird der Chat‑basierte Setup‑Agent im /academicagent‑Workflow verwendet. Mögliche Ursachen:
* Fehlende Integration des TUIs: academicagent_wrapper.sh startet die TUI nur mit --interactive; der /academicagent‑Skill ruft jedoch direkt Task(setup-agent) auf, wodurch der Setup‑Agent promptbasiert läuft. User, die den CLI‑Weg nutzen, sehen daher keinen TUI.
* Prompt‑Design: In .claude/agents/setup-agent.md werden alle Schritte (Keyword‑Extraktion, DB‑Discovery, Bewertung) als eigenständige User‑Fragen implementiert. Es gibt keine feste Reduktionslogik; deswegen stellt der Agent viele Fragen und hat wenig Vorauswahl.
* Unnötige Fragen: Viele Werte (z. B. start_year, end_year, databases_per_iteration, early termination) können aus dem Modus oder der Konfiguration abgeleitet werden. Die Prompt‑Spezifikation legt diese Parameter offen und zwingt den Agenten, sie abzufragen.
2 Orchestrator halluziniert / startet search‑agent nicht zuverlässig
Mehrere Nutzer berichten, dass der orchestrator‑agent nach Ankündigung eines Sub‑Agent‑Starts stoppt oder den falschen Agenten ruft. In der Robustness‑Dokumentation wird genau dieses Verhalten beschrieben. Ursachen:
* Turn‑Management: Der orchestrator gibt eine Beschreibung aus („Ich starte jetzt den search‑agent…“) und schließt den Turn, bevor der Task()‑Call generiert wird. Die LLM beendet den Schritt ohne Aufruf – ein bekanntes Halluzinationsmuster.
* Fehlende Retry‑Logik: Wenn ein Sub‑Agent nicht startet (z. B. Browser‑Timeout), bricht der orchestrator den Workflow ab statt erneut zu versuchen.
* Unvalidierter Phasenübergang: Der orchestrator prüft teils nicht, ob die vorherige Phase erfolgreich war. Startet die Suche ohne vorhandenes search_strings.json, schlägt er fehl.
* Falsche Dateipfade: Die select_config.py erzeugt das Verzeichnis Downloads/ (Groß‑D), während Auto‑Permissions und Browser‑Agent downloads/ (klein‑d) erwarten. Der Browser‑Agent könnte daher keine PDFs speichern, was als „Sub‑Agent startet nicht“ wahrgenommen wird.
* Environment‑Variable CURRENT_AGENT: Wenn CURRENT_AGENT beim Spawn nicht gesetzt wird oder an Sub‑Agents verloren geht, greift das Auto‑Permission‑System nicht – es wird jedes Mal eine Berechtigung abgefragt.
3 Keine PDF‑Downloads
Der Browser‑Agent speichert PDFs in runs/<run_id>/downloads/ und erzeugt downloads.json. Gründe für fehlende Downloads:
* Falscher Zielordner: Wie oben erwähnt, erzeugt select_config.py das Verzeichnis Downloads/ (Groß‑D), während die Browser‑Agent‑Prompt und die Auto‑Permission‑Regeln ausschließlich runs/<run-id>/downloads/ akzeptieren. Der Browser‑Agent kann daher weder schreiben noch wird ihm die Erlaubnis erteilt.
* Pre‑Creation des Run‑Verzeichnisses: Wenn create_run_structure.sh nicht ausgeführt wurde, existiert downloads/nicht und der Browser‑Agent muss es anlegen. Für das Setup‑Agent sind solche Schreibvorgänge nicht auto‑erlaubt – der User wird jedes Mal gefragt. Bei fehlender Bestätigung schlägt der Download fehl.
* Chrome/Browser‑Timeout: Der Browser‑Agent verwendet browser_cdp_helper.js und Playwright. Fehler (Timeout, DB‑Login) werden möglicherweise nicht durch den orchestrator abgefangen. Das System beendet den Download, ohne die Gründe zu loggen.
* Fehlende Proxy/DB‑Login: Manche Datenbanken brauchen DBIS‑Proxy oder Uni‑Login. Ohne Login versucht der Browser‑Agent PDF‑Links zu laden und erhält HTML‑Fehlerseiten; der orchestrator interpretiert das als „kein Download“.
4 Ständige Berechtigungsabfragen
Beim Speichern fast jeder Datei erscheint ein Permission‑Prompt, obwohl der User bereits die Zustimmung erteilt hat. Ursachen sind:
* Auto‑Permission nicht aktiviert: Die Environment‑Variablen CLAUDE_SESSION_AUTO_APPROVE_AGENTS und ACADEMIC_AGENT_BATCH_MODE setzen das System in einen Modus, in dem alle Standarddateien ohne Nachfrage geschrieben werden dürfen. Wenn diese Variablen nicht gesetzt sind oder beim Agent‑Spawn verloren gehen, fragt das System für jeden Schreibvorgang erneut.
* Nicht übereinstimmende Pfad‑Regeln: Auto‑Permissions erlauben nur genau definierte Muster (z. B. runs/<run-id>/metadata/search_strategy.txt, runs/<run-id>/downloads/.*). Wenn ein Agent versucht, ein Verzeichnis mit Großbuchstaben zu schreiben (Downloads/), fällt es durch und der User muss bestätigen.
* Fehlender Aufruf von create_run_structure.sh: Das Skript erzeugt alle Zielordner und leere Dateien, wodurch später keine neuen Dateien angelegt werden müssen. Wird dieses Skript übersprungen (z. B. im Setup‑Agent), müssen die Agents die Dateien zur Laufzeit erzeugen und benötigen jedes Mal eine explizite Bestätigung.
Wahrscheinlichste Root Causes (Top 5, priorisiert)
1. Falsche Verzeichnisnamen (Downloads vs. downloads) – Der Browser‑Agent darf PDFs nur in runs/<run-id>/downloads/ speichern, die Setup‑Skripte erzeugen aber Downloads/. Das führt zu fehlgeschlagenen Downloads und Permission‑Prompts.
2. Setup‑Agent überspringt create_run_structure.sh – Ohne vorab angelegte Ordner und Dateien muss jeder Agent bei der Erstellung um Erlaubnis fragen. Der Prompt weist darauf hin, das Skript aufzurufen, aber in der realen Implementation wird es nicht zuverlässig verwendet.
3. CURRENT_AGENT‑Umgebung wird nicht korrekt vererbt – Wenn der orchestrator beim Spawn nicht export CURRENT_AGENT=<name> setzt, kann auto_permissions.py den Agenten nicht erkennen und erlaubt keine Auto‑Zugriffe.
4. Prompt‑Design des Orchestrators – Der orchestrator beschreibt Aktionen und wartet auf den nächsten Turn, statt sofort Task(search-agent) aufzurufen. Dadurch werden Sub‑Agenten nicht gestartet.
5. Fehlende Retry‑ und Validierungslogik – Der orchestrator startet eine Phase auch dann, wenn die Datei aus der vorherigen Phase fehlt (z. B. search_strings.json) und beendet den Workflow sofort bei Fehlern ohne Wiederholung.
Konkreter Maßnahmenplan
Quick Wins (sofort umsetzbar)
1. Verzeichnisnamen harmonisieren: In select_config.py und anderen Skripten Downloads/ durch downloads/ ersetzen. Ebenso die Verwendung von output/ vs. outputs/ überprüfen. Korrigieren Sie die Auto‑Permission‑Regeln, falls weitere Diskrepanzen existieren.
2. create_run_structure.sh verpflichtend machen: Der Setup‑Agent sollte immer via safe_bash das Skript aufrufen, bevor run_config.json geschrieben wird. Damit existieren alle Dateien/Ordner und Auto‑Permissions greifen ohne weitere Prompts.
3. Automatische Session‑Genehmigung aktivieren: Stellen Sie sicher, dass CLAUDE_SESSION_AUTO_APPROVE_AGENTS=true und ACADEMIC_AGENT_BATCH_MODE=true gesetzt werden, bevor der orchestrator oder Setup‑Agent gespawnt wird.
4. Explicit Action‑First Pattern implementieren: In der orchestrator‑Prompt den Task()‑Aufruf immer VOR dem erklärenden Text generieren lassen. Beispielsweise: zuerst Task(search-agent, args) aufrufen, anschließend den Erfolg melden.
5. Retry‑Logik für Agent‑Spawn integrieren: Implementieren Sie im orchestrator einen Try–Catch‑Block mit maximal zwei Retries und exponentiellem Backoff. Falls das Spawnen fehlschlägt, erneut versuchen oder dem User anzeigen, welche Phase nicht gestartet werden konnte.
Mittelfristige Refactorings
1. Prompt‑Reduktion im Setup‑Agent: Entfernen Sie Fragen, die aus Kontext ableitbar sind (z. B. Zeitbereich „letzte 5 Jahre“ oder Standard‑Modus). Führen Sie Modus, Ziel‑Zitate, Datenbankanzahl und Qualitätskriterien in einer einzigen Auswahl zusammen (siehe TUI‑Redesign). Verwenden Sie sinnvolle Defaults aus config/academic_context.md.
2. Zentralisierte Pfad‑Konstanten: Legen Sie in scripts/constants.py Konstanten für Verzeichnisnamen fest (z. B. DOWNLOADS_DIR="downloads"). Alle Skripte und Prompts importieren diese Konstanten. Dadurch entstehen keine Inkonsistenzen bei Groß/Kleinschreibung.
3. State‑Validierung: Integrieren Sie die Phase‑Prerequisite‑Checks aus ORCHESTRATOR_ROBUSTNESS_FIXES.mdvor jedem Task()‑Aufruf. Falls eine Datei fehlt, bricht der orchestrator mit einer klaren Fehlermeldung ab und fragt nicht nach der nächsten Phase.
4. Observability verbessern: Ergänzen Sie browser_cdp_helper.js und andere Tools um strukturierte Logs (JSON‑Zeilen pro Aktion) und legen Sie sie im jeweiligen Agent‑Logfile ab. Verwenden Sie das Logging‑Schema aus scripts/budget_limiter.py als Vorlage.
5. Encapsulate Agent Spawning in Python: Statt Task() direkt im LLM‑Prompt auszuführen, könnte ein kleines Python‑Wrapper‑Script (z. B. spawn_agent.py) aufgerufen werden. Dieses setzt CURRENT_AGENT, ruft claude code taskauf und validiert das Ergebnis. Somit ist die Logik deterministischer.
Architekturverbesserungen
1. State Machine für Orchestrator: Modellieren Sie den 7‑Phasen‑Workflow als deterministische Zustandsmaschine. Jeder Zustand definiert klar die erforderlichen Eingaben, den auszuführenden Agenten und die erwarteten Ausgaben. Der orchestrator ruft die Unteragenten nicht per LLM‑Spekulation, sondern anhand des State‑Maschinendiagramms. Dies lässt sich als Python‑Dienst implementieren, der den LLM‑Agent nur für inhaltliche Aufgaben nutzt.
2. Hook‑basierte Permission‑Caching: Statt bei jedem File‑Write die Permission zu prüfen, kann das Auto‑Permission‑System einen Session‑Cache führen: Beim ersten Write zu runs/<run_id>/downloads/ wird die Genehmigung eingeholt und anschließend bis zum Ende der Session wiederverwendet. Dazu wird CURRENT_AGENT und run_id als Schlüssel verwendet.
3. Unified TUI and LLM Setup: Verwenden Sie die Logik von interactive_setup.py als Referenz für den Setup‑Agent. Der LLM kann die gleichen Schritte (Forschungsfrage → Keyword‑Extraktion → Modus‑Auswahl → Zusammenfassung) in 2–3 Dialogrunden abbilden. Dadurch reduziert sich der Chat‑Overhead und die Erfahrung ähnelt der TUI.
4. Parameterizable Search Strategy: Legen Sie Modus‑Profile (Quick, Standard, Deep) als YAML ab und lassen Sie den Setup‑Agent nur das Profil wählen. Alle anderen Parameter werden automatisch gesetzt.
TUI‑Redesign‑Vorschlag (1–3 Schritte)
Ziel: Der Setup‑Flow soll möglichst wenig Interaktion benötigen und die User‑Erfahrung verbessern.
1. Schritt 1 – Forschungsfrage eingeben
    * Der Agent zeigt eine Question‑Box (CLI UI Standard) mit der Aufforderung, die Forschungsfrage einzugeben. Nach Eingabe führt der Agent automatisch eine Keyword‑Extraktion durch (z. B. mit einer Stopword‑Liste wie in interactive_setup.py) und zeigt die fünf wichtigsten Keywords an.
2. Schritt 2 – Modus‑Auswahl mit Defaults
    * Präsentieren Sie eine Auswahlbox (1 = Quick, 2 = Standard, 3 = Deep) wie im CLI‑UI‑Beispiel. Jede Option enthält Ziel‑Zitate, geschätzte Zeit und DB‑Anzahl. Zusätzlich können Parameter wie Zeitbereich (z. B. „letzte 5 Jahre“) und Qualitätskriterien als Default angezeigt werden. Die meisten Nutzer müssen nur eine Zahl wählen.
    * Optional: Eine Option „Eigenes Profil“ erlaubt fortgeschrittenen Nutzern, einen YAML‑Konfigurationsdatei zu wählen oder Parameter manuell anzupassen.
3. Schritt 3 – Zusammenfassung & Bestätigung
    * Nachdem der Modus gewählt wurde, generiert der Agent die vollständige run_config.json und zeigt eine Info‑Box mit den wichtigsten Einstellungen (Frage, Keywords, Modus, Zeitbereich, erwartete Dauer). Nur wenn der User bestätigt, wird create_run_structure.sh via safe_bash ausgeführt und run_config.json geschrieben. Danach startet der orchestrator automatisch.
Fragen, die entfallen können
* Start‑/End‑Jahr: aus Modus ableitbar (z. B. Quick = letzte 3 Jahre, Standard = 5 Jahre). Fortgeschrittene können dies im Profil anpassen.
* Datenbanken‑Liste: Der Setup‑Agent kann auf Basis der Disziplin in academic_context.md eine Top‑Liste erzeugen und die iterative Suche automatisch durchführen. Eine manuelle DB‑Auswahl sollte optional bleiben.
* Anzahl der Datenbanken pro Iteration, frühe Terminierung etc. – diese Werte sind im Profil festgelegt.
Empfohlene Libraries / Architektur
* Für lokale CLI bleibt questionary sinnvoll. Innerhalb des LLMs kann man die CLI‑UI‑Standard‑Boxen verwenden, um die gleichen Menüs anzuzeigen und Eingaben zu validieren.
* Der Setup‑Agent soll create_run_structure.sh über safe_bash aufrufen und die generierte run_config.json validieren. Dann ruft er den orchestrator per Task(orchestrator-agent) ohne weitere Fragen.
Permission‑Handling‑Redesign
Ein robustes Berechtigungsmodell sollte die Anzahl der User‑Prompts minimieren, ohne Sicherheitsrichtlinien zu verletzen.
1. Einmalige Zustimmung pro Session: Beim Start des /academicagent‑Skills wird der User nach globaler Zustimmung gefragt (z. B. „Darf der Agent innerhalb dieses Run‑Verzeichnisses Dateien lesen/schreiben?“). Wird zugestimmt, setzt das System CLAUDE_SESSION_AUTO_APPROVE_AGENTS=true und ACADEMIC_AGENT_BATCH_MODE=true. Der orchestrator speichert diese Entscheidung im Session‑Kontext und vererbt die Variablen an alle Sub‑Agents.
2. Scope‑basierte Berechtigungen: Auto‑Permissions werden pro Agent und pro run_id definiert.  auto_permissions.pykann erweitert werden, um bei unbekannten Pfaden zu prüfen, ob der Pfad innerhalb des Run‑Scopes liegt (z. B. regex ^runs/<current_run>/). Dadurch können Agents auch neue Unterordner (wie downloads/tmp) anlegen, solange sie im Run‑Verzeichnis bleiben.
3. Session‑Cache: Speichern Sie im Memory (oder in runs/<run_id>/metadata/permissions.json), dass bestimmte Aktionen bereits genehmigt wurden. Beim nächsten gleichartigen Zugriff wird keine erneute Anfrage gestellt.
4. Zustandsverlust verhindern: Jeder Agent muss export CURRENT_AGENT=<name> setzen, bevor er startet. Das kann im Python‑Spawn‑Wrapper oder in den claude code task‑Argumenten geschehen. Somit erkennt auto_permissions.py den Agenten und wendet die passenden Regeln an.
5. Verbesserte Logging/Auditing: Jede Ablehnung oder manuelle Genehmigung wird mit Zeitstempel und Pfad in runs/<run_id>/logs/permissions.log protokolliert. Nach Abschluss der Recherche kann der User diese Datei einsehen.
Debugging‑/Observability‑Plan
Um die angesprochenen Probleme nachhaltig zu diagnostizieren, sollten folgende Maßnahmen umgesetzt werden:
1. Feingranulare Logs: Jeder Agent sollte pro Aktion (Tool‑Call, Datei‑Zugriff, Browser‑Navigation) einen JSON‑Logeintrag mit Zeitstempel, Phase, Aktionstyp, Pfad und Ergebnis schreiben. Die Logdateien pro Agent (runs/<run_id>/logs/<agent>_agent.log) sollten standardisiert sein. Bei Fehlern wie „PDF konnte nicht geladen werden“ muss der genaue HTTP‑Status und die URL geloggt werden.
2. Event‑Tracing im orchestrator: Vor und nach jedem Task()‑Aufruf schreibt der orchestrator einen Eintrag „Spawn search-agent – Attempt 1“, „Spawn search-agent – Success / Failure“. Zusammen mit der Retry‑Logik kann man nachverfolgen, warum ein Spawn fehlschlug (Timeout, Permission‑Error, falscher Pfad).
3. Überprüfen der Übergabeparameter: Loggen Sie vor jedem Agent‑Spawn, welche Dateien übergeben werden (z. B. databases.json für den search‑agent). Nach dem Spawn überprüfen Sie, ob das erwartete Output‑File existiert und dem JSON‑Schema entspricht.
4. PDF‑Download‑Fehler klassifizieren:
    * Startfehler: browser-agent wurde nicht gestartet – identifizieren Sie dies über fehlende Spawn‑Logs.
    * URL‑Fehler: die herunterzuladende URL führt zu einer 404‑/403‑Seite. Speichern Sie URL und HTTP‑Status im Log.
    * Auth‑Fehler: das PDF erfordert Proxy/Uni‑Login – erkennen Sie HTML‑Login‑Seiten anhand von Musterwörtern („login“, „Shibboleth“) und vermerken Sie dies im Log.
    * Parser‑Fehler: pdftotext oder die Text‑Extraktion schlägt fehl. Loggen Sie das PDF‑Dateiformat und eventuelle Fehlermeldungen.
    * Timeout: Download bricht nach N Sekunden ab. Loggen Sie die Dauer und erhöhen Sie bei Bedarf das Timeout.
5. LLM‑Halluzinationen eindämmen: Setzen Sie Guardrails in den Prompts, die explizit anweisen, dass Aktionen ohne Output als Fehler gelten. Verwenden Sie die „Implementierungs‑Checkliste“ als Referenz und fügen Sie sie dem orchestrator‑Prompt hinzu. Führen Sie bei fehlender oder fehlerhafter Antwort des Sub‑Agenten einen Retry aus.
6. Monitoring‑Dashboard: Ein Tmux‑Dashboard oder eine kleine Web‑App kann die aktuellen Phasen, Fortschritte, Log‑Einträge und Fehler in Echtzeit anzeigen. So erkennt der Nutzer frühzeitig, wenn der Browser‑Agent nichts herunterlädt oder der orchestrator hängen bleibt.
Rückfragen
Die oben genannten Verbesserungen basieren auf der vorhandenen Repository‑Struktur. Um gezielt zu helfen, wären folgende Punkte hilfreich:
1. Welche Start‑Methode nutzt du aktuell? Startest du /academicagent über den Chat oder den interaktiven TUI (wrapper‑Script)? Davon hängt ab, ob create_run_structure.sh ausgeführt wird.
2. Existieren Debug‑Logs von fehlgeschlagenen Runs? Eine Analyse konkreter Logdateien (z. B. browser_agent.log, orchestrator_agent.log) könnte weitere Hinweise geben.
3. Wie werden die Environment‑Variablen gesetzt? Wird CURRENT_AGENT korrekt gesetzt und wird CLAUDE_SESSION_AUTO_APPROVE_AGENTS im Chat‑Kontext aktiviert? Dies lässt sich durch Ausgaben in den Logs leicht nachprüfen.

Bericht 2
Technische und architektonische Analyse des AcademicAgent-Setups
Architekturüberblick und Datenfluss
Kurzfazit zur Architektur (Ist-Zustand)Dein System ist als Multi-Agent-Setup für Claude Code (von Anthropic) konzipiert und kombiniert (a) Prompt-definierte Sub-Agents in .claude/agents/ mit (b) einem Shell/Python/Node-Tooling-Layer in scripts/, der Security-Gates (Action-Gate, Schema-Validation), State-Management und Browser-Steuerung per Chrome DevTools Protocol (CDP) kapselt. Das ist grundsätzlich eine gute „Defense-in-Depth“-Richtung: Orchestrator delegiert Web/PDF-Zugriffe an spezialisierte Agents, und Outputs sollen via validation_gate.py geprüft werden.
Die Hauptursache für deine aktuellen Symptome ist jedoch nicht ein einzelner Bug, sondern ein Bündel systemischer Inkonsistenzen:
* Es existieren mehrere konkurrierende Artefakt-/Pfad-Konventionen (runs/ vs. projects/, output/ vs. outputs/, downloads/ vs. pdfs/, ranked_candidates.json vs. ranked_top27.json). Diese Inkonsistenzen tauchen gleichzeitig in Agent-Prompts und Scripts auf und führen zu falschen Preconditions, fehlenden Übergaben und „Workflows, die scheinbar laufen, aber keine echten Artefakte erzeugen“.
* Dein Permission-Setup in .claude/settings.json ist so gebaut, dass „ask“-Regeln breit matchen („Write“, „Bash()“, „Task()“ …). Laut offizieller Doku werden Regeln deny → ask → allow ausgewertet; damit schlägt ask deine allow-Regeln praktisch tot → Ergebnis: Permission-Spam.
* Der PDF-Download ist „im Design vorgesehen“, aber in der konkreten Toolchain nicht robust implementiert (z. B. kein Download-Action im CDP-Helper; Browser-Agent-Prompt setzt auf wget, das gleichzeitig durch Permission-/Action-Gate geblockt ist).
Architekturdiagramm in Textform (Komponenten + Datenfluss)(Notation: → Datenfluss / Übergabe; [ ] Artefakte; ( ) ausführende Einheit)
* (User in Claude Code Chat)→ startet /academicagent (Entry-Skill; in deinen Prompts referenziert)→ (setup-agent)→ erzeugt [run_config.json] + Setup-Artefakte→ (orchestrator-agent) koordiniert Phasen und spawnt Sub-Agents via Task→ (browser-agent) steuert Chrome via CDP (Node/Playwright-Helper) und sammelt Kandidaten / PDFs→ (search-agent) generiert Suchstrings→ (scoring-agent) rankt Kandidaten→ (extraction-agent) verarbeitet PDFs (pdftotext etc.)→ (orchestrator-agent) finalisiert Outputs (Bibliographie, Quote Library)
* Infrastruktur-/Tooling-Layer (lokal in scripts/):
    * safe_bash.py + action_gate.py (Command-Allowlist/Blocklist) vor jeder Shell-Ausführung
    * validation_gate.py (JSON-Schema-Validation + Sanitization) als Mandatory Gate nach Sub-Agent-Outputs
    * browser_cdp_helper.js + cdp_wrapper.py (Playwright connectOverCDP) für Navigation/Suche/Screenshots
    * validate_agent_execution.sh (Post-Phase Assertions: keine SYNTHETIC DOIs, PDFs existieren, Logs existieren)
    * state_manager.py (Resume/Recovery) + Live-Monitor Scripts (status_watcher.sh, launch_live_monitor.sh)
    * Domain/DBIS-Policy: validate_domain.py, domain_whitelist.json, track_navigation.py (DBIS-first)

Problemanalyse der vier aktuellen Probleme
Problemanalyse Punkt 1: Setup-Agent nutzt keine TUI, fragt zu viel, wenig AuswahlBeobachtungen im Repo
* Der Setup-Agent ist als „Dialog-Agent“ beschrieben und enthält einen sehr langen, phasenbasierten Fragenkatalog (Run-Goal, Research Question, Target Citations, Search Intensity, Zeitraum, Strategie, Qualitätskriterien, Keywords, Bestätigung etc.). Das ist strukturiert, aber kein echtes TUI (keine Menüs/Select-Widgets; nur textbasierte Boxen und „Wähle [1–x]“).
* Parallel existiert ein Script generate_config.py, das bereits „Research Modes“ (quick/deep/trend usw.) kapselt – das wäre perfekt geeignet, die Fragen drastisch zu reduzieren –, aber es generiert eine Markdown-Config im alten Format und nicht konsistent run_config.json.
Wahrscheinliche Ursachen (Hypothesen)
* H1 (sehr wahrscheinlich): „TUI“ ist aktuell nur als ASCII-Box-Standard dokumentiert (CLI_UI_STANDARD.md), aber es gibt kein interaktives Terminal-UI (curses/prompt-toolkit) im Tooling-Layer, und der Setup-Agent ruft auch keine entsprechende CLI auf.
* H2 (wahrscheinlich): Die Setup-Logik ist konzeptuell aus zwei Welten gemischt: (a) Prompt-gesteuerter Dialog in .claude/agents/setup-agent.md und (b) alte Config/Project-Flow-Scripts (generate_config.py, select_config.py) – dadurch wird nicht sauber auf „1–3 Schritte“ optimiert, sondern alles bleibt „question-by-question“.
Woran du es erkennen würdest (Code/Config/Logs)
* Es gibt keine Script-Abhängigkeiten für TUI-Libs in requirements.txt (nur jsonschema).
* Du findest keinen Setup-Runner wie setup_tui.py o. ä., der run_config.json konsistent erzeugt (stattdessen Markdown-Config-Generator).
Verdächtige Dateien/Module/Funktionen (prüfen)
* .claude/agents/setup-agent.md (Frageumfang/Flow)
* scripts/generate_config.py (Mode-Kapselung vorhanden, aber Output-Format/Ort inkonsistent)
* scripts/select_config.py (Run-Verzeichnis wird anders aufgebaut/benannt)
Schnelle Validierung (konkrete Checks)
* Check 1: Suche in repo nach „questionary“, „prompt_toolkit“, „textual“, „Inquirer“ – wenn leer, existiert keine echte TUI. (Der Repo-Status spricht bereits stark dafür.)
* Check 2: Vergleiche, ob Setup-Agent wirklich runs/<id>/config/run_config.json erzeugt (Contract) oder irgendwo anders; Pfad-Drift ist aktuell einer der größten Pain Points.

Problemanalyse Punkt 2: Orchestrator halluziniert / startet Search-Agent nicht zuverlässigBeobachtungen im Repo
* Dein orchestrator-agent enthält mittlerweile explizite Anti-Halluzinations-Regeln („DEMO-MODUS verboten“, „nie synthetische DOIs“), Action-First Pattern und sogar ein Shell-nahes „Phase Execution“-Gerüst (execute_phase_0..6, validate prerequisites, validate_agent_execution).
* Gleichzeitig enthält derselbe Orchestrator Prompt widersprüchliche Erwartungen:
    * Phase-Outputs heißen mal ranked_candidates.json, mal ranked_top27.json.
    * Phase 5 Preconditions prüfen PDFs in $RUN_DIR/pdfs, während andere Contracts/Docs Downloads in downloads/ erwarten.
* search-agent ist in der Tool-Konfiguration als „read-only, no Bash, no Write“ beschrieben (Outputs als Return-String), während der Orchestrator an mehreren Stellen so tut, als würde metadata/search_strings.json von search-agent geschrieben. Das ist ein klassischer Grund für „Agent wurde gestartet, aber Artefakt ist leer/fehlt“.
Wahrscheinliche Ursachen (Hypothesen)
* H1 (sehr wahrscheinlich): Pfad-/Artefakt-Inkonsistenzen führen dazu, dass Orchestrator Preconditions nicht erfüllt sieht oder falsche Dateien validiert. Wenn dann die Steuerlogik auf „wenn File exists → skip/continue“ basiert, kann das in „instabil/halluziniert“ münden, weil der Orchestrator intern versucht, Lücken zu füllen.
* H2 (sehr wahrscheinlich): search-agent kann in der aktuellen Tool-Ausstattung nicht selbst metadata/search_strings.json schreiben (kein Write/Bash), aber Orchestrator erwartet es. Ergebnis: fehlende Output-Datei → Folgephasen brechen, oder Orchestrator erstellt „irgendwas“ (Pseudo-Output) als Fallback.
* H3 (wahrscheinlich): Permission-Prompts unterbrechen Tool-Calls; wenn ein Turn endet, bevor Task() wirklich ausgeführt wurde, tritt genau das in ORCHESTRATOR_ROBUSTNESS_FIXES.md beschriebene Anti-Pattern ein („Ankündigen statt Ausführen“).
Woran du es in Logs/Artefakten erkennst
* In runs/<RUN_ID>/logs/ fehlt ein belastbarer Nachweis, dass der Sub-Agent wirklich lief (z. B. leer/fehlend: search_agent.log bzw. browser_agent.log). Dein Validator prüft das bereits für browser-agent in Phase 2.
* metadata/search_strings.json existiert nicht oder ist Placeholder/ungültig (z. B. [] statt object), insbesondere wenn create_run_structure.sh vorab leere Arrays schreibt.
Verdächtige Dateien/Module/Funktionen (prüfen)
* .claude/agents/orchestrator-agent.md (Phase-Gerüst + Preconditions + Output-Namen)
* .claude/agents/search-agent.md (Tooling: kein Write/Bash)
* scripts/create_run_structure.sh (Placeholder JSON + falsche Ordnernamen)
* scripts/validate_agent_execution.sh (stellt Halluzinationen/PDF-Fehler fest, aber nur wenn aufgerufen)
Schnelle Validierung (konkrete Checks)
* Check 1: Läuft Phase 1 wirklich? Prüfe: existiert runs/<id>/metadata/search_strings.json und entspricht dem Schema (nicht []). Wenn nicht, ist H2/H1 praktisch bestätigt.
* Check 2: Stelle sicher, dass der Orchestrator nach Phase 1 immer validation_gate.py aufruft (Schema-Gate) – sonst reichen „File exists“-Checks nicht.
* Check 3: Prüfe deine aktive Permission-Regel-Liste via /permissions in Claude Code – wenn ask breit matcht, ist Workflow-Abbruch an Tool-Gates plausibel.

Problemanalyse Punkt 3: Keine PDF-DownloadsBeobachtungen im Repo (sehr belastbar)
* Dein CDP-Helper (browser_cdp_helper.js) kennt Actions wie navigate, search, extract, screenshot, inject, status – kein download. Damit ist der „CDP Download“ im aktuellen Stand nicht implementiert.
* Der Browser-Agent-Prompt für Phase 4 beschreibt „wget-first“ und nutzt zudem projects/[ProjectName]/.../pdfs/ als Zielpfad – während andere Teile deines Systems runs/<id>/downloads/ nutzen. Das ist praktisch eine Garantie für „PDFs landen nirgendwo, wo der Rest sucht“.
* wget/curl werden in deinem Security-Layer explizit geblockt:
    * Claude Code Settings: deny enthält Bash(curl *), und ask/deny-Regeln wirken vor allow.
    * Zusätzlich blockt action_gate.py Network-Commands wie wget/curl über Pattern-Matching.
Wahrscheinliche Ursachen (Hypothesen)
* H1 (sehr wahrscheinlich): Phase 4 ist konzeptuell beschrieben, aber praktisch nicht lauffähig, weil (a) wget geblockt ist und (b) CDP-Download fehlt.
* H2 (wahrscheinlich): Selbst wenn PDFs irgendwo gespeichert würden, würden nachgelagerte Steps sie nicht finden: Orchestrator Preconditions prüfen teils $RUN_DIR/pdfs, während create_run_structure.sh downloads/ anlegt und AGENT_API_CONTRACTS.md PDFs ebenfalls unter downloads/ beschreibt.
* H3 (plausibel): Downloads über Playwright+CDP sind in bestimmten Konstellationen fehleranfällig; es gibt dokumentierte Issues speziell rund um Downloads nach connectOverCDP(). Das muss man in deinem Design einkalkulieren (Fallback/Alternative).
* H4 (kontextabhängig): Domain-/DBIS-Policy kann direkte Navigations-/Download-URLs blocken, wenn Session/Referer nicht als „DBIS-first“ erkannt wird.
Woran man es im Code/Logs erkennen würde
* In Phase 4: downloads/downloads.json fehlt oder bleibt leer, und im Dateisystem gibt es 0 PDFs. Dein Validator bricht bei 0 PDFs explizit ab.
* Browser-Agent-Log existiert, aber enthält nur Navigation/Screenshots, keine „download started/completed“-Events, weil die Action nicht existiert.
Verdächtige Dateien/Module/Funktionen (prüfen)
* scripts/browser_cdp_helper.js (fehlende Download-Implementierung)
* .claude/agents/browser-agent.md Phase 4 (wget-first + projects/ Pfade)
* .claude/agents/orchestrator-agent.md (Preconditions/Paths für Phase 4/5)
* scripts/domain_whitelist.json + validate_domain.py (Blockiert ggf. direkte PDF-Hosts ohne DBIS-Session)
Schnelle Validierung (konkrete Checks)
* Check 1: Existiert irgendein PDF im Run-Ordner? Dein Validator zählt runs/<id>/downloads/*.pdf. Wenn 0, ist H1 praktisch bestätigt.
* Check 2: Suche im Repo nach „download“ im CDP-Helper – wenn es keine Action gibt, ist CDP-Download schlicht nicht implementiert.

Problemanalyse Punkt 4: Ständige BerechtigungsabfragenBeobachtungen im RepoDeine .claude/settings.json definiert gleichzeitig:
* allow: viele spezifische Regeln (Write(runs/**), Bash(python3 scripts/*), Task(browser-agent) …)
* ask: extrem breit (Edit, Write, Bash(), WebFetch, WebSearch, Task())
Laut offizieller Claude Code Doku gilt: Regeln werden in der Reihenfolge deny → ask → allow ausgewertet; first match wins. Damit bedeutet ein ask wie Write oder Bash(*): „immer fragen“, selbst wenn du unten allow gesetzt hast.
Wahrscheinliche Ursachen (Hypothesen)
* H1 (sehr wahrscheinlich): Dein Permission-Spam ist primär „self-inflicted“ durch die Regelreihenfolge + die breite ask-Liste.
* H2 (wahrscheinlich): Du hast intern ein eigenes Auto-Permission-Konzept (scripts/auto_permissions.py) dokumentiert, aber es ist nicht an den Claude-Code Permission Layer gekoppelt (keine Hook-Integration). Ohne Hooks bleibt das wirkungslos gegen UI-Prompts.
* H3 (kontextabhängig): Falls zusätzlich „Managed Settings“ aktiv sind (Enterprise/Team), kann dein Projekt-Settings-File teilweise überschrieben werden. Claude Code dokumentiert die Settings-Precedence und managed settings locations.
Woran man es erkennen würde
* In /permissions siehst du Regeln, die aus .claude/settings.json kommen; wenn ask breit matcht, wird immer gefragt. Claude Code weist explizit auf /permissions als Diagnose-UI hin.
Verdächtige Dateien/Module/Funktionen (prüfen)
* .claude/settings.json (ask-Regeln)
* scripts/create_run_structure.sh (soll Prompts reduzieren, funktioniert aber nicht, solange Bash(*) als ask rule greift)
* scripts/auto_permissions.py (Konzept vs. tatsächliche Claude-Code-Permission-Evaluierung)
Schnelle Validierung (konkrete Checks)
* Check 1: Entferne testweise ask: ["Bash(*)", "Write", "Task(*)"] und prüfe, ob Prompt-Spam sofort verschwindet. Das folgt direkt aus der documented rule evaluation order.
* Check 2: Prüfe /permissions, ob du doppelte/konkurrierende Regeln aus user/local/project/managed scopes hast.

Wahrscheinlichste Root Causes
Top Root Causes (priorisiert, mit Begründung)
1. Claude Code Permission-Regeln sind so definiert, dass ask fast alles überschreibt → dadurch entsteht Permission-Spam, der wiederum Tool-Calls/Agent-Spawns unterbricht. Zentral: deny → ask → allow. 
2. Artefakt-/Pfad-Inkonsistenzen im gesamten Stack (Prompts, Scripts, Contracts): runs/ vs projects/, output/outputs, downloads/pdfs, ranked_candidates/ranked_top27, run_config mal in root, mal in config/. Das erzeugt falsche Preconditions und kaputte Übergaben. 
3. Tool-Capability/Contract Drift: z. B. search-agent hat kein Write/Bash, aber Orchestrator erwartet Datei-Outputs. Das produziert „Agent läuft, Output fehlt“ und triggert Folgefehler. 
4. PDF-Download ist praktisch nicht implementiert bzw. durch Security Gates blockiert: kein Download-Action im CDP-Helper; Browser-Agent-Prompt setzt auf wget, das in Settings/Action-Gate geblockt ist. 
5. Run-Structure Initialisierung erzeugt falsche „scheinbar vorhandene“ Outputs (create_run_structure.sh schreibt placeholder [] in Files, die eigentlich objects sein sollten, und nutzt abweichende Ordnernamen). Das kann Phasen fälschlich „bestehen lassen“ oder Validation/Parsing sprengen. 

Maßnahmenplan mit konkreten Fixes
Quick Wins (geringer Aufwand, hoher Impact)
Quick Win A: Permission-Spam sofort stoppen (Settings-Regeln korrigieren)
* Datei: .claude/settings.json
* Änderung: Entferne die breite ask-Liste oder mache sie extrem spezifisch. Grund: deny → ask → allow; broad ask gewinnt immer.
Minimaler Ansatz (Beispiel, Prinzip):
json
Kopieren
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "defaultMode": "acceptEdits",
  "permissions": {
    "deny": [
      "Read(.env)", "Read(.env.*)", "Read(./.env)", "Read(./.env.*)",
      "Read(secrets/**)", "Read(./secrets/**)", "Read(~/.ssh/**)",
      "Bash(sudo *)", "Bash(rm -rf *)", "Bash(dd *)", "Bash(mkfs*)",
      "Bash(ssh *)", "Bash(scp *)", "Bash(rsync *)",
      "Bash(curl *)", "Bash(wget *)"
    ],
    "allow": [
      "Read", "Grep", "Glob",
      "Write(runs/**)", "Edit(runs/**)", "Write(/tmp/*)",
      "Task(setup-agent)", "Task(orchestrator-agent)", "Task(browser-agent)",
      "Task(search-agent)", "Task(scoring-agent)", "Task(extraction-agent)",
      "Bash(python3 scripts/*)", "Bash(node scripts/*)", "Bash(bash scripts/*)",
      "Bash(jq *)", "Bash(grep *)", "Bash(find runs/**)", "Bash(mkdir -p runs/**)"
    ],
    "ask": []
  }
}
Warum acceptEdits: Claude Code dokumentiert, dass File-Modifications sonst nur sessionweise freigegeben werden; acceptEdits reduziert weiteren UX-Spam.
Quick Win B: Ein einziges „Source of Truth“-Run-Layout definieren und überall durchziehen
* Zielarchitektur (empfohlen): orientiere dich strikt am Contract in AGENT_API_CONTRACTS.md und am README-Run-Layout.
* Konkrete Entscheidung:
    * runs/<RUN_ID>/config/run_config.json
    * runs/<RUN_ID>/metadata/*.json (databases/search_strings/candidates/ranked_candidates/research_state)
    * runs/<RUN_ID>/downloads/ + downloads.json
    * runs/<RUN_ID>/outputs/ (quotes.json, quote_library.json, bibliography.bib, summary.md)
    * runs/<RUN_ID>/logs/
Danach: alle abweichenden Stellen patchen (siehe „Mittelfristige Refactors“).
Quick Win C: create_run_structure.sh so fixen, dass es nicht schadet
* Datei: scripts/create_run_structure.sh
* Probleme aktuell: falscher Ordnername output/ statt outputs/, falsche Vorbelegung ([] statt object), run_config.json liegt im root vom run, nicht im config/, und metadata/downloads.json statt downloads/downloads.json.
* Fix-Idee:
    * Erzeuge nur Ordner + leere Files, oder initialisiere mit minimal schema-konformen Objekten (z. B. { "databases": [], "timestamp": "..." } statt []).
    * Halte Pfade exakt an Contract.
Quick Win D: Search-Agent Output-Strategie konsistent machenDu hast zwei saubere Optionen – aktuell ist es „halb-halb“:
* Option 1 (empfohlen): Gib dem search-agent den Write-Tool-Zugriff zurück (oder (falls du es minimal halten willst) lass ihn ein File schreiben). Dann stimmt Contract „search-agent schreibt metadata/search_strings.json“.
* Option 2: Belasse search-agent read-only, aber dann muss Orchestrator den Return-JSON immer in metadata/search_strings.json schreiben und anschließend validation_gate.py laufen lassen.

Mittelfristige Refactors (1–3 Tage, stabiler Betrieb)
Refactor A: „path_config“ zentralisieren
* Neues Modul: scripts/path_config.py (oder scripts/paths.py)
* Zweck: Ein einziger Ort für Run-Layout (Funktionen wie run_dir(run_id), path_search_strings(run_id) etc.).
* Warum: Du hast aktuell dieselbe Logik redundant/abweichend in Prompts und Scripts (Orchestrator, Browser-Agent, create_run_structure, validate_agent_execution, select_config).
Refactor B: Alte „projects/“-Welt konsequent entfernen
* Dateien: .claude/agents/browser-agent.md, .claude/agents/extraction-agent.md, scripts/select_config.py, scripts/generate_config.py (stellenweise)
* Änderung: Replace projects/[ProjectName]/... → runs/<RUN_ID>/... und vereinheitliche Dateinamen.
Refactor C: Orchestrator Preconditions + Output-Namen bereinigen
* Datei: .claude/agents/orchestrator-agent.md
* Änderung:
    * nur ranked_candidates.json oder nur ranked_top27.json (eins!)
    * nur downloads/ oder nur pdfs/ (eins!)
    * only one location for run_config.json
* Warum: Preconditions sind dein „State Machine“-Ersatz. Wenn diese schon falsche Pfade prüfen, wirkt der Orchestrator „instabil“.

Architekturverbesserungen (systematisch gegen deine Problemklasse)
Architektur-Zielbild: deterministischer Orchestrator + „dumb“ Agents
* Orchestrator wird zu einer harten State Machine (Phasen/Transitions, Artefakt-Check, Schema-Gate).
* Sub-Agents sind „Worker“ ohne Interpretationsspielraum: sie bekommen Input-Pfad + Output-Pfad + Constraints und liefern nur Ergebnisse.
* Jede Phase endet erst, wenn:
    1. Output-Datei existiert und
    2. validation_gate.py erfolgreich war und
    3. validate_agent_execution.sh die Realitätschecks bestanden hat.
Das reduziert Halluzinationen technisch (nicht nur prompt-basiert), weil „Fake Output“ sofort als Gate-Fail sichtbar wird.

TUI-Redesign für Setup-Agent
TUI-Redesign-Vorschlag (1–3 Schritte, konkret)
Ziel: Setup von 10+ Fragen auf maximal 3 Interaktionen reduzieren, ohne Flexibilität zu verlieren.
Schritt 1: Modus-Auswahl (Single Select) + Advanced Toggle
* Default wird aus academic_context.md abgeleitet (Disziplin, Standard-Zeitraum, bevorzugte DBs).
* User wählt nur:
    * Quick (z. B. 5–8 Quellen)
    * Standard (z. B. 18 Quellen)
    * Deep (z. B. 40+ Quellen)
    * optional „Advanced…“ (öffnet zweite Ebene, aber Standard bleibt 1 Schritt)Du hast die Mode-Mappings bereits in generate_config.py als Konzept – das solltest du für run_config.json nutzen (statt Markdown-Config).
Schritt 2: Forschungsfrage (ein Freitextfeld)
* Aus der Frage werden Keywords extrahiert (automatisch). Setup fragt nur „Keywords übernehmen? (Ja/Nein)“.
Schritt 3: Review & Start (Confirm)
* Zeige eine Zusammenfassung und biete nur: Start / Zurück / Advanced.
Welche Fragen können komplett weg?
* Search Intensity: direkt durch Mode mappen (Quick=low, Standard=medium, Deep=high).
* Search Strategy: standardmäßig „iterativ“ (du bewirbst das als Default ohnehin). Nur in Advanced ändern.
* Target Citations: aus Mode ableiten, in Advanced optional übersteuerbar.
Welche Fragen zusammenführen?
* „Run Goal“ + „Target citations“ + „quality criteria“ + „time period“ → ein Mode-Preset.
Welche Werte ableiten statt fragen?
* Disziplin, Standard-DBs, Zitierstil, Default-Zeitraum → aus academic_context.md und database_disciplines.yaml/DB-Pool-Logik.
Library-/Architektur-Empfehlung für die echte TUI
* Python TUI: questionary/prompt_toolkit-basierte Menüs (Single Select, Checkbox, Confirm) oder textual für eine „schicke“ UI. In deinem Repo sind aktuell praktisch keine Python-Dependencies außer jsonschema, daher müsstest du requirements.txt erweitern.
* Wichtig: Wenn du diese TUI aus Claude Code heraus starten willst, musst du das Tooling so bauen, dass es wirklich interaktiv funktionieren kann; dein safe_bash.py capturt stdout/stderr per default, was für echte TUIs unpraktisch ist.

Permission-Handling-Redesign
Warum ständig neue Berechtigungsabfragen getriggert werden (Root Cause)
* In Claude Code gilt: Regeln werden deny → ask → allow evaluiert; die erste passende Regel gewinnt. Mit ask: ["Write", "Bash(*)", "Task(*)", ...] erzwingst du faktisch permanent Prompts.
* Zusätzlich sind File-Edit/Write-Approvals laut Doku typischerweise session-gebunden, während Bash-Approvals dauerhaft pro Projekt/Command sein können. Wenn du Persistenz willst, brauchst du entweder allow-Rules oder geeignete Modes (acceptEdits).
Robustes Modell (Einmalige Zustimmung, Scope-basiert, ohne UX-Spam)
Einmalige Zustimmung pro Projekt (praktisch):
* Stelle defaultMode auf acceptEdits (oder nutze sehr großzügige Edit/Write(runs/**) allow rules).
* Halte deny hart für Secrets und destruktive Commands.
Scope-basiert (Run-/Session-gebunden):
* Alle Agent-Schreiboperationen müssen unter runs/<RUN_ID>/... passieren. Das ist dein Scope. Danach kann Write(runs/**) global erlaubt werden.
* Vermeide absolute Pfade in Agent-Outputs/Commands, damit Rules sicher matchen (Claude Code Rules matchen auf Tool(specifier)-Strings).
Session-/Run-gebundenes Auto-Allow (optional, wenn du dynamischer werden willst):Claude Code dokumentiert Hooks („PreToolUse“), die vor dem Permission-System laufen und Approve/Deny entscheiden können. Damit könntest du dein auto_permissions.py wirklich produktiv machen (z. B. „erlaube Write nur für aktuelles RUN_ID Präfix“). Empfehlung: erst nach Stabilisierung nutzen, weil Hooks schnell Security-Risiken erzeugen.
Logging/Auditing ohne Spam
* Logge jede erlaubte Tool-Aktion als JSONL-Event (run_id, phase, tool, specifier, decision) in runs/<id>/logs/permissions.jsonl. Du hast bereits einen JSON-Logger.

Debugging- und Observability-Plan
Konkrete Debugging-Strategie (Orchestrator ↔ Search-Agent ↔ PDF-Download)
Logging/Events/Tracing (was einbauen)
1. Korrelations-ID überall: RUN_ID muss in jedem Log-Event enthalten sein. (Dein Logger kann Metadata tragen.)
2. Task-Spawns als Events: Orchestrator schreibt vor jedem Task:
    * {event:"task_spawn", phase, agent, input_files, expected_output}und nach Result: {event:"task_done", status, duration, output_paths}.
3. Artefakt-Manifest: runs/<id>/metadata/manifest.json (oder JSONL), das pro Phase den „expected artifacts“-Status speichert. Das reduziert „File exists, aber falsch“. (Harter Gate: schema-valid).
Übergaben prüfen (Orchestrator ↔ Search-Agent)
* Prüfe, ob der Search-Agent tatsächlich eine Datei schreibt oder ob er „Return-JSON“ liefert (Tool-Config sagt: kein Write/Bash). Das muss Orchestrator explizit behandeln.
* Validiere nach Phase 1: validation_gate.py gegen schemas/search_strings_schema.json (Schema-Referenz ist in Orchestrator-Prompt vorgesehen).
PDF-Download-Fehler klassifizieren (damit du nicht im Dunkeln tappst)Lege für jeden PDF-Versuch ein Event an:
* download_attempt_started (source_db, doi, url, method=cdp|http, attempt_n)
* download_attempt_failed (error_class)
* download_attempt_succeeded (bytes, content_type, path)
Klassifikation (praktisch):
* Startfehler (Download-Action fehlt / falsche Selector-Patterns) → wahrscheinlich bei dir aktuell, weil CDP-Helper keine Download-Action hat.
* URL-Fehler (404/Invalid)
* Auth-/Paywall-Fehler (redirect zu login, HTML statt PDF)
* Policy-Block (validate_domain blockt direct, fehlender DBIS-Session-Kontext)
* Timeout/Retry exhausted (sollte via RetryHandler sichtbar sein)
* Silent failure (Datei existiert, aber zu klein/korrupt) → dein Validator prüft „<1KB“.
„Halluzinationen“ technisch eindämmen (Guardrails, Determinismus)
* Nutze die bereits vorhandenen Realitäts-Gates erzwingend: validate_agent_execution.sh nach Phase 2/4/5 und validation_gate.py nach jedem Sub-Agent Output.
* Entferne Polling/„ich mache gleich…“-Text vor Tool-Calls (Action-First Pattern). Das ist explizit als Fix dokumentiert.
* Reduziere die Freiheitsgrade: Orchestrator sollte nicht entscheiden, wie ein Output synthetisiert wird, sondern nur „Subagent ausführen, Validate, Save State“. Deine Prompt-Regeln gehen bereits in diese Richtung, aber die Pfad- und Contract-Drifts sabotieren das; erst vereinheitlichen, dann wirkt das Gate wirklich.
Bericht 3




















Prompt-Audit für AcademicAgent
Executive Summary
Die Agent-Prompts in deinem Repository sind grundsätzlich sauber strukturiert (YAML-Frontmatter, klarer Rollen-/Phasenbezug, starke Security- und Robustness-Ideen wie Schema-Validation und Anti-Halluzinations-Regeln). Gleichzeitig gibt es mehrere harte Widersprüche zwischen (a) dem kanonischen Contract (AGENT_API_CONTRACTS.md), (b) den Prompttexten selbst, (c) dem Permission-/Tool-Layer (.claude/settings.json, action_gate.py, safe_bash.py, auto_permissions.py) und (d) der tatsächlichen Browser-Tooling-Fähigkeit (browser_cdp_helper.js). Diese Drift erzeugt genau die Failure-Klassen, die du beschrieben hattest (Agent startet/arbeitet „scheinbar“, Artefakte fehlen, PDF-Downloads passieren nicht, Permission-Spam und Orchestrator-“Halluzinationen”).
Die größten Hebel (High Impact) sind prompt-seitig sehr konkret:
* Ein Contract, ein Run-Layout, ein Dateinamen-Satz: runs/<RUN_ID>/config|metadata|downloads|outputs|logs + exakt die Dateinamen aus AGENT_API_CONTRACTS.md.
* Tool-Capability-Drift beheben: Browser- und Search-Agent müssen entweder wirklich Write besitzen und Artefakte schreiben – oder der Orchestrator muss als einziger Writer fungieren. Der Repo-Stand ist derzeit „halb/halb“ und bricht.
* PDF-Download realistisch machen: Aktueller CDP-Helper hat keine Download-Action; wget/curl sind durch Settings + Action-Gate blockiert → Prompt muss entweder ein implementiertes Download-Interface nutzen oder sauber/early failen (statt „Download behaupten“).
* Permission-Handling nicht im Prompt “herbeiwünschen”: Prompts tun so, als würde CURRENT_AGENT Auto-Approval in Claude Code „aktivieren“. Im Repo ist das primär ein lokales Script (auto_permissions.py), aber .claude/settings.json enthält breite ask-Regeln, die Permission-Spam erzwingen. Prompt-Instruktionen sollten das nicht als zuverlässig darstellen.
Unten bekommst du pro Agent: Prompt-Metadaten, präzise Schwächen, konkrete Patch-Diffs (minimal), alternative deterministische Formulierungen (Tool-First) und Guardrails (Schema-Checks, expected_output Paths, Failure Modes, Retry).
Prompt-Inventar und Metadaten
Extrahierte Agent-Prompt-Dateien
Laut Projektstruktur liegen die Agent-Prompts hier: .claude/agents/{browser,extraction,orchestrator,scoring,search,setup}-agent.md.
Globaler Permission/Tool-Rahmen
Projektweit gelten die Regeln in .claude/settings.json:
* deny: u. a. Secrets (.env, ~/.ssh) und Netzwerk-Commands (curl, wget, ssh, scp, rsync)
* allow: u. a. Write(runs/**), Tasks für alle Agents, Bash(python3 scripts/*), Bash(node scripts/*)
* ask: sehr breit (Edit, Write, Bash(*), WebFetch, WebSearch, Task(*)).
Zusätzlich erzwingt safe_bash.py vor jedem Bash-Command das action_gate.py Whitelist/Blocklist-Regime (z. B. blockiert Network-Downloads via curl/wget/fetch).
Kanonischer I/O-Contract (Soll-Zustand)
AGENT_API_CONTRACTS.md definiert ein eindeutiges Run-Layout und File Contracts (Phase 0–6), inkl. weiterer Regeln: „All JSON outputs MUST be validated via validation_gate.py“.
Kanonisches Layout (aus Contract):runs/<RUN_ID>/config/run_config.jsonruns/<RUN_ID>/metadata/{databases,search_strings,candidates,ranked_candidates}.jsonruns/<RUN_ID>/downloads/downloads.json + downloads/*.pdfruns/<RUN_ID>/outputs/{quotes,quote_library}.json + bibliography.bib (+ Reports)
Diese Contract-Realität kollidiert aktuell prompt- und script-seitig mit alternativen Namens- und Pfadwelten (projects/[ProjectName], ranked_top27.json, pdfs/, output/ statt outputs/).
Prompt-Analysen pro Agent mit Patches und Guardrails
Wichtiger Hinweis (methodisch): Ich zitiere jeweils die relevanten Prompt-Segmente und evaluiere sie gegen den kanonischen Contract + Tooling. Die vollständigen Prompts sind in den File-Quellen enthalten.
Orchestrator-Agent
Datei / Metadaten
* Pfad: .claude/agents/orchestrator-agent.md
* Tools (Frontmatter): Read, Grep, Glob, Bash, Task, Write
* Contract-Verweis: AGENT_API_CONTRACTS.md, Validation-Gate Pflicht
Was ist gutDer Prompt enthält viele richtige “Production-Grade”-Leitplanken:
* explizites Anti-Halluzinations-Verbot („DEMO-MODUS verboten“, keine synthetischen Daten)
* “Action-First”-Pattern, Retry-Pattern, Prerequisite-Guards, Output-Validation-Gate
Schwächen (präzise)
1. Widersprüchliche Dateinamen und Pfade innerhalb desselben Orchestrator-Prompts
* Früher Abschnitt beschreibt Run-Layout mit metadata/ranked_candidates.json, downloads/, outputs/quotes.json.
* Später „Phase Overview“ nutzt abweichend metadata/ranked_top27.json, pdfs/*.pdf, metadata/downloads.json, Quote_Library.csv, Annotated_Bibliography.md außerhalb outputs/. → Das ist ein klassischer Trigger für „instabil/halluziniert“, weil Preconditions und Folgephasen gegeneinander laufen.
1. CURRENT_AGENT / Auto-Permission im Prompt als “funktionierend” dargestellt (risikobehaftet)Der Prompt behauptet, export CURRENT_AGENT=... aktiviere ein Auto-Permission-System und verhindere Permission-Dialoge. Repo-real: auto_permissions.py ist ein Script mit Regex-Rules; .claude/settings.json enthält gleichzeitig breite ask-Regeln, die Permission-Prompts erzwingen. → Selbst wenn CURRENT_AGENT in einer Shell gesetzt würde, ist unklar, ob das Claude-Code-permissions beeinflusst (Hypothese: nein). Prompt sollte das als best effort behandeln, nicht als Guarantee.
2. Gemischte Semantik: Task()-Calls “in Bash-Snippets”Der Prompt zeigt „Task( … )“ in bash-artigen Pseudocode-Blöcken. → Risiko: Orchestrator generiert Text statt echten Tool-Calls oder verwechselt Execution Context.
Minimaler Patch (Diff/Zeilenänderung)Ziel: „One Contract to rule them all“ + Tool-First + eindeutige expected_output paths.
diff
Kopieren
--- a/.claude/agents/orchestrator-agent.md
+++ b/.claude/agents/orchestrator-agent.md
@@
- Run-Directory-Layout (Alle Agents schreiben hier):
- runs// ...
+ RUN LAYOUT (CANONICAL, NO ALTERNATES):
+ runs/$RUN_ID/
+   config/run_config.json
+   metadata/{databases,search_strings,candidates,ranked_candidates}.json
+   downloads/downloads.json + downloads/*.pdf
+   outputs/{quotes,quote_library}.json + outputs/bibliography.bib + outputs/*.md
@@
- Phase Overview ... Output: metadata/ranked_top27.json ... pdfs/*.pdf ... metadata/downloads.json ... Quote_Library.csv
+ Phase Overview MUST MATCH AGENT_API_CONTRACTS.md:
+ Phase 3 output: metadata/ranked_candidates.json
+ Phase 4 outputs: downloads/downloads.json + downloads/*.pdf
+ Phase 5 output: outputs/quotes.json
+ Phase 6 outputs: outputs/quote_library.json + outputs/bibliography.bib (+ reports)
@@
- Task() examples shown inside bash snippets
+ NEVER embed Task() inside bash snippets. Use:
+ 1) Bash via safe_bash.py (only for scripts)
+ 2) Task tool call as a real tool invocation (no surrounding pseudo-code)
Begründung: Contract-Wahrheit liegt in AGENT_API_CONTRACTS.md; Validator und E2E-Skripte erwarten Downloads unter runs/<RUN_ID>/downloads/ und Quotes unter outputs/.
Alternative Formulierung (deterministisch, Tool-First)Ersetze (oder ergänze) am Anfang des Orchestrator-Prompts eine „Phase Template“-Sektion:
Phase Template (MANDATORY)InputPaths = […]OutputPaths = […]Step 1: Validate prerequisites (filesystem)Step 2: Spawn subagent via Task (first action)Step 3: Validate output via python3 scripts/validation_gate.py --write-sanitizedStep 4: Run bash scripts/validate_agent_execution.sh <phase> <RUN_ID>Step 5: Update research_state.jsonStep 6: Continue immediately (no user prompt outside checkpoints)
Das ist kompatibel mit deinen bestehenden Robustness-Fixes.
Guardrails
* Explizite expected_output pro Phase: als Tabelle im Prompt (aus Contract kopiert, aber nur ein Satz).
* Hard Stop bei Path-Drift: Wenn irgendwo projects/ oder pdfs/ im Agent-return vorkommt → abort + log. (Das verhindert „alte Welt“-Rückfälle.)
* Validation-Pflichten: validation_gate.py muss auf die kanonischen Schemafiles zeigen. validation_gate.py existiert und sanitisiert Textfelder + Injection-Patterns.
Impact-Priorität: High (weil Orchestrator die gesamte Pipeline deterministisch machen oder zerstören kann).
Setup-Agent
Datei / Metadaten
* Pfad: .claude/agents/setup-agent.md
* Tools: Read, Grep, Glob, Bash, Write; Task explizit disallowed
* Output-Vertrag: „runs//config/run_config.json + _Config.md“ (im Prompt genannt)
Was ist gut
* Setup-Agent denkt bereits in „Mode“-Auswahl und iterativer Suchstrategie (frühzeitige Termination), inkl. Default-Ableitungen aus academic_context.md.
* Er erzeugt strukturiertes run_config.json (statt nur Markdown-Config) und dokumentiert erwartete Logging-Events.
Schwächen (präzise)
1. Pfad-Kollision im eigenen Prompt
* Im Prompt steht Output Contract runs//config/run_config.json, aber später steht „Write: runs/[timestamp]/run_config.json“ (ohne /config/).
* Zusätzlich existiert im Repo ein Script create_run_structure.sh, das runs/$RUN_ID/run_config.json anlegt und output/ statt outputs/ benutzt. → Setup kann „richtig“ sein, aber nachgelagerte Phasen suchen woanders.
1. Zu viele Fragen / TUI nur als ASCII-Box-SimulationDer Prompt modelliert Multi-Phase-Dialoge (Run Goal, Research Question, Target Citations, Search Intensity, Zeitraum, Strategy, Qualitätskriterien …). → Das ist UX-lastig und führt zum “zu viele Fragen”-Symptom.
Minimaler PatchZiel: Pfad eindeutig + Dialog drastisch reduzieren via Mode-Preset.
diff
Kopieren
--- a/.claude/agents/setup-agent.md
+++ b/.claude/agents/setup-agent.md
@@
- Outputs: `runs//config/run_config.json` + `_Config.md`
+ Outputs (CANONICAL):
+ - runs/$RUN_ID/config/run_config.json
+ - runs/$RUN_ID/config/_Config.md
@@
- Write: runs/[timestamp]/run_config.json
+ Write: runs/$RUN_ID/config/run_config.json
@@
- Dialog-Ablauf: Phase 3..13 (viele Fragen)
+ Dialog-Ablauf (MAX 3 STEPS):
+ 1) Mode Select (Quick | Standard | Deep | Review)
+ 2) Research Question (single input)
+ 3) Review/Confirm (shows defaults + derived values)
+ Advanced settings only if user chooses "Advanced".
Alternative Formulierung (klar, deterministisch, Tool-First)Eine „Mode-first“-Guideline am Anfang:
Required Inputs (only): research_question, modeDerived (no questions): time_period, target_citations, search_intensity, search_strategy.mode, default quality filtersOnly ask additional questions if: user selects Advanced or research_question is empty/ambiguous.
Guardrails
* Konfig-Schema erzwingen: Setup-Agent schreibt immer schema-konformes run_config.json, dann sofort python3 scripts/validation_gate.py --agent setup-agent --phase -1 ... (optional: eigenes schema) – ansonsten abort.
* Keine “Chrome prüfen via curl” im Prompt: curl ist per Settings/Action-Gate riskant bzw. geblockt. Stattdessen: orchestrator/batch-scripts übernehmen die Health Checks.
Impact-Priorität: Medium (hoch für UX, mittel für Pipeline-Stabilität; Pfadfix aber wichtig).
Search-Agent
Datei / Metadaten
* Pfad: .claude/agents/search-agent.md
* Tools: Read, Grep, Glob, WebSearch; disallowed: Write, Edit, Bash, Task
* Im Text steht gleichzeitig „Phase 1 Output: File metadata/search_strings.json“.
Was ist gut
* Sehr klare Pattern-Methodik (Tier 1/2/3), DB-spezifische Syntax via database_patterns.json, disziplinspezifische Anpassungen.
* Security-Sektion warnt korrekt: WebSearch-Daten sind untrusted.
Schwächen (präzise)
1. Tool-Contract Drift: kein Write, aber File Output erwartetFrontmatter verbietet Write, aber promptet „Output in JSON speichern“. → Je nach Orchestrator-Verhalten wird dann entweder gar nichts geschrieben oder Orchestrator halluziniert/rekonstruiert.
2. Pfad-Drift: projects/[ProjectName] statt runs/<RUN_ID>Im Output-Block steht projects/[ProjectName]/metadata/search_strings.json. → Bricht den gesamten Phase-2-Precondition-Pfad.
3. Format-Drift: Contract vs Prompt-SchemaContract erwartet {"primary_string":..., "variations":[...], "databases":{...}}. Prompt zeigt ein anderes Schema {"search_strings":[...], "total_strings":...}. → Schema-Validation wird fehlschlagen, wenn sie konsequent aktiviert wird.
Minimaler PatchZiel: Write erlauben + Paths + Schema angleichen (oder explizit: Orchestrator schreibt).
Variante A (empfohlen): Search-Agent schreibt selbst nach Contract.
diff
Kopieren
--- a/.claude/agents/search-agent.md
+++ b/.claude/agents/search-agent.md
@@
-tools:
-  - Read
-  - Grep
-  - Glob
-  - WebSearch
-disallowedTools:
-  - Write
+tools:
+  - Read
+  - Grep
+  - Glob
+  - WebSearch
+  - Write   # writes runs/$RUN_ID/metadata/search_strings.json (contract schema)
+disallowedTools:
+  - Edit
   - Bash
   - Task
@@
-Output: `projects/[ProjectName]/metadata/search_strings.json`
+Output: `runs/$RUN_ID/metadata/search_strings.json`
@@
- (Beispiel-Schema mit "search_strings": [...])
+ Use EXACT schema from AGENT_API_CONTRACTS.md (primary_string, variations, databases, timestamp).
Variante B (Alternative): Search-Agent bleibt read-only; dann muss Orchestrator den Return-JSON in die Datei schreiben + validieren. (Dann muss der Prompt alle File-Schreib-Anweisungen entfernen und „Return JSON only“ hart festnageln.)
Alternative Formulierung (deterministisch)
Generate metadata/search_strings.json in contract schema.If database-specific syntax unknown: use generic Boolean and mark "confidence": 0.5 inside databases[db].
Guardrails
* Schema-Gate: Orchestrator muss validation_gate.py gegen schemas/search_strings_schema.json laufen lassen (oder passendes Schema).
* No stale paths: Wenn im Prompt oder Output projects/ vorkommt → hard fail (stale-world detector).
Impact-Priorität: High (weil Phase 2 ohne Suchstrings häufig „startet nicht“ oder instabil wirkt).
Scoring-Agent
Datei / Metadaten
* Pfad: .claude/agents/scoring-agent.md
* Tools: Read, Grep, Glob, Write; disallowed: Bash, WebFetch, WebSearch, Task
* Prompt schreibt projects/[ProjectName]/metadata/ranked_top27.json.
Was ist gut
* Sehr klare Bewertungsrubrik + Edge-Case-Handling (0 Kandidaten, <27, Portfolio-Imbalance, missing citations).
* Offline Scoring (kein Web) ist sauber: deterministic, weniger Angriff/Noise.
Schwächen (präzise)
1. Output-Dateiname und Pfad driftetContract: runs/<id>/metadata/ranked_candidates.json. Prompt: projects/.../ranked_top27.json. → Phase 4 im Contract erwartet ranked_candidates; Browser-Agent liest teils ranked_top27; Auto-permissions ebenfalls gemischt. 
2. Score-Schema driftet (D1–D5 vs Contract keys)Contract erwartet score keys relevance, citation_impact, recency, methodology, accessibility + total_score. Prompt nutzt D1–D5 total 0–5 und Ranking via Score × log10(Citations+1). → Das ist nicht per se falsch, aber ohne Mapping bricht Schema-Validation.
Minimaler Patch
diff
Kopieren
--- a/.claude/agents/scoring-agent.md
+++ b/.claude/agents/scoring-agent.md
@@
- Output File: `projects/[ProjectName]/metadata/ranked_top27.json`
+ Output File: `runs/$RUN_ID/metadata/ranked_candidates.json`
@@
- scores: { "D1":..., "D2":..., "D3":..., "D4":..., "D5":..., "total": ... }
+ scores (contract keys):
+ { "relevance":..., "citation_impact":..., "recency":..., "methodology":..., "accessibility":... }
+ total_score = sum(scores)
@@
- total_ranked: 27
+ total_scored: <number>
+ Include field: "selection_hint": { "recommended_top_n": 27 }
Alternative Formulierung (klar, deterministisch)
Keep internal D1–D5 if you want, but export contract keys only.If citation counts missing, set citation_impact=0 and add "notes":["citation_missing"].
Guardrails
* Knockout/Edge-Case Output muss trotzdem schema-valid sein: Leere ranked-Liste ist erlaubt, aber timestamp, total_scored Pflicht. (Sonst orchestrator kann nicht unterscheiden zwischen „kein Ergebnis“ und „Bug“.)
* No interactive waits in scoring-agent: Der Prompt schreibt „Wait for user decision“ in Edge Cases. Das ist orchestrator responsibility (Checkpoint), nicht scoring-agent.
Impact-Priorität: High (weil Output-Namen/Schema hier direkt PDF-Download-Phase triggert).
Browser-Agent
Datei / Metadaten
* Pfad: .claude/agents/browser-agent.md
* Tools: Read, Grep, Glob, Bash, WebFetch
* disallowed: Write, Edit, Task
* Prompt behauptet gleichzeitig: Phase 0/2/4 „schreibt“ databases.json, candidates.json, downloads.json + PDFs.
Was ist gut
* Sehr starke Security-Haltung: External HTML untrusted; Domain-Validation; Sanitization Pflicht; Retry-Policy explizit.
* Es wird konsequent safe_bash.py gefordert (gute Enforce-Idee).
Schwächen (präzise)
1. Write-Tool ist disallowed, aber Outputs “müssen” Dateien seinDer Prompt beschreibt File Outputs (Phase 0/2/4), aber Frontmatter verbietet Write. → Das erzeugt in der Praxis „keine candidates.json / keine downloads.json“.
2. PDF-Download ist promptseitig postuliert, toolingseitig nicht vorhandenDein CDP-Helper unterstützt actions: navigate, search, extract, screenshot, inject, status – kein download. Gleichzeitig blocken Settings + Action-Gate curl/wget und externe URL-fetches über Bash. → Resultat: Phase 4 kann nicht „wirklich“ PDFs herunterladen, selbst wenn der Prompt das fordert.
3. Input-File Naming DriftAuto-permission/read-list nennt ranked_top27. Contract nennt ranked_candidates. 
Minimaler Patch (Prompt)Ziel: Capabilities ehrlich machen + Write aktivieren + Download-Failure-Mode definieren.
diff
Kopieren
--- a/.claude/agents/browser-agent.md
+++ b/.claude/agents/browser-agent.md
@@
-tools:
-  - Read
-  - Grep
-  - Glob
-  - Bash
-  - WebFetch
-disallowedTools:
-  - Write
+tools:
+  - Read
+  - Grep
+  - Glob
+  - Bash
+  - WebFetch
+  - Write   # MUST write outputs under runs/$RUN_ID/*
+disallowedTools:
   - Edit
   - Task
@@
- Phase 4 (PDF Download): Schreibt downloads/downloads.json + downloads/*.pdf
+ Phase 4 (PDF Download): MUST produce
+ - runs/$RUN_ID/downloads/downloads.json
+ - runs/$RUN_ID/downloads/*.pdf
+ If download mechanism unavailable -> return structured error:
+ { "error_type":"DownloadNotImplemented", "recommended_fix":"Implement CDP download action", ... }
@@
- Reads ranked_top27.json
+ Reads metadata/ranked_candidates.json (contract)
Alternative Formulierung (Tool-First, deterministisch)
For each phase, do:
1. Use node scripts/browser_cdp_helper.js navigate|search|extract via python3 scripts/safe_bash.py
2. Persist JSON outputs with Write into canonical paths
3. If Phase 4: if you cannot download a PDF with existing tooling, do not pretend. Write a failed entry with reason and mark status in downloads.json.
Guardrails
* Download-Failure ist ein First-Class Outcome: downloads.json muss pro DOI status=failed + reason enthalten, nicht “silent ignore”. Contract ist schon nahe dran (status, failed_dois).
* Hard dependency check: browser-agent soll vor Phase 4 prüfen, ob browser_cdp_helper.js eine Download-Action hat. Wenn nicht: early fail + Orchestrator checkpoint. (Das verhindert “keine PDFs, aber weiter”).
Impact-Priorität: High (weil es direkt „keine PDF-Downloads“ erklärt).
Extraction-Agent
Datei / Metadaten
* Pfad: .claude/agents/extraction-agent.md
* Tools: Read, Grep, Glob, Write; disallowed: Bash, WebFetch, WebSearch, Task
* Output: runs//outputs/quotes.json (im Prompt), Contract: outputs/quotes.json.
Was ist gut
* Sehr klare “0-Toleranz für erfundene Zitate”, Seitenzahlpflicht, und Security: PDF untrusted, pdf_security_validator Pflicht.
Schwächen (präzise)
1. Input-Pfad driftet: downloads vs pdfs vs projectsContract: input PDFs liegen unter runs/<id>/downloads/*.pdf. Prompt: nennt runs//pdfs/*.pdf in Auto-permission und projects/[ProjectName]/pdfs/*.pdf im Workflow. → Das bricht Phase 5 sofort, selbst wenn PDFs korrekt downloadd wurden.
2. Bash disallowed, aber Prompt beschreibt pdftotext-AktivitätenFrontmatter sagt: „PDF processing via scripts called by orchestrator“ – gut. Aber Prompt formuliert „Du führst aus: PDF → Text-Konvertierung (pdftotext)“. → Das ist widersprüchlich; führt zu Erwartungsfehlern (“warum macht agent das nicht?”).
Minimaler Patch
diff
Kopieren
--- a/.claude/agents/extraction-agent.md
+++ b/.claude/agents/extraction-agent.md
@@
- Read (Auto-Allowed): - runs//pdfs/*.pdf
+ Read: - runs/$RUN_ID/downloads/*.pdf
@@
- Phase 5 Input - projects/[ProjectName]/pdfs/*.pdf
+ Phase 5 Input - runs/$RUN_ID/downloads/*.pdf
@@
- "Du führst aus: PDF → Text-Konvertierung (pdftotext)"
+ PDF->Text conversion is orchestrator responsibility (Bash via safe_bash.py).
+ extraction-agent reads prepared text in runs/$RUN_ID/txt/*.txt or reads PDFs only if text already available.
Alternative Formulierung (deterministisch)
Precondition: runs/$RUN_ID/downloads/*.pdf exists and passes pdf_security_validator.If not: write outputs/quotes.json as empty with error summary and ask orchestrator to checkpoint.
Guardrails
* Quote Schema: quotes müssen page/page_number konsistent setzen (Validator prüft u. a. Seitenzahl-Fehlen als Warnung in validate_agent_execution.sh).
* Skip-Logik: Bei korrupten PDFs: errors/extraction_error_*.json schreiben (Prompt nennt das bereits), aber Pfade müssen dem Run-Layout entsprechen.
Impact-Priorität: Medium (Phase 5 bricht sonst; aber oft scheitert es schon früher an Downloads).
Cross-Cutting Findings und Root-Cause-Cluster
Contract-Drift als primärer Stabilitätskiller
Du hast mindestens vier parallele “Wahrheiten” im Repo:
* Kanonisch: AGENT_API_CONTRACTS.md (runs/config|metadata|downloads|outputs)
* Orchestrator-Prompt: teilweise kanonisch, teilweise ranked_top27.json, pdfs/, CSV-Outputs
* Subagent-Prompts: teils projects/[ProjectName], teils runs// Platzhalter
* Scripts: create_run_structure.sh erzeugt output/ statt outputs/ und legt run_config.json im Run-Root an, plus initialisiert zentrale JSON-Files als [] statt schema-konformer Objekte.
Solange diese Drift existiert, treten “Halluzinationen” technisch als Fehlannahmen auf: der Orchestrator „glaubt“, Inputs existieren oder wurden erzeugt, während er nur Placeholder-Files vorfindet.
PDF-Download ist aktuell promptseitig versprochen, toolingseitig nicht implementiert
* browser_cdp_helper.js hat keine Download-Action.
* curl/wget werden durch Settings und Action Gate geblockt.
* Validator erwartet PDFs in runs/<id>/downloads/*.pdf und failt hart auf „0 PDFs“.
Das ist keine “Prompt-Feinheit”, sondern eine harte Feature-Lücke: Prompt muss entweder (a) Download-Mechanismus korrekt ansprechen oder (b) “DownloadNotImplemented” sauber melden.
Permission-Spam wird durch Settings erzwungen, nicht durch Prompts gelöst
.claude/settings.json hat ask für Write und Bash(*) und Task(*). Prompts verlassen sich auf auto_permissions.py + CURRENT_AGENT, aber das ist in Repo-Stand kein zuverlässiger Ersatz für die Claude Code Permission Evaluation (mindestens: die breiten ask-Regeln werden nicht “weggezaubert”).
Priorisierte Änderungen als Tabelle
Agent	Dateipfad	Hauptproblem(e)	Konkrete Änderung (Datei + Patch)	Priorität	Test-Check
orchestrator-agent	.claude/agents/orchestrator-agent.md	Interne Pfad-/Dateinamen-Widersprüche (ranked_top27/pdfs/CSV vs Contract), Task-in-Bash-Pseudocode, Auto-permission als “Guarantee”	Canonical run layout erzwingen; Phase Overview auf Contract umstellen; Task nicht in Bash zeigen	High	bash scripts/validate_agent_execution.sh 4 <RUN_ID> muss PDFs zählen; python3 scripts/validation_gate.py --agent browser-agent --phase 2 ... muss bestehen
setup-agent	.claude/agents/setup-agent.md	Write-Pfad driftet (config/run_config.json vs run_config.json), zu viele Fragen	Outputs auf runs/$RUN_ID/config/ vereinheitlichen; Setup auf 3 Schritte reduzieren (Mode, Frage, Confirm)	Med	Nach Setup existiert runs/<id>/config/run_config.json und validation_gate.py validiert Schema
search-agent	.claude/agents/search-agent.md	Kein Write-Tool, aber file output erwartet; projects/-Pfad; Schema driftet	Write erlauben oder Return-only clean machen; Pfad auf runs/$RUN_ID/metadata/search_strings.json; Contract-Schema verwenden	High	python3 scripts/validation_gate.py --agent search-agent --phase 1 --output-file runs/<id>/metadata/search_strings.json --schema schemas/...
scoring-agent	.claude/agents/scoring-agent.md	ranked_top27 vs ranked_candidates; projects/-Pfad; D1–D5 vs Contract keys	Output file + schema mapping auf Contract; interaktive waits entfernen (checkpoint nur orchestrator)	High	validation_gate.py auf ranked_candidates; Orchestrator findet Phase-4-Input ohne Pfad-Magie
browser-agent	.claude/agents/browser-agent.md	Write disallowed aber muss Artefakte schreiben; PDF-Download-Mechanik fehlt in Tooling	Write erlauben; Phase-4 Failure Mode “DownloadNotImplemented”; Input auf ranked_candidates; Download action check	High	bash scripts/validate_agent_execution.sh 4 <RUN_ID>: PDFs >0 und downloads.json vorhanden
extraction-agent	.claude/agents/extraction-agent.md	Input-Pfad driftet (pdfs/projects vs downloads/runs); widersprüchliche pdftotext-Verantwortung	Input auf runs/$RUN_ID/downloads/*.pdf; Conversion responsibility klären; outputs/quotes.json fix	Med	bash scripts/validate_agent_execution.sh 5 <RUN_ID>: outputs/quotes.json vorhanden, Seitenzahlen plausibel
Optionales Mermaid-Flowchart für Orchestrator → Subagents
#mermaid-rd9{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#333;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-rd9 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-rd9 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-rd9 .error-icon{fill:#552222;}#mermaid-rd9 .error-text{fill:#552222;stroke:#552222;}#mermaid-rd9 .edge-thickness-normal{stroke-width:1px;}#mermaid-rd9 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-rd9 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-rd9 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-rd9 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-rd9 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-rd9 .marker{fill:#333333;stroke:#333333;}#mermaid-rd9 .marker.cross{stroke:#333333;}#mermaid-rd9 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-rd9 p{margin:0;}#mermaid-rd9 .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#333;}#mermaid-rd9 .cluster-label text{fill:#333;}#mermaid-rd9 .cluster-label span{color:#333;}#mermaid-rd9 .cluster-label span p{background-color:transparent;}#mermaid-rd9 .label text,#mermaid-rd9 span{fill:#333;color:#333;}#mermaid-rd9 .node rect,#mermaid-rd9 .node circle,#mermaid-rd9 .node ellipse,#mermaid-rd9 .node polygon,#mermaid-rd9 .node path{fill:#ECECFF;stroke:#9370DB;stroke-width:1px;}#mermaid-rd9 .rough-node .label text,#mermaid-rd9 .node .label text,#mermaid-rd9 .image-shape .label,#mermaid-rd9 .icon-shape .label{text-anchor:middle;}#mermaid-rd9 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-rd9 .rough-node .label,#mermaid-rd9 .node .label,#mermaid-rd9 .image-shape .label,#mermaid-rd9 .icon-shape .label{text-align:center;}#mermaid-rd9 .node.clickable{cursor:pointer;}#mermaid-rd9 .root .anchor path{fill:#333333!important;stroke-width:0;stroke:#333333;}#mermaid-rd9 .arrowheadPath{fill:#333333;}#mermaid-rd9 .edgePath .path{stroke:#333333;stroke-width:2.0px;}#mermaid-rd9 .flowchart-link{stroke:#333333;fill:none;}#mermaid-rd9 .edgeLabel{background-color:rgba(232,232,232, 0.8);text-align:center;}#mermaid-rd9 .edgeLabel p{background-color:rgba(232,232,232, 0.8);}#mermaid-rd9 .edgeLabel rect{opacity:0.5;background-color:rgba(232,232,232, 0.8);fill:rgba(232,232,232, 0.8);}#mermaid-rd9 .labelBkg{background-color:rgba(232, 232, 232, 0.5);}#mermaid-rd9 .cluster rect{fill:#ffffde;stroke:#aaaa33;stroke-width:1px;}#mermaid-rd9 .cluster text{fill:#333;}#mermaid-rd9 .cluster span{color:#333;}#mermaid-rd9 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(80, 100%, 96.2745098039%);border:1px solid #aaaa33;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-rd9 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#333;}#mermaid-rd9 rect.text{fill:none;stroke-width:0;}#mermaid-rd9 .icon-shape,#mermaid-rd9 .image-shape{background-color:rgba(232,232,232, 0.8);text-align:center;}#mermaid-rd9 .icon-shape p,#mermaid-rd9 .image-shape p{background-color:rgba(232,232,232, 0.8);padding:2px;}#mermaid-rd9 .icon-shape rect,#mermaid-rd9 .image-shape rect{opacity:0.5;background-color:rgba(232,232,232, 0.8);fill:rgba(232,232,232, 0.8);}#mermaid-rd9 .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#mermaid-rd9 .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#mermaid-rd9 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}
	writes runs/RUN_ID/config/run_config.json
Phase 0 Task	writes metadata/databases.json
Phase 1 Task	writes metadata/search_strings.json
Phase 2 Task	writes metadata/candidates.json
Phase 3 Task	writes metadata/ranked_candidates.json
Phase 4 Task	writes downloads/downloads.json + PDFs
Phase 5 Task	writes outputs/quotes.json	Phase 6	writes quote_library.json + bibliography.bib + reports
User: /academicagent
setup-agent
orchestrator-agent
browser-agent
search-agent
browser-agent
scoring-agent
browser-agent
extraction-agent
finalization scripts
Complete
Code anzeigen
Rückfragen
Hypothese 1: Nutzt du lokale CLI-Variante von Claude Code oder die Web-Variante (claude.ai/code)? (Das ist relevant, weil Settings/Agent-Personas teils anders angewendet werden können; dein Repo verlässt sich stark auf .claude/settings.json.)
Hypothese 2: Willst du als Design-Entscheidung, dass alle Subagents selbst Dateien schreiben (Write-Tool), oder soll nur der Orchestrator schreiben und Subagents liefern Return-JSON? Der Repo-Stand ist gemischt und das ist ein Root-Cause-Generator.
Hypothese 3: Soll Phase 4 wirklich per Browser-CDP downloaden (mit Session/Cookies), oder akzeptierst du einen HTTP-Fallback via WebFetch? (Aktuell blocken Action-Gate/Settings viele Netzwerkpfade; CDP-Helper hat keinen Download.)

User: /academicagent	setup-agent	orchestrator-agent	browser-agent	search-agent	browser-agent	scoring-agent	browser-agent	extraction-agent	finalization scripts


