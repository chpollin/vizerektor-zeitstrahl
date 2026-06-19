# -*- coding: utf-8 -*-
"""Scan extracted text dumps for date candidates with context + location."""
import os, re, glob, io, csv

OUT = r"c:\tmp\vizerektor-extraktion"

MONTHS = r"(?:Jän(?:ner)?|Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Maerz|Apr(?:il)?|Mai|Jun(?:i)?|Jul(?:i)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Okt(?:ober)?|Nov(?:ember)?|Dez(?:ember)?)"

PATTERNS = [
    ("ISO_DMY",   re.compile(r"\b\d{4}-\d{2}-\d{2}\b")),
    ("ISO_YM",    re.compile(r"\b\d{4}-\d{2}(?!\d)\b")),
    ("DE_DMY",    re.compile(r"\b\d{1,2}\.\s?\d{1,2}\.\s?\d{2,4}\b")),
    ("DE_DAYMON", re.compile(r"\b\d{1,2}\.\s?" + MONTHS + r"\.?(?:\s+\d{4})?", re.I)),
    ("DE_MONYEAR",re.compile(r"\b" + MONTHS + r"\s+\d{4}\b", re.I)),
    ("SEMESTER",  re.compile(r"\b(?:SS|WS|SoSe|WiSe|Sommersemester|Wintersemester)\s?\d{2,4}(?:/\d{2,4})?\b", re.I)),
    ("DECADE",    re.compile(r"\b\d{4}er(?:\s?Jahr(?:e|en)?)?\b")),
    ("REL_IN",    re.compile(r"\bin\s+(?:den\s+)?(?:nächsten\s+|kommenden\s+)?(?:\d{1,3}|ein(?:em|en)?|zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwanzig|dreißig|hundert)\s+(?:Tag(?:en)?|Woche(?:n)?|Monat(?:en)?|Jahr(?:en|zehnt(?:en)?)?)", re.I)),
    ("REL_VOR",   re.compile(r"\bvor\s+(?:\d{1,3}|ein(?:em|igen)?|zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwanzig|dreißig|hundert)\s+(?:Tag(?:en)?|Woche(?:n)?|Monat(?:en)?|Jahr(?:en|zehnt(?:en)?)?)", re.I)),
    ("REL_WORD",  re.compile(r"\b(?:heute|gestern|vorgestern|morgen|übermorgen|nächste[snr]?\s+(?:Woche|Monat|Jahr|Semester)|letzte[snr]?\s+(?:Woche|Monat|Jahr|Semester)|kommende[snr]?\s+(?:Woche|Monat|Jahr|Semester)|diese[snr]?\s+(?:Woche|Monat|Jahr|Semester)|seit\s+\d+\s+(?:Jahren|Monaten|Wochen|Tagen))\b", re.I)),
    ("YEAR",      re.compile(r"\b(?:19|20)\d{2}\b")),
]

# location marker detectors
RE_FOLIE = re.compile(r"^===== FOLIE (\d+) =====")
RE_ZEILE = re.compile(r"^\[Z(\d+)\]")
RE_PARA  = re.compile(r"^\[P(\d+)\]")
RE_TAB   = re.compile(r"^\[TABELLE (\d+)\]")

rows = []
for txt in sorted(glob.glob(os.path.join(OUT, "*.txt"))):
    name = os.path.basename(txt)[:-4]  # strip .txt
    loc = ""
    with io.open(txt, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            m = RE_FOLIE.match(line)
            if m: loc = "Folie %s" % m.group(1); continue
            m = RE_ZEILE.match(line)
            if m: loc = "Z%s" % m.group(1)
            m = RE_PARA.match(line)
            if m: loc = "P%s" % m.group(1)
            m = RE_TAB.match(line)
            if m: loc = "Tabelle %s" % m.group(1); continue
            # strip leading marker for context display
            disp = re.sub(r"^\[(Z|P)\d+\]\s?", "", line)
            seen_spans = []
            for cat, rx in PATTERNS:
                for mm in rx.finditer(line):
                    span = mm.span()
                    # avoid double-counting YEAR inside a richer match on same span overlap
                    if cat == "YEAR" and any(s[0] <= span[0] < s[1] for s in seen_spans):
                        continue
                    seen_spans.append(span)
                    raw_match = mm.group(0).strip()
                    ctx = disp.strip()
                    if len(ctx) > 160:
                        # window around match
                        a = max(0, mm.start()-70); b = min(len(line), mm.end()+70)
                        ctx = ("…" if a>0 else "") + line[a:b].strip() + ("…" if b<len(line) else "")
                        ctx = re.sub(r"^\[(Z|P)\d+\]\s?", "", ctx)
                    rows.append([name, loc, cat, raw_match, ctx])

# dedup identical (file, loc, cat, raw, ctx)
seen = set(); uniq = []
for r in rows:
    k = tuple(r)
    if k in seen: continue
    seen.add(k); uniq.append(r)

with io.open(os.path.join(OUT, "candidates.tsv"), "w", encoding="utf-8", newline="") as f:
    wcsv = csv.writer(f, delimiter="\t")
    wcsv.writerow(["Quelldatei","Fundstelle","Kategorie","Rohtext","Kontext"])
    for r in uniq:
        wcsv.writerow(r)

# summary by category
from collections import Counter
c = Counter(r[2] for r in uniq)
print("Kandidaten gesamt:", len(uniq))
for k,v in sorted(c.items(), key=lambda x:-x[1]):
    print("  %-10s %4d" % (k, v))
