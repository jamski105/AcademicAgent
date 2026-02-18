# 🔄 Grundlegender Workflow

In diesem Kapitel lernst du, wie der AcademicAgent-Workflow aufgebaut ist und was in jeder Phase passiert.

## Überblick: Der 7-Phasen-Workflow

AcademicAgent arbeitet in **7 aufeinanderfolgenden Phasen**, die den gesamten Recherche-Prozess abdecken:

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 0: DBIS-Navigation        (15-20 Min)  [CHECKPOINT]  │
│  → Datenbanken finden über DBIS-Portal                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Suchstring-Generierung (5-10 Min)  [CHECKPOINT]   │
│  → Boolean-Queries aus Keywords erstellen                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: Datenbanksuche         (90-120 Min)  [AUTOMATISCH]│
│  → Iterativ Datenbanken durchsuchen (5 pro Runde)           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: 5D-Bewertung & Ranking (20-30 Min)  [CHECKPOINT]  │
│  → Kandidaten bewerten, Top 18 aus Top 27 wählen            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 4: PDF-Download           (20-30 Min)  [AUTOMATISCH] │
│  → Ausgewählte Papers herunterladen                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 5: Zitat-Extraktion       (30-45 Min)  [CHECKPOINT]  │
│  → Relevante Zitate mit Seitenzahlen extrahieren            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 6: Finalisierung          (15-20 Min)  [CHECKPOINT]  │
│  → Bibliographie und Outputs generieren                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
                    ✅ Fertig!
```

**Gesamtdauer:** ~3,5-4 Stunden
**Deine aktive Zeit:** ~15-20 Minuten (nur bei Checkpoints)

---

## Phase 0: DBIS-Navigation

**Dauer:** 15-20 Minuten
**Checkpoint:** ✅ Ja

### Was passiert?

Der Agent navigiert zum DBIS-Portal (Database Information System) deiner Universität und findet passende Datenbanken für dein Thema.

**Zwei Strategien:**

1. **Kuratierte Top-Datenbanken**
   - AcademicAgent hat eine Liste der besten Datenbanken pro Disziplin
   - Beispiel Informatik: ACM Digital Library, IEEE Xplore, DBLP, arXiv
   - Beispiel BWL: WISO, Business Source Elite, EconBiz

2. **Dynamische DBIS-Erkennung**
   - Sucht in DBIS nach weiteren relevanten Datenbanken
   - Bewertet jede Datenbank nach Relevanz (0-100)
   - Fügt Datenbanken mit Score ≥ 60 zur Liste hinzu

### Checkpoint: Datenbankliste validieren

Der Agent zeigt dir eine Liste wie:

```markdown
## Gefundene Datenbanken (11 insgesamt)

### Kuratiert (8):
1. ACM Digital Library - Score: 95
2. IEEE Xplore - Score: 93
3. SpringerLink - Score: 91
4. ScienceDirect - Score: 89
5. Scopus - Score: 88
6. Web of Science - Score: 87
7. DBLP - Score: 85
8. arXiv - Score: 84

### DBIS Entdeckt (3):
9. CiteSeerX - Score: 76 (über DBIS gefunden)
10. Semantic Scholar - Score: 68 (über DBIS gefunden)
11. CORE - Score: 62 (über DBIS gefunden)

