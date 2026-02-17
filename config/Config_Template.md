# 📋 Config-Template - AcademicAgent

**Version:** 1.0
**Hinweis:** Passe dieses Template für dein Projekt an und speichere es als `Config_[DeinProjekt].md`

---

## 1. PROJECT INFO

**Projekt-Titel:**
```
[z.B. "Lean Governance in DevOps-Teams"]
```

**Disziplin:**
```
[z.B. "Informatik" / "Jura" / "Medizin" / "BWL" / "Ingenieurwesen" / "Sozialwissenschaften"]
```

**Forschungsfrage:**
```
[z.B. "Wie wird Lean Governance in DevOps-Teams umgesetzt und welche Mechanismen werden verwendet?"]
```

**Kontext (optional):**
```
[z.B. "Masterarbeit, FH Technikum Wien, Studiengang Software Engineering"]
```

---

## 2. SEARCH CLUSTERS

**Hinweis:** Mindestens 3 Cluster erforderlich. Cluster 4 ist optional.

### Cluster 1: Core-Konzept (Hauptthema)

**EN:**
```
- [Begriff 1, z.B. "lean governance"]
- [Begriff 2, z.B. "lightweight governance"]
- [Begriff 3, z.B. "agile governance"]
```

**DE (optional, für deutsche Datenbanken):**
```
- [Begriff 1, z.B. "schlanke Steuerung"]
- [Begriff 2, z.B. "Lean Governance"]
```

---

### Cluster 2: Domain/Kontext (Anwendungsbereich)

**EN:**
```
- [Begriff 1, z.B. "DevOps"]
- [Begriff 2, z.B. "continuous delivery"]
- [Begriff 3, z.B. "CI/CD"]
```

**DE (optional):**
```
- [Begriff 1, z.B. "DevOps"]
- [Begriff 2, z.B. "kontinuierliche Auslieferung"]
```

---

### Cluster 3: Mechanismen/Instrumente (Praktiken, Tools)

**EN:**
```
- [Begriff 1, z.B. "automation"]
- [Begriff 2, z.B. "pull requests"]
- [Begriff 3, z.B. "code review"]
- [Begriff 4, z.B. "infrastructure as code"]
```

**DE (optional):**
```
- [Begriff 1, z.B. "Automatisierung"]
- [Begriff 2, z.B. "Pull Requests"]
```

---

### Cluster 4: Methoden/Modelle (optional)

**EN:**
```
- [Begriff 1, z.B. "case study"]
- [Begriff 2, z.B. "framework"]
- [Begriff 3, z.B. "empirical study"]
```

---

## 3. DATABASES

### Primary Databases (3-5 Datenbanken)

**Hinweis:** Wähle disziplin-spezifische Datenbanken.

**Informatik/Ingenieurwesen:**
```
- IEEE Xplore
- ACM Digital Library
- SpringerLink
- Scopus
- ScienceDirect
```

**Jura/Rechtswissenschaften:**
```
- Beck-Online
- Juris
- HeinOnline
- SpringerLink (Rechtswissenschaften)
- Scopus
```

**Medizin/Life Sciences:**
```
- PubMed
- Cochrane Library
- Scopus
- SpringerLink (Medicine)
- ScienceDirect
```

**BWL/Management:**
```
- EBSCO Business Source
- JSTOR
- SpringerLink (Business & Management)
- Scopus
- ProQuest
```

**Deine Auswahl (3-5):**
```
1. [z.B. "IEEE Xplore"]
2. [z.B. "SpringerLink"]
3. [z.B. "Scopus"]
4. [z.B. "ACM Digital Library"]
5. [z.B. "ScienceDirect"]
```

---

### DBIS Search Keywords (für DB-Discovery, optional)

**Hinweis:** Wenn der Agent zusätzliche Datenbanken finden soll.

```
[z.B. "Software Engineering" / "Rechtswissenschaft" / "Medical Informatics" / "Business Management"]
```

---

## 4. SOURCE PORTFOLIO

**Target Total:**
```
[z.B. 18 Quellen]
```

