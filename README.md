# Zeitdaten-Extraktion & Zeitstrahl

**Live-Demo:** https://chpollin.github.io/vizerektor-zeitstrahl/

Artefakt der Vizerektor-Demo: Datumsangaben aus 21 heterogenen Dokumenten
(7 PPTX-Foliendecks, 1 DOCX-Skriptum, 13 Markdown-Wissensdokumente) extrahiert,
normalisiert, mit Quellenbeleg versehen und als interaktiver Zeitstrahl dargestellt.

## Web-App öffnen

`index.html` im Browser öffnen (Doppelklick genügt — keine Installation, kein Server,
keine Internetverbindung nötig). Lädt die eingebetteten Daten aus `timeline_data.js`.

**Navigation**
- **Mausrad** über dem Zeitstrahl: zoomen (auf Cursorposition zentriert)
- **Ziehen**: verschieben
- **Minimap unten**: Dichteprofil über die ganze Zeitspanne; das gelbe Sichtfenster
  ziehen (verschieben) oder an den Rändern fassen (zoomen), Klick springt
- **Sprung-Presets**: *Gesamt · 2020–2028 · Kurs Juni 2026*; im Panel zusätzlich Epochen

**Lesen**
- **Lanes mit Baseline** je Markierung; **Datumslabels** direkt am Strahl (wo Platz ist)
- **Dekaden** als beschriftete Bänder; **„heute"-Linie** (19.06.2026) und **Kursfenster Juni 2026** hervorgehoben
- **Cluster (Zahl-Badge)**: anklicken → hineinzoomen; bei deckungsgleichen Daten Liste öffnen
- **Marke**: anklicken → Detailpanel mit Rohtext, ISO-Datum, Granularität, Quelldatei,
  Fundstelle, Kontext und Markierung
- **Übersichtspanel** (rechts, solange nichts gewählt): Legende, Kennzahlen, Funde je Quelldatei

**Filtern**
- Markierung, Granularität (beide mit Live-Zählern), Quelldatei, Volltextsuche
- Ansicht *Distinkt* (eine Marke je Datum) ↔ *Alle Funde* (jeder Fund einzeln, Dichte via Cluster)

## Design

Helles UI im Corporate Design der Universität Graz (CD-Manual Stand März 2025):

- **Primärfarben** als Gerüst: Gelb `#ffd500` (Markenbalken, aktive Schalter, Kursfenster,
  Minimap-Sichtfenster), Schwarz, Weiß, Grau `#c6c6c6` (Linien)
- **Sekundärpalette** für die Lanes (laut Manual „für Tabellen, Diagramme, Infografiken"):
  Blau `#689cce` = Ereignis, Grün `#9fcb81` = Zitations-/Literaturjahr, Grau = Technik-Stempel,
  Orange/Rot `#e4684b` = Nicht-Datum
- **Schrift** Nunito Sans (Light/ExtraBold; auf Uni-PCs vorinstalliert, sonst System-Fallback)
- Flächige Farbcodierung statt farbiger Texte, keine Schrifteffekte/Schatten

## Datenartefakte

| Datei | Inhalt |
|---|---|
| `zeitdaten_tabelle.csv` | Voll-Tabelle, **eine Zeile pro Fund** (1.514), `;`-getrennt, UTF-8-BOM (Excel) |
| `zeitdaten_tabelle.md` | dieselbe Tabelle als Markdown, chronologisch sortiert |
| `zeitdaten_distinct.csv` | 175 **distinkte** normalisierte Daten, aggregiert (Fundzahl + Quelldateien) |
| `timeline_data.js` | für die Web-App eingebettete Funde (JSON) inkl. berechneter Start/End-Spannen |

## Spalten der Tabelle

Rohtext · Normalisiert (ISO) · Granularität · Quelldatei · Fundstelle · Kontext · Markierung

### Markierung (4-wertig)

- **Ereignis** — inhaltliche Daten (historische Ereignisse, Releases, Kurstermine, Beispieldaten)
- **Zitations-/Literaturjahr** — bloße Jahreszahl im Quellen-/Literaturkontext
- **Technik-Stempel** — Dokument-Metadaten (`created:`/`updated:`, Zugriffs-/Copyright-Daten)
- **Nicht-Datum (Identifier)** — Fehltreffer (arXiv-IDs, Versionsnummern), markiert statt gelöscht

Hinweis: In der VU 4.4 ist Metadaten-/Archivbeschreibung selbst Lehrstoff. Felder wie
`dc:date`, `foaf:birthDate`, `Date:` sind daher **inhaltliche Beispieldaten** (Zweig-Korrespondenz),
kein Datei-Stempel — sie sind als *Ereignis* markiert.

### Granularität

Tag · Monat · Jahr · Jahrzehnt · Semester · relativ (gegen 2026-06-18 verankert).
Zwei Funde sind nicht eindeutig als Kalenderdatum auflösbar (Semester-Fehltreffer `WS0203`,
Versionsnummer `1.0. 2024`) und werden in der App unter „ohne sichere Position" geführt.

## Reproduktion

Pipeline in `pipeline/` (Python 3 mit `python-pptx`, `python-docx`):

1. `extract.py` — Text aus allen Dateien mit Fundstellen-Markern in Dumps
2. `candidates.py` — Datums-Kandidaten per Regex + Kontextfenster
3. `normalize.py` — ISO-Normalisierung, Granularität, Markierung; schreibt CSVs
4. `gen_data.py` — `timeline_data.js` für die Web-App

Pfade in den Skripten sind auf dieses Demo-Verzeichnis gesetzt.