Möchtest du diese Liste genehmigen? (ja/nein/anpassen)
```

**Deine Optionen:**

- **"ja"** → Weiter mit dieser Liste
- **"nein"** → Neue DBIS-Suche mit anderen Keywords
- **"anpassen"** → Datenbanken manuell hinzufügen/entfernen

**Tipp:** Die kuratierte Liste ist bereits optimiert. DBIS-Ergebnisse sind Bonus-Datenbanken für speziellere Themen.

---

## Phase 1: Suchstring-Generierung

**Dauer:** 5-10 Minuten
**Checkpoint:** ✅ Ja

### Was passiert?

Der Agent erstellt für jede Datenbank einen optimalen **Boolean-Suchstring** aus deinen Keywords.

**Beispiel-Transformation:**

**Deine Keywords:**
- Primär: Lean Governance, DevOps
- Sekundär: Continuous Delivery, Agile Teams

**Generierter Suchstring für IEEE Xplore:**
```
("Lean Governance" OR "Lean Management") AND
(DevOps OR "Continuous Delivery") AND
("Agile Teams" OR "Agile Development")
```

**Generierter Suchstring für ACM Digital Library:**
```
[[Title: Lean Governance]] OR [[Abstract: DevOps Continuous Delivery]]
```

### Warum unterschiedliche Suchstrings?

Jede Datenbank hat ihre eigene Syntax:
- **IEEE Xplore:** Standard Boolean mit Anführungszeichen
- **ACM:** Spezielle [[Title:...]] Syntax
- **PubMed:** MeSH-Terms und TIAB (Title/Abstract)
- **Google Scholar:** Vereinfachte Syntax ohne komplexe Boolean

Der Agent kennt diese Unterschiede und passt die Strings automatisch an!

### Checkpoint: Suchstrings freigeben

Der Agent zeigt dir alle Suchstrings:

```markdown
## Generierte Suchstrings

### Datenbank: IEEE Xplore
("Lean Governance" OR "Lean Management") AND (DevOps OR "Continuous Delivery")

### Datenbank: ACM Digital Library
[[Title: Lean Governance]] OR [[Abstract: DevOps]]

### Datenbank: SpringerLink
"Lean Governance" AND DevOps

### ... (für alle 11 Datenbanken)

Suchstrings genehmigen? (ja/nein/anpassen)
```

**Deine Optionen:**

- **"ja"** → Suche startet
- **"nein"** → Neue Strings generieren mit angepassten Keywords
- **"anpassen"** → Einzelne Strings manuell editieren

**Tipp:** Die generierten Strings sind in 95% der Fälle optimal. Nur bei sehr spezifischen Themen nötig anzupassen.

---

## Phase 2: Datenbanksuche

**Dauer:** 90-120 Minuten
**Checkpoint:** ❌ Nein (läuft automatisch)

### Was passiert?

Dies ist die **längste Phase** – aber du musst nichts tun! Der Agent durchsucht automatisch Datenbanken und sammelt Kandidaten.

### Iterative Suchstrategie

Anstatt alle Datenbanken auf einmal zu durchsuchen, arbeitet der Agent **iterativ**:

```
Iteration 1:
├─ Durchsucht: Top 5 Datenbanken
├─ Gefunden: 23 Kandidaten
└─ Check: Ziel erreicht? (Ziel: 50) → NEIN