**Breakdown (optional, aber empfohlen):**
```
- [X] Primary Sources (Peer-reviewed, empirisch)
  [z.B. 10 Primary Sources]

- [Y] Management/Practice Sources (z.B. IEEE Software, HBR, practitioner journals)
  [z.B. 6 Management Sources]

- [Z] Standards/Frameworks (z.B. ISO, ITIL, Gesetze, Guidelines)
  [z.B. 2 Standards]
```

**Ziel-Zitate:**
```
[z.B. 40-50 Zitate (2-3 pro Quelle)]
```

---

## 5. QUALITY THRESHOLDS

### Min Year
```
[z.B. 2015]
```
**Hinweis:** Quellen älter als dieses Jahr werden ausgeschlossen.

---

### Citation Threshold

**Hinweis:** Disziplin-spezifisch!

| Disziplin | Empfohlener Threshold |
|-----------|------------------------|
| Informatik | 50-100 |
| Jura | 10-30 |
| Medizin | 100-500 |
| BWL | 50-150 |
| Ingenieurwesen | 30-80 |

**Deine Auswahl:**
```
[z.B. 50]
```

---

### Min Score (5D-Scoring)
```
[z.B. 4.0 / 5.0]
```
**Hinweis:** Quellen mit Score < Min Score werden ausgeschlossen (außer Grenzfälle 3.0-4.0 → User entscheidet).

---

### Preprint Max %
```
[z.B. 10%]
```
**Hinweis:** Max. Anteil von Preprints (arXiv, SSRN, etc.). Empfohlen: 10-20%.

---

## 6. CONSTRAINTS

### Excluded Topics

**Hinweis:** Themen, die NICHT relevant sind (werden automatisch ausgeschlossen).

```
[z.B. "social media", "blockchain", "cryptocurrency"]
```

---

### Citation Rules

**Max. Wörter pro Zitat:**
```
[z.B. 35 Wörter]
```

**Seitenzahl:**
```
[Pflicht / Optional]
[Empfohlen: Pflicht]
```

**Zitat-Typ:**
```
[Wörtlich / Paraphrase]
[Empfohlen: Wörtlich]
```

---

### Language

**Suchsprache:**
```
[EN / DE / EN+DE]
[z.B. "EN" für Informatik, "DE" für deutsches Jura, "EN+DE" für BWL]
```

---

## 7. OUTPUT (optional)

### Quote Library Format
```
[CSV / Excel]
[Standard: CSV]
```

### Annotated Bibliography Format
```
[Markdown / PDF]
[Standard: Markdown]
```

---

## 8. ADVANCED OPTIONS (optional)

### Enable Snowballing
```
[true / false]
[Standard: false]
```
**Hinweis:** Wenn true, sucht der Agent auch in Referenzen gefundener Quellen (erhöht Zeitaufwand um 20-30%).

---

### Custom Scoring Weights (optional)

**Hinweis:** Standard-Gewichtung: D1=1.0, D2=1.0, D3=1.0, D4=1.0, D5=1.0

```
D1 (Themen-Fokus): [z.B. 1.5]
D2 (Cluster-Abdeckung): [z.B. 1.0]
D3 (Mechanismen): [z.B. 1.2]
D4 (Methodische Fundierung): [z.B. 1.0]
D5 (Zitierfähigkeit): [z.B. 0.8]
```

---

## ✅ BEISPIEL-CONFIG (Informatik: Lean Governance in DevOps)

