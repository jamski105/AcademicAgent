# DBIS Integrations-Anleitung

## Übersicht

Das Database Information System (DBIS) ist ein umfassender Katalog wissenschaftlicher Datenbanken. Der Agent nutzt DBIS, um dynamisch zusätzliche relevante Datenbanken zu entdecken.

## DBIS URLs

### Hauptzugriff
- **DBIS Homepage**: https://dbis.ur.de
- **TIB Hannover Zugang**: https://dbis.ur.de/UBTIB
- **Suche**: https://dbis.ur.de/UBTIB/suche

### Such-URLs
```
# Suche nach Keyword
https://dbis.ur.de/UBTIB/suche?q={keyword}

# Suche nach Fachgebiet
https://dbis.ur.de/UBTIB/fachgebiet/{fach}

# Beispiele:
https://dbis.ur.de/UBTIB/suche?q=machine+learning
https://dbis.ur.de/UBTIB/fachgebiet/Informatik
```

## Agent Workflow: DBIS-Suche

### Schritt 1: Initiale Recherche
1. Benutzeranfrage analysieren → Thema & Disziplin extrahieren
2. Prüfe `database_disciplines.yaml` für Top-Datenbanken der Disziplin

### Schritt 2: DBIS-Zusatzrecherche
Wenn mehr Datenbanken benötigt werden:

```python
1. Öffne DBIS-Suche: https://dbis.ur.de/UBTIB/suche?q={research_topic}
2. Analysiere Suchergebnisse
3. Für jede relevante Datenbank:
   - Titel extrahieren
   - Kurzbeschreibung lesen (enthält Fachgebiet, Inhalt, Zugang)
   - URL zur Datenbank extrahieren
   - Zugangsinfo (frei/lizenzpflichtig) notieren
```

### Schritt 3: Relevanz-Bewertung
Für jede gefundene DBIS-Datenbank:

```
Score = 0

# DBIS-Beschreibung analysieren
IF Thema in Beschreibung: Score += 30
IF Disziplin in Beschreibung: Score += 25
IF relevante Keywords: Score += 15

# Zugang
IF Open Access: Score += 10
IF Lizenziert: Score += 5

# Qualitätsindikatoren
IF "peer-reviewed": Score += 10
IF "international": Score += 5

Relevanz-Score = min(Score, 100)
```

### Schritt 4: Ergebnis zusammenstellen
```
Top-Datenbanken aus YAML (score 90-100)
+
Relevante DBIS-Funde (score >= 60)
→ Sortiert nach Score
→ Top 5-10 Datenbanken empfehlen
```

## DBIS-Webseiten Struktur

### Suchergebnisseite
```html
<div class="result-list">
  <div class="result-item">
    <h3 class="db-title">
      <a href="/UBTIB/resources/{id}">Datenbankname</a>
    </h3>
    <p class="db-description">
      Kurzbeschreibung mit Fachgebiet und Inhalt...
    </p>
    <span class="access-info">
      <!-- frei zugänglich / lizenzpflichtig / teilweise frei -->
    </span>
  </div>
</div>
```

### Datenbankdetailseite
- **URL**: `https://dbis.ur.de/UBTIB/resources/{dbis_id}`
- **Inhalt**:
  - Vollständige Beschreibung
  - Fachgebiete
  - Inhaltstypen (Volltexte, Abstracts, etc.)
  - Zugang (frei/lizenziert)
  - Link zur eigentlichen Datenbank

## Beispiel-Workflow

### Anfrage: "Ich suche Paper zu Machine Learning in der Medizin"

#### 1. YAML Top-Datenbanken
```yaml
- PubMed (Medicine, Score: 95)
- IEEE Xplore (Computer Science, Score: 95)
- arXiv (CS/Math/Physics, Score: 85)
```

#### 2. DBIS-Suche
```
URL: https://dbis.ur.de/UBTIB/suche?q=machine+learning+medizin

Gefundene Datenbanken:
1. "Nature Machine Intelligence" (Score: 85)
   - Description: "Papers on ML applications in science and medicine"
   - Access: Subscription
   - Relevant: Ja

2. "MEDLINE" (Score: 75)
   - Description: "Biomedical literature database"
   - Access: Free via PubMed
   - Relevant: Ja, aber PubMed bereits in Top-Liste

3. "Computer Science Bibliographies" (Score: 65)
   - Description: "CS conference proceedings"
   - Relevant: Weniger, zu allgemein
```

#### 3. Finale Empfehlung
```
1. PubMed (Score: 95, YAML)
2. IEEE Xplore (Score: 95, YAML)
3. arXiv (Score: 85, YAML)
4. Nature Machine Intelligence (Score: 85, DBIS)
5. MEDLINE (Score: 75, DBIS - aber via PubMed)
```

## Browser-Agent Instruktionen

### WebFetch für DBIS
```python
# Suche durchführen
url = f"https://dbis.ur.de/UBTIB/suche?q={query}"
prompt = """
Extrahiere von dieser DBIS-Suchseite:
1. Datenbanknamen (aus h3.db-title)
2. Beschreibungen (aus p.db-description)
3. Zugangsinfo (frei/Subskription)
4. DBIS IDs (aus Ressourcen-Links)

Formatiere als JSON:
[
  {
    "name": "...",
    "description": "...",
    "access": "free|subscription",
    "dbis_id": "..."
  }
]
"""
result = WebFetch(url, prompt)
```

### Detailseite abrufen
```python
url = f"https://dbis.ur.de/UBTIB/resources/{dbis_id}"
prompt = """
Extrahiere detaillierte Informationen:
- Vollständige Beschreibung
- Fachgebiete/Disziplinen
- Inhaltstypen
- Zugangsdetails
- Direkte Datenbank-URL
"""
details = WebFetch(url, prompt)
```

## Integration mit academic_context.md

Die DBIS-Ergebnisse werden mit den User-Präferenzen aus `academic_context.md` kombiniert:

```
IF user_preferred_database in DBIS_results:
    Score += 50  # Starker Bonus

IF user_discipline matches DBIS_db_discipline:
    Score += 20
```

## Hinweise für Agent-Entwicklung

1. **Caching**: DBIS-Ergebnisse können gecacht werden (15-30 Min)
2. **Rate Limiting**: Nicht mehr als 1 Request/Sekunde
3. **Fallback**: Bei DBIS-Fehler nur YAML-Datenbanken nutzen
4. **Sprache**: DBIS ist primär deutsch, unterstützt aber englische Suchbegriffe
5. **Institution**: TIB Hannover (UBTIB) hat guten Zugriff - als Standard verwenden