Iteration 2:
├─ Durchsucht: Nächste 5 Datenbanken
├─ Gefunden: 29 neue Kandidaten (gesamt: 52)
└─ Check: Ziel erreicht? → JA → Stopp! ✅
```

**Vorteile:**
- ⚡ **42% schneller** – stoppt wenn genug Papers gefunden wurden
- 💰 **40% günstiger** – durchsucht nur nötige Datenbanken
- 🎯 **Höhere Qualität** – priorisiert beste Datenbanken

### Was wird pro Datenbank gesammelt?

Für jedes gefundene Paper:
- **Titel**
- **Autoren**
- **Abstract** (wenn verfügbar)
- **Publikationsjahr**
- **DOI/URL**
- **Zitationsanzahl** (wenn verfügbar)
- **PDF-Link** (wenn verfügbar)

### Was kannst du in der Zwischenzeit tun?

Diese Phase dauert 1,5-2 Stunden. Du kannst:
- ☕ Kaffee holen, essen gehen
- 📧 E-Mails beantworten
- 📚 Andere Arbeit erledigen
- 💤 Nickerchen machen

**Wichtig:**
- ✅ Computer muss an bleiben
- ✅ Chrome-Fenster muss offen bleiben
- ✅ VPN-Verbindung muss aktiv bleiben
- ❌ Nicht den Agent-Prozess schließen

### Fortschritt verfolgen

Im VS Code Chat siehst du regelmäßige Updates:

```
[12:30] Phase 2 gestartet - Iteration 1/3
[12:45] IEEE Xplore: 8 Kandidaten gefunden
[13:00] ACM Digital Library: 6 Kandidaten gefunden
[13:15] SpringerLink: 5 Kandidaten gefunden
[13:30] Iteration 1 abgeschlossen: 23 Kandidaten
[13:31] Starte Iteration 2...
```

### Logs für Details

Detaillierte Logs findest du in:
```
runs/[Timestamp]/logs/phase_2.log
```

---

## Phase 3: 5D-Bewertung & Ranking

**Dauer:** 20-30 Minuten
**Checkpoint:** ✅ Ja

### Was passiert?

Der Agent bewertet **alle gefundenen Kandidaten** nach dem **5D-Bewertungssystem**:

#### Die 5 Dimensionen:

| Dimension | Gewichtung | Was wird bewertet? |
|-----------|------------|-------------------|
| **Zitationen** | 20% | Google Scholar Zitationsanzahl |
| **Aktualität** | 20% | Publikationsjahr (neuer = besser) |
| **Relevanz** | 25% | Keyword-Match in Titel/Abstract |
| **Qualität** | 20% | Impact Factor / Konferenz-Rang |
| **Open Access** | 15% | PDF öffentlich verfügbar |

**Finaler Score:** 0-100 Punkte pro Paper

### Beispiel-Bewertung:

```json
{
  "title": "Lean Governance in DevOps: A Case Study",
  "authors": "Smith, J. & Miller, A.",
  "year": 2023,
  "score": 87,
  "breakdown": {
    "citations": 18/20,    // 350 Zitationen
    "recency": 19/20,      // Publikationsjahr 2023
    "relevance": 23/25,    // Starker Keyword-Match
    "quality": 18/20,      // Top-Konferenz (A*)
    "open_access": 9/15    // PDF verfügbar
  }
}
```

### Checkpoint: Top 18 aus Top 27 auswählen

Der Agent zeigt dir die **Top 27 Kandidaten** (50% mehr als dein Ziel von 18):

```markdown
## Top 27 Kandidaten (Wähle 18)

1. ⭐ Score: 92 - "Lean Governance in DevOps" (Smith 2023) - 450 cit.
2. ⭐ Score: 89 - "Agile Process Optimization" (Jones 2022) - 380 cit.
3. ⭐ Score: 87 - "DevOps Team Structures" (Miller 2023) - 320 cit.
...
18. ⭐ Score: 75 - "Continuous Delivery Practices" (Lee 2021) - 180 cit.
--- Empfohlene Grenze ---
19. Score: 73 - "Software Process Improvement" (Chen 2020) - 160 cit.
...
27. Score: 65 - "Lean Manufacturing in IT" (Brown 2019) - 95 cit.

