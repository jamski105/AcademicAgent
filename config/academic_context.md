# Wissenschaftlicher Kontext

**Version:** 3.0
**Zweck:** Statischer wissenschaftlicher Kontext für alle Recherche-Runs

---

## Anleitung

Fülle dieses Template **einmal** aus mit dem allgemeinen Kontext deiner wissenschaftlichen Arbeit. Diese Informationen werden für **alle Recherche-Runs** verwendet.

**Was gehört NICHT hierher:**
- ❌ Spezifische Forschungsfragen für einzelne Kapitel
- ❌ Anzahl benötigter Zitate pro Run
- ❌ Run-spezifische Keywords

**Was gehört hierher:**
- ✅ Allgemeines Forschungsgebiet und Thema
- ✅ Hintergrund und Kontext der Arbeit
- ✅ Grundlegende Methoden und Theorien
- ✅ Generelle Keywords die immer relevant sind
- ✅ Bevorzugte Datenbanken (optional)

---

## 1. Forschungsgebiet

**Hauptdisziplin:**
```
[Beispiel: Human-Computer Interaction, Machine Learning, Klinische Psychologie,
Software Engineering, Rechtswissenschaften, etc.]
```

**Spezialisierung/Sub-Bereich:**
```
[Beispiel: VR Accessibility, DevOps Governance, Medizinrecht,
AI Ethics, etc.]
```

---

## 2. Hintergrund der Arbeit

**Art der Arbeit:**
```
[Beispiel: Masterarbeit, Bachelorarbeit, Dissertation, Paper, Forschungsprojekt]
```

**Kontext:**
```
[Beispiel:
"Masterarbeit an der TU Wien über Accessibility in VR-Anwendungen für Menschen
mit motorischen Einschränkungen. Fokus auf alternative Input-Methoden zu
Hand-Tracking, insbesondere für Nutzer mit Tremor oder eingeschränkter
Handbeweglichkeit."]
```

**Hauptziel der Arbeit:**
```
[Beispiel:
"Entwicklung und Evaluation eines adaptiven Input-Systems für VR, das sich
automatisch an verschiedene Grade motorischer Einschränkungen anpasst."]
```

---

## 3. Verwendete Methoden/Theorien

**Forschungsmethoden:**
```
[Beispiel:
- User-Centered Design
- Qualitative Interviews mit Betroffenen (N=15)
- Usability Testing mit Prototypen
- Vergleichsstudie verschiedener Input-Methoden]
```

**Theoretischer Rahmen:**
```
[Beispiel:
- Universal Design Principles
- ISO 9241 (Ergonomie der Mensch-System-Interaktion)
- Accessibility Guidelines (WCAG, EN 301 549)]
```

**Technologien/Tools:**
```
[Beispiel:
- Unity 3D für VR-Entwicklung
- Oculus Quest 2 als Zielplattform
- Eye-Tracking Hardware (Tobii)
- Verschiedene adaptive Controller]
```

---

## 4. Wichtige Keywords

**Hinweis:** Liste hier **generelle** Keywords auf, die für deine gesamte Arbeit relevant sind.
Run-spezifische Keywords werden später vom Setup-Agent abgefragt.

**Hauptkonzepte:**
```
[Beispiel:
- Virtual Reality
- VR
- Immersive Environments
- Accessibility
- Inclusive Design
- Universal Access]
```

**Technische Begriffe:**
```
[Beispiel:
- Hand Tracking
- Gesture Control
- Eye Tracking
- Voice Control
- Adaptive Interfaces
- Assistive Technology]
```

**Zielgruppen/Kontext:**
```
[Beispiel:
- Motor Impairments
- Physical Disabilities
- Limited Mobility
- Tremor
- Cerebral Palsy]
```

---

## 5. Bevorzugte Datenbanken (optional)

**Hinweis:** Wenn leer gelassen, erkennt der Agent automatisch passende Datenbanken
basierend auf deinem Forschungsgebiet.

**Deine bevorzugten Datenbanken:**
```
[Beispiel:
- ACM Digital Library (für HCI-Papers)
- IEEE Xplore (für technische Aspekte)
- PubMed (für medizinische Perspektive)]
```

**Warum diese Datenbanken?**
```
[Beispiel:
"ACM und IEEE haben die beste Abdeckung für HCI- und VR-Forschung.
PubMed ist wichtig für die medizinische Perspektive auf motorische Einschränkungen."]
```

---

## 6. Zitationseinstellungen

**Zitationsstil:**
```
APA 7
```

**Alternativen:** IEEE, MLA, Chicago, Harvard, Vancouver

**Max Wörter pro Zitat:**
```
50
```

