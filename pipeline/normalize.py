# -*- coding: utf-8 -*-
"""Normalize date candidates to ISO + granularity, classify event vs technical."""
import io, csv, re
from collections import Counter

IN  = r"c:\tmp\vizerektor-extraktion\candidates.tsv"
OUT_CSV = r"c:\tmp\vizerektor-extraktion\zeitdaten_tabelle.csv"
OUT_MD  = r"c:\tmp\vizerektor-extraktion\zeitdaten_tabelle.md"

MON = {
 'jän':1,'jänner':1,'jan':1,'januar':1,'feb':2,'februar':2,'mär':3,'märz':3,'maerz':3,
 'apr':4,'april':4,'mai':5,'jun':6,'juni':6,'jul':7,'juli':7,'aug':8,'august':8,
 'sep':9,'sept':9,'september':9,'okt':10,'oktober':10,'nov':11,'november':11,'dez':12,'dezember':12
}
WORDNUM = {'ein':1,'einem':1,'einen':1,'eine':1,'zwei':2,'drei':3,'vier':4,'fünf':5,'sechs':6,
 'sieben':7,'acht':8,'neun':9,'zehn':10,'elf':11,'zwölf':12,'zwanzig':20,'dreißig':30,'hundert':100}

def y4(y):
    y = int(y)
    if y < 100:
        return 2000 + y if y <= 40 else 1900 + y
    return y

def normalize(cat, raw, ctx):
    """return (iso, granularity_label) or (None,None) if unresolved."""
    r = raw.strip()
    low = r.lower()
    if cat == "ISO_DMY":
        return r[:10], "Tag"
    if cat == "ISO_YM":
        return r[:7], "Monat"
    if cat == "DE_DMY":
        m = re.match(r"(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{2,4})", r)
        if m:
            d,mo,y = int(m.group(1)), int(m.group(2)), y4(m.group(3))
            if 1<=mo<=12 and 1<=d<=31:
                return "%04d-%02d-%02d" % (y,mo,d), "Tag"
        return None, None
    if cat == "DE_DAYMON":
        m = re.match(r"(\d{1,2})\.\s?([A-Za-zÄÖÜäöüß]+)\.?(?:\s+(\d{4}))?", r)
        if m:
            d = int(m.group(1)); mon = MON.get(m.group(2).lower().rstrip('.'))
            if mon:
                if m.group(3):
                    return "%04d-%02d-%02d" % (int(m.group(3)),mon,d), "Tag"
                return "????-%02d-%02d" % (mon,d), "Tag (Jahr aus Kontext)"
        return None, None
    if cat == "DE_MONYEAR":
        m = re.match(r"([A-Za-zÄÖÜäöüß]+)\s+(\d{4})", r)
        if m:
            mon = MON.get(m.group(1).lower())
            if mon:
                return "%04d-%02d" % (int(m.group(2)),mon), "Monat"
        return None, None
    if cat == "SEMESTER":
        m = re.search(r"(SS|SoSe|Sommersemester)\s?(\d{2,4})", r, re.I)
        if m:
            return "%04d (SS)" % y4(m.group(2)), "Semester (~Mär–Jun)"
        m = re.search(r"(WS|WiSe|Wintersemester)\s?(\d{2,4})(?:/(\d{2,4}))?", r, re.I)
        if m:
            return "%04d (WS)" % y4(m.group(2)), "Semester (~Okt–Jän)"
        return None, None
    if cat == "DECADE":
        m = re.match(r"(\d{4})er", r)
        if m:
            return "%04ss" % m.group(1)[:3] if False else m.group(1)[:3]+"0s", "Jahrzehnt"
        return None, None
    if cat == "YEAR":
        return r, "Jahr"
    if cat in ("REL_IN","REL_VOR","REL_WORD"):
        return rel_norm(cat, low), "relativ"
    return None, None

