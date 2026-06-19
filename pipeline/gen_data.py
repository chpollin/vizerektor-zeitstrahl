# -*- coding: utf-8 -*-
"""Build timeline_data.js (embedded JSON) from the full find-level table."""
import io, csv, re, json, calendar

SRC = r"c:\tmp\vizerektor-extraktion\zeitdaten_tabelle.csv"
OUT = r"c:\Users\Chrisi\Downloads\vizerektor-demo\zeitdaten\timeline_data.js"

rows = list(csv.reader(io.open(SRC, encoding="utf-8-sig"), delimiter=";"))
hdr, rows = rows[0], rows[1:]
# cols: Rohtext;Normalisiert (ISO);Granularität;Quelldatei;Fundstelle;Kontext;Markierung;Pattern

def last_day(y, m): return calendar.monthrange(y, m)[1]

def span(iso, gran):
    """Return (start, end, kind, placeable) as 'YYYY-MM-DD' strings."""
    g = gran.lower()
    # day
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso)
    if m and g.startswith("tag"):
        return iso, iso, "point", True
    # month
    m = re.match(r"^(\d{4})-(\d{2})$", iso)
    if m and g.startswith("monat"):
        y, mo = int(m.group(1)), int(m.group(2))
        return "%04d-%02d-01" % (y, mo), "%04d-%02d-%02d" % (y, mo, last_day(y, mo)), "range", True
    # plain year
    if g == "jahr" and re.match(r"^\d{4}$", iso):
        y = int(iso)
        return "%04d-01-01" % y, "%04d-12-31" % y, "range", True
    # decade  "1990s"
    m = re.match(r"^(\d{3})0s$", iso)
    if m:
        d = int(m.group(1)) * 10
        return "%04d-01-01" % d, "%04d-12-31" % (d + 9), "band", True
    # semester  "2026 (SS)" / "0203 (WS)"
    m = re.match(r"^(\d{1,4})\s*\((SS|WS)\)$", iso)
    if m:
        y = int(m.group(1))
        if y < 1800 or y > 2100:
            return None, None, "point", False  # parser false positive (e.g. 0203)
        if m.group(2) == "SS":
            return "%04d-03-01" % y, "%04d-06-30" % y, "range", True
        return "%04d-10-01" % y, "%04d-01-31" % (y + 1), "range", True
    # relative: leading YYYY or YYYY-MM, else anchor 2026-06-18
    m = re.match(r"^(\d{4})(?:-(\d{2}))?", iso)
    if g == "relativ":
        if m:
            y = int(m.group(1)); mo = int(m.group(2)) if m.group(2) else 6
            d = 15 if m.group(2) else 18
            return "%04d-%02d-%02d" % (y, mo, d), "%04d-%02d-%02d" % (y, mo, d), "rel", True
        return "2026-06-18", "2026-06-18", "rel", True
    # last-resort: any leading 4-digit year
    m = re.match(r"^(\d{4})", iso)
    if m:
        y = int(m.group(1))
        if 1700 <= y <= 2100:
            return "%04d-01-01" % y, "%04d-12-31" % y, "range", True
    return None, None, "point", False

FLAG_KEY = {
    "Ereignis": "ereignis",
    "Zitations-/Literaturjahr": "zitat",
    "Technik-Stempel": "technik",
    "Nicht-Datum (Identifier)": "nichtdatum",
}

items = []
for i, r in enumerate(rows):
    roh, iso, gran, datei, fund, ktx, flag, pat = r
    start, end, kind, placeable = span(iso, gran)
    items.append({
        "id": i,
        "roh": roh,
        "iso": iso,
        "gran": gran,
        "datei": datei,
        "fund": fund,
        "ktx": ktx,
        "flag": flag,
        "fk": FLAG_KEY.get(flag, "ereignis"),
        "start": start,
        "end": end,
        "kind": kind,
        "ok": placeable,
    })

placeable = sum(1 for it in items if it["ok"])
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("// Auto-generiert aus zeitdaten_tabelle.csv — %d Funde\n" % len(items))
    f.write("const FINDS = ")
    json.dump(items, f, ensure_ascii=False)
    f.write(";\n")

print("timeline_data.js geschrieben")
print("  Funde gesamt:", len(items))
print("  platzierbar :", placeable)
print("  ohne Position:", len(items) - placeable)
# show the non-placeable ones
for it in items:
    if not it["ok"]:
        print("   NP:", it["iso"], "|", it["gran"], "|", it["roh"][:30], "|", it["ktx"][:50])