**Hinweis:** Dieser Wert sollte normalerweise nicht geändert werden (50 Wörter = optimal für Zitat-Bibliothek)

---

## 7. Relevante Autoren/Paper (optional)

**Seminal Papers in deinem Feld:**
```
[Beispiel:
- Smith et al. (2023): "Accessible VR: A Systematic Review"
- Johnson & Lee (2022): "Adaptive Interfaces for Motor Impairments"
- Wilson (2021): "Beyond Hand Tracking: Alternative Input Methods for VR"]
```

**Wichtige Forscher/Gruppen:**
```
[Beispiel:
- Dr. Sarah Chen (Stanford HCI Lab) - Accessibility in VR
- Prof. Michael Rodriguez (MIT) - Adaptive Systems
- Ability Lab Chicago - Assistive Technology Research]
```

**Warum sind diese relevant?**
```
[Beispiel:
"Diese Autoren haben Pionierarbeit im Bereich accessible VR geleistet.
Ihre Frameworks und Methoden bilden die Grundlage für meine Arbeit."]
```

---

## 8. Zeitliche Eingrenzung (Default)

**Standard-Zeitraum für Recherchen:**
```
2019-2026 (Last 7 years)
```

**Begründung:**
```
[Beispiel:
"VR-Technologie hat sich in den letzten 5 Jahren stark entwickelt.
Papers vor 2019 sind oft nicht mehr relevant, da sie auf veralteter Hardware basieren."]
```

**Hinweis:** Dieser Default kann in jedem Run individuell angepasst werden.

---

## 9. Qualitätsanforderungen (Default)

**Peer-Review erforderlich:**
```
Ja
```

**Preprints einbeziehen:**
```
Ja (arXiv, bioRxiv für cutting-edge Forschung)
```

**Minimum Citation Count:**
```
5 (Papers mit weniger als 5 Citations werden standardmäßig gefiltert)
```

**Conference Tiers (für CS):**
```
A, B (CORE Ranking)
```

**Hinweis:** Diese Defaults können in jedem Run angepasst werden.

---

## 10. Sprachen

**Bevorzugte Sprachen:**
```
1. Englisch (primär)
2. Deutsch (sekundär, falls relevant)
```

**Andere akzeptable Sprachen:**
```
[Beispiel: Französisch, Spanisch - nur wenn sehr relevant]
```

---

## Beispiel: Ausgefüllter Kontext

```markdown
# Wissenschaftlicher Kontext

## 1. Forschungsgebiet
Hauptdisziplin: Human-Computer Interaction
Spezialisierung: VR Accessibility for Motor Impairments

## 2. Hintergrund der Arbeit
Art: Masterarbeit
Kontext: TU Wien, Studiengang Medieninformatik
"Entwicklung und Evaluation alternativer Input-Methoden für VR-Anwendungen
für Menschen mit eingeschränkter Handmotorik."

## 3. Verwendete Methoden
- User-Centered Design
- Qualitative Interviews (N=15)
- Prototyping & Usability Testing
- Comparative Analysis verschiedener Input-Methoden

## 4. Keywords
Hauptkonzepte: VR, Virtual Reality, Accessibility, Inclusive Design
Technisch: Hand Tracking, Eye Tracking, Voice Control, Adaptive Interfaces
Zielgruppe: Motor Impairments, Physical Disabilities, Tremor

## 5. Bevorzugte Datenbanken
- ACM Digital Library
- IEEE Xplore
- PubMed

## 6. Zitationseinstellungen
Stil: APA 7
Max Wörter: 50

## 7. Relevante Autoren
- Smith et al. (2023): "Accessible VR: A Systematic Review"
- Johnson (2022): "Adaptive Interfaces"

## 8. Zeitraum Default
2019-2026 (neueste VR-Forschung)

## 9. Qualität
Peer-Reviewed: Ja
Preprints: Ja
Min Citations: 5
```

---

## Nächste Schritte

Nach dem Ausfüllen dieser Datei:

1. **Speichere** die Datei als `academic_context.md` im `config/` Ordner
2. **Starte** den Academic Agent mit: `/academicagent`
3. Der Setup-Agent wird diesen Kontext laden und dich durch einen **run-spezifischen Dialog** führen

Der Setup-Agent fragt dann:
- "Was ist dein spezifisches Ziel für diesen Run?" (z.B. Zitate für Kapitel 3)
- "Wie viele Zitate brauchst du?"
- "Welche speziellen Keywords für diesen Run?"
- etc.

---

**Version History:**
- 2.0 (2026-02-17): Neue Struktur mit Trennung statisch/dynamisch
- 1.0 (2026-01-15): Original Config_Template.md