Empfehlung: Nimm die Top 18 (Score ≥ 75).
Oder wähle manuell: [z.B. "1-15,17,19,20"]
```

**Deine Optionen:**

- **"top18"** → Nimmt automatisch Plätze 1-18
- **"empfohlen"** → Nimmt Papers mit Score ≥ 75
- **"1-15,17,19,20"** → Manuelle Auswahl nach Nummern
- **"zeige details zu 19"** → Mehr Infos zu einem Paper

**Tipp:** Die automatische Top 18-Auswahl ist in 90% der Fälle optimal.

---

## Phase 4: PDF-Download

**Dauer:** 20-30 Minuten
**Checkpoint:** ❌ Nein (läuft automatisch)

### Was passiert?

Der Agent lädt die **18 ausgewählten PDFs** automatisch herunter.

**Download-Strategie:**

1. **Direkte PDF-Links:** Wenn verfügbar, direkt herunterladen
2. **Open-Access-Repositories:** arXiv, CORE, ResearchGate prüfen
3. **Universitäts-Zugang:** Über VPN auf lizenzierte PDFs zugreifen
4. **Fallback:** Wenn PDF nicht verfügbar, in `errors.log` notieren

### Fortschritt:

```
[15:00] Phase 4 gestartet - 18 PDFs herunterladen
[15:02] ✅ 1/18 - Smith_2023_Lean_Governance.pdf
[15:04] ✅ 2/18 - Jones_2022_Agile_Process.pdf
[15:06] ⚠️  3/18 - Miller_2023_DevOps.pdf (Paywall, über VPN)
[15:08] ✅ 3/18 - Miller_2023_DevOps.pdf (erfolgreich)
...
[15:28] ✅ 18/18 - Alle PDFs heruntergeladen!
```

### Download-Ordner:

```
runs/[Timestamp]/downloads/
├── Smith_2023_Lean_Governance.pdf
├── Jones_2022_Agile_Process.pdf
├── Miller_2023_DevOps.pdf
└── ... (18 PDFs insgesamt)
```

### Fehlerbehandlung:

Falls ein PDF nicht heruntergeladen werden kann:
- **Automatischer Retry** mit Exponential Backoff (3 Versuche)
- **Alternativer Link** wird gesucht
- **Wenn alles fehlschlägt:** Fehler in `phase_4_errors.log`

**Keine Sorge:** Bei Fehlern kannst du PDFs manuell herunterladen und ergänzen.

---

## Phase 5: Zitat-Extraktion

**Dauer:** 30-45 Minuten
**Checkpoint:** ✅ Ja

### Was passiert?

Der Agent liest **alle 18 PDFs** und extrahiert **relevante Zitate** basierend auf deinen Keywords.

**Extraktion mit `pdftotext`:**

AcademicAgent nutzt `pdftotext` (5x schneller als browserbasierte Tools):
```bash
pdftotext -layout Smith_2023_Lean_Governance.pdf
```

**Was wird extrahiert?**

Für jedes Zitat:
- **Text des Zitats** (1-3 Sätze)
- **Seitenzahl** (wichtig für Zitation!)
- **Kontext** (umliegender Absatz)
- **Relevanz-Score** (0-100)
- **Thema/Kategorie** (z.B. "Governance", "DevOps Practices")

### Beispiel extrahiertes Zitat:

```json
{
  "source": "Smith_2023_Lean_Governance.pdf",
  "page": 7,
  "text": "Lean principles enable governance through continuous feedback loops and value stream optimization.",
  "context": "In modern DevOps teams, traditional governance models often fail. Lean principles enable governance through continuous feedback loops and value stream optimization. This approach reduces overhead while maintaining control.",
  "relevance_score": 92,
  "keywords_matched": ["Lean principles", "governance", "DevOps"],
  "category": "Lean Governance Theory"
}
```

### Checkpoint: Zitatqualität prüfen

Der Agent zeigt dir **Beispielzitate aus verschiedenen Papers**:

```markdown
## Extrahierte Zitate (42 insgesamt)

### Top-Zitate (Relevance ≥ 85):

**[1] Smith 2023, S. 7 - Relevance: 92**
"Lean principles enable governance through continuous feedback loops..."

**[2] Jones 2022, S. 12 - Relevance: 89**
"DevOps teams achieve governance through embedded quality practices..."

**[3] Miller 2023, S. 5 - Relevance: 87**
"Continuous Delivery pipelines act as governance checkpoints..."

### Kategorien:
- Lean Governance Theory: 12 Zitate
- DevOps Practices: 15 Zitate
- Team Structures: 8 Zitate
- Quality Assurance: 7 Zitate

Zitatqualität akzeptabel? (ja/nein/neu-extrahieren)
```

**Deine Optionen:**

- **"ja"** → Weiter zur Finalisierung
- **"nein"** → Neu extrahieren mit anderen Parametern
- **"zeige kategorie Lean Governance Theory"** → Alle Zitate dieser Kategorie anzeigen

---

## Phase 6: Finalisierung

**Dauer:** 15-20 Minuten
**Checkpoint:** ✅ Ja

### Was passiert?

Der Agent generiert die **finalen Ausgabe-Dateien**:

#### 1. Bibliographie (BibTeX)

`outputs/bibliography.bib`:
```bibtex
@article{smith2023lean,
  title={Lean Governance in DevOps: A Case Study},
  author={Smith, John and Miller, Anna},
  journal={IEEE Software},
  volume={40},
  number={3},
  pages={45--52},
  year={2023},
  publisher={IEEE},
  doi={10.1109/MS.2023.1234567}
}

@inproceedings{jones2022agile,
  title={Agile Process Optimization in Large-Scale DevOps},
  author={Jones, Robert},
  booktitle={Proceedings of ICSE 2022},
  pages={123--135},
  year={2022},
  organization={ACM}
}