```markdown
# Config - Lean Governance in DevOps

## 1. PROJECT INFO
Projekt-Titel: Lean Governance in DevOps-Teams
Disziplin: Informatik
Forschungsfrage: Wie wird Lean Governance in DevOps-Teams umgesetzt und welche Mechanismen werden verwendet?

## 2. SEARCH CLUSTERS
Cluster 1 (EN): lean governance, lightweight governance, agile governance
Cluster 1 (DE): schlanke Steuerung, Lean Governance

Cluster 2 (EN): DevOps, continuous delivery, CI/CD
Cluster 2 (DE): DevOps, kontinuierliche Auslieferung

Cluster 3 (EN): automation, pull requests, code review, infrastructure as code
Cluster 3 (DE): Automatisierung, Pull Requests, Code-Review

## 3. DATABASES
Primary Databases:
1. IEEE Xplore
2. SpringerLink
3. Scopus
4. ACM Digital Library
5. ScienceDirect

DBIS Search Keywords: Software Engineering, DevOps

## 4. SOURCE PORTFOLIO
Target Total: 18 Quellen
Breakdown:
- 10 Primary Sources (Peer-reviewed)
- 6 Management Sources (IEEE Software, etc.)
- 2 Standards (ISO, ITIL)

Ziel-Zitate: 40-50 Zitate

## 5. QUALITY THRESHOLDS
Min Year: 2015
Citation Threshold: 50
Min Score: 4.0 / 5.0
Preprint Max %: 10%

## 6. CONSTRAINTS
Excluded Topics: social media, blockchain, cryptocurrency
Citation Rules: Max. 35 Wörter, Seitenzahl Pflicht, Wörtlich
Language: EN

## 7. OUTPUT
Quote Library Format: CSV
Annotated Bibliography Format: Markdown

## 8. ADVANCED OPTIONS
Enable Snowballing: false
```

---

## ✅ BEISPIEL-CONFIG (Jura: DSGVO-Compliance)

```markdown
# Config - DSGVO-Compliance in Unternehmen

## 1. PROJECT INFO
Projekt-Titel: DSGVO-Compliance-Anforderungen für Unternehmen
Disziplin: Jura
Forschungsfrage: Welche rechtlichen Anforderungen stellt die DSGVO an Unternehmen und wie werden diese umgesetzt?

## 2. SEARCH CLUSTERS
Cluster 1 (DE): DSGVO, Datenschutz-Grundverordnung, Datenschutz
Cluster 1 (EN): GDPR, General Data Protection Regulation, data protection

Cluster 2 (DE): Unternehmen, Compliance, Haftung
Cluster 2 (EN): companies, compliance, liability

Cluster 3 (DE): Dokumentationspflicht, Datenschutzbeauftragter, Einwilligung
Cluster 3 (EN): documentation requirements, data protection officer, consent

## 3. DATABASES
Primary Databases:
1. Beck-Online
2. Juris
3. HeinOnline
4. SpringerLink (Rechtswissenschaften)
5. Scopus

DBIS Search Keywords: Rechtswissenschaft, Datenschutzrecht

## 4. SOURCE PORTFOLIO
Target Total: 18 Quellen
Breakdown:
- 10 Primary Sources (Aufsätze, Kommentare)
- 5 Gerichtsentscheidungen
- 3 Standards (DSGVO-Text, Leitlinien)

Ziel-Zitate: 40-50 Zitate

## 5. QUALITY THRESHOLDS
Min Year: 2016 (DSGVO-Inkrafttreten)
Citation Threshold: 10 (Jura hat weniger Zitationen)
Min Score: 4.0 / 5.0
Preprint Max %: 5%

## 6. CONSTRAINTS
Excluded Topics: Strafrecht, Steuerrecht (falls nicht relevant)
Citation Rules: Max. 35 Wörter, Seitenzahl/Clause Pflicht, Wörtlich
Language: DE+EN

## 7. OUTPUT
Quote Library Format: CSV
Annotated Bibliography Format: Markdown

## 8. ADVANCED OPTIONS
Enable Snowballing: false
```

---

## 🚀 NÄCHSTE SCHRITTE

1. **Passe dieses Template an:**
   - Fülle alle `[Platzhalter]` aus
   - Speichere als: `Config_[DeinProjekt].md`
   - Ort: `~/AcademicAgent/config/Config_[DeinProjekt].md`

2. **Starte den Agent:**
   ```
   Lies agents/orchestrator.md und starte die Recherche für ~/AcademicAgent/config/Config_[DeinProjekt].md
   ```

---

**Ende des Config-Templates.**