ANCHOR = (2026,6,18)
def rel_norm(cat, low):
    # crude anchored normalization against 2026-06-18; mark as relative
    m = re.search(r"(\d{1,3}|ein|einem|einen|zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwanzig|dreißig|hundert)\s+(tag|woche|monat|jahr)", low)
    sign = -1 if cat=="REL_VOR" else 1
    if m:
        n = int(m.group(1)) if m.group(1).isdigit() else WORDNUM.get(m.group(1),None)
        unit = m.group(2)
        if n is not None:
            y,mo,d = ANCHOR
            if unit.startswith("jahr"):
                return "%04d (±, Anker 2026-06-18)" % (y+sign*n),
            if unit.startswith("monat"):
                tot = (y*12+(mo-1)) + sign*n
                return "%04d-%02d (±, Anker 2026-06)" % (tot//12, tot%12+1),
            return "ca. %d %s%s (Anker 2026-06-18)" % (n, unit, "" if cat!="REL_VOR" else " zurück"),
    # word relatives
    return "relativ (Anker 2026-06-18)",

def rel_wrap(cat, low):
    v = rel_norm(cat, low)
    return v[0] if isinstance(v, tuple) else v

CITE = re.compile(r"arxiv|doi:|https?://|\bvol\.|\bs\.\s?\d|\bpp?\.\s?\d|verlag|\bhrsg|\bet al|journal|proceedings|preprint|\beds?\.|\(\d{4}\)|,\s?\d{4}\)|„[^“]+“.*\d{4}", re.I)

def classify(cat, raw, ctx, iso):
    c = ctx.lower()
    # 1) identifier false positives (arXiv:1911.01547 -> "1911"; version 1.0 -> 1.0.2024)
    if cat == "YEAR" and re.search(r"arxiv:\s?\d{4}\.\d", c):
        return "Nicht-Datum (Identifier)"
    if cat == "YEAR" and re.search(r"\b" + re.escape(raw) + r"\.\d{4,}", ctx):
        return "Nicht-Datum (Identifier)"
    if iso == "(unaufgelöst)":
        return "Nicht-Datum (Identifier)"
    # 2) document timestamps: ONLY frontmatter created/updated + access/copyright.
    #    NOT date:/datum:/dc:date — in this corpus those are taught metadata examples (content).
    if re.search(r"^(created|updated|modified)\s*:", c) or re.search(r"\b(created|updated)\s*:\s*\d{4}", c):
        return "Technik-Stempel"
    if any(k in c for k in ["abgerufen", "zugriff", "accessed", "retrieved",
                            "letzter abruf", "zuletzt geändert", "stand:", "© ", "copyright", "exportiert aus"]):
        return "Technik-Stempel"
    # 3) bare year inside a citation / bibliography context
    if cat == "YEAR" and CITE.search(ctx):
        return "Zitations-/Literaturjahr"
    return "Ereignis"

rows = list(csv.reader(io.open(IN, encoding="utf-8"), delimiter="\t"))[1:]
out = []
for fname, loc, cat, raw, ctx in rows:
    if cat in ("REL_IN","REL_VOR","REL_WORD"):
        iso = rel_wrap(cat, raw.lower()); gran="relativ"
    else:
        iso, gran = normalize(cat, raw, ctx)
    iso = iso or "(unaufgelöst)"
    # resolve year-from-context day dates (corpus is SS-2026 teaching material)
    if iso.startswith("????"):
        ym = re.search(r"\b(19\d{2}|20\d{2})\b", ctx)
        year = ym.group(1) if ym else "2026"
        iso = year + iso[4:]
        gran = "Tag (Jahr=%s aus Kontext)" % year
    flag = classify(cat, raw, ctx, iso)
    out.append([raw, iso, gran or "?", fname, loc, ctx, flag, cat])

# sort: resolved ISO ascending, unresolved last
def sortkey(r):
    iso = r[1]
    m = re.match(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", iso)
    if m:
        return (0, int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0))
    return (1, 9999, 99, 99)
out.sort(key=sortkey)

cols = ["Rohtext","Normalisiert (ISO)","Granularität","Quelldatei","Fundstelle","Kontext","Markierung","Pattern"]
with io.open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(cols)
    for r in out: w.writerow(r)

# ---- distinct view: collapse by normalized ISO, keep flag; aggregate sources ----
from collections import defaultdict
dist = defaultdict(lambda: {"flags":Counter(), "gran":None, "files":set(), "raws":set(), "ctx":None})
for raw, iso, gran, fname, loc, ctx, flag, cat in out:
    if flag.startswith("Nicht-Datum"):
        continue
    d = dist[iso]
    d["flags"][flag]+=1; d["gran"]=gran; d["files"].add(fname); d["raws"].add(raw)
    if d["ctx"] is None or (flag=="Ereignis" and len(ctx)>len(d["ctx"] or "")):
        d["ctx"]=ctx

def sortkey_iso(iso):
    m = re.match(r"(\d{3,4})", iso)
    return (0, int(m.group(1))) if m else (1, 9999)

distinct_rows = []
for iso in sorted(dist, key=sortkey_iso):
    d = dist[iso]
    primary = d["flags"].most_common(1)[0][0]
    distinct_rows.append([iso, d["gran"], primary, sum(d["flags"].values()),
                          len(d["files"]), " / ".join(sorted(d["raws"])[:3]),
                          (d["ctx"] or "")[:120], "; ".join(sorted(d["files"]))])

with io.open(r"c:\tmp\vizerektor-extraktion\zeitdaten_distinct.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Normalisiert (ISO)","Granularität","Markierung (primär)","Funde","Dateien","Rohtext-Beispiele","Kontext","Quelldateien"])
    for r in distinct_rows: w.writerow(r)

# stats
print("Funde gesamt (eine Zeile pro Fund):", len(out))
print("Distinkte normalisierte Daten:", len(distinct_rows))
print("\nNach Markierung (alle Funde):")
for k,v in Counter(r[6] for r in out).most_common(): print("  %-28s %d" % (k,v))
print("\nNach Granularität (alle Funde):")
for k,v in Counter(r[2] for r in out).most_common(): print("  %-28s %d" % (k,v))
print("\nDistinkte Daten nach Markierung:")
for k,v in Counter(r[2] for r in distinct_rows).most_common(): print("  %-28s %d" % (k,v))