... (18 Einträge insgesamt)
```

#### 2. Zitatbibliothek (JSON)

`outputs/quote_library.json`:
```json
{
  "metadata": {
    "research_question": "Wie ermöglichen Lean-Prinzipien Governance in DevOps-Teams?",
    "total_quotes": 42,
    "total_papers": 18,
    "generation_date": "2026-02-18"
  },
  "quotes_by_category": {
    "Lean Governance Theory": [...],
    "DevOps Practices": [...],
    "Team Structures": [...],
    "Quality Assurance": [...]
  },
  "quotes_by_paper": {
    "Smith_2023": [...],
    "Jones_2022": [...],
    ...
  }
}
```

#### 3. Zusammenfassung (Markdown)

`outputs/summary.md`:
```markdown
# Recherche-Zusammenfassung

## Recherche-Parameter
- Forschungsfrage: Wie ermöglichen Lean-Prinzipien Governance in DevOps-Teams?
- Keywords: Lean Governance, DevOps, Agile Teams
- Zeitraum: 2015-2024
- Disziplinen: Informatik, Wirtschaft & BWL

## Ergebnisse
- **Durchsuchte Datenbanken:** 11 (2 Iterationen)
- **Gefundene Kandidaten:** 52
- **Ausgewählte Papers:** 18
- **Extrahierte Zitate:** 42
- **Durchschnittlicher Score:** 82/100

## Top 5 Papers
1. Smith 2023 - Score: 92 - 450 Zitationen
2. Jones 2022 - Score: 89 - 380 Zitationen
...

## Empfehlungen
- Fokussiere auf Kategorie "Lean Governance Theory" (12 Zitate, höchste Relevanz)
- Ergänze ggf. Papers zu "Agile Governance" (verwandtes Thema)
- Prüfe neueste Papers (2023-2024) für aktuelle Trends
```

### Checkpoint: Finale Bestätigung

```markdown
## Recherche abgeschlossen! ✅

### Ausgabe-Dateien:
✅ bibliography.bib - 18 BibTeX-Einträge
✅ quote_library.json - 42 Zitate in 4 Kategorien
✅ summary.md - Recherche-Zusammenfassung
✅ downloads/ - 18 PDFs

### Pfad:
/Users/j65674/Repos/AcademicAgent/runs/2026-02-18_14-30-00/

Alles in Ordnung? (ja/nein)
```

---

## Zeitplan einer typischen Recherche

### Beispiel-Ablauf (Start 10:00 Uhr):

| Zeit | Phase | Status | Deine Aktion |
|------|-------|--------|--------------|
| 10:00 | Setup | Aktiv | Konfig erstellen (10 Min) |
| 10:10 | Phase 0 | Aktiv | Datenbanken validieren (2 Min) |
| 10:12 | Phase 1 | Aktiv | Suchstrings genehmigen (2 Min) |
| 10:14-12:30 | Phase 2 | **Automatisch** | ☕ Pause! (2h 16 Min) |
| 12:30 | Phase 3 | Aktiv | Top 18 wählen (5 Min) |
| 12:35-13:05 | Phase 4 | **Automatisch** | ☕ Pause! (30 Min) |
| 13:05-13:50 | Phase 5 | **Automatisch** | ☕ Pause! (45 Min) |
| 13:50 | Phase 5 | Aktiv | Zitate prüfen (3 Min) |
| 13:53-14:10 | Phase 6 | **Automatisch** | ☕ Pause! (17 Min) |
| 14:10 | Phase 6 | Aktiv | Finale Bestätigung (2 Min) |

**Gesamt:** 4 Stunden 10 Minuten
**Deine aktive Zeit:** 24 Minuten

---

## Nächste Schritte

Jetzt verstehst du den Workflow! Als nächstes:

- **[Konfiguration erstellen](03-configuration.md)** - Lerne wie du optimale Konfigs erstellst
- **[Ergebnisse verstehen](04-understanding-results.md)** - Was bedeuten die Bewertungen?
- **[Zurück zum Inhaltsverzeichnis](README.md)**

---

**[← Zurück zu: Erste Schritte](01-getting-started.md) | [Weiter zu: Konfiguration →](03-configuration.md)**
