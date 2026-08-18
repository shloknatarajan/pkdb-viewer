#!/usr/bin/env python3
"""
Pull a spread-out sample of abstracts from a Method-A tier so precision can be
judged (does each hit actually report PK parameters PKDB curates?).

esearch (db=pmc, tier term) -> collect UIDs across several retstart offsets ->
elink pmc->pubmed -> efetch pubmed abstracts. Writes JSONL for classification.

Usage:
  ingest/.venv/bin/python scope_estimation/sample_precision.py medium 50
  ingest/.venv/bin/python scope_estimation/sample_precision.py broad 50
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL, EMAIL = "pkdb-scope", "shlok@gxl.ai"
SLEEP = 0.34

OA = '"open access"[filter]'
MESH_PK = '"Pharmacokinetics"[MeSH Terms]'
HUMANS = 'Humans[MeSH]'
PK_SIGNAL = (
    '("Pharmacokinetics"[MeSH Terms] OR pharmacokinetics[Subheading] '
    'OR "Area Under Curve"[MeSH] OR "Metabolic Clearance Rate"[MeSH] OR "Half-Life"[MeSH] '
    'OR AUC[tiab] OR Cmax[tiab] OR clearance[tiab] OR "half-life"[tiab] '
    'OR "volume of distribution"[tiab] OR "concentration-time"[tiab] OR bioavailability[tiab])'
)
TIERS = {
    "broad": f"{OA} AND {PK_SIGNAL} AND {HUMANS}",
    "medium": f"{OA} AND {MESH_PK} AND {HUMANS}",
}


def get(url: str) -> bytes:
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            if attempt == 4:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("unreachable")


def esearch_uids(term: str, retstart: int, retmax: int) -> list[str]:
    q = urllib.parse.urlencode({"db": "pmc", "term": term, "retstart": retstart,
                                "retmax": retmax, "tool": TOOL, "email": EMAIL})
    root = ET.fromstring(get(f"{EUTILS}/esearch.fcgi?{q}"))
    time.sleep(SLEEP)
    return [e.text for e in root.findall(".//IdList/Id")]


def pmc_to_pubmed(pmc_uids: list[str]) -> dict[str, str]:
    q = urllib.parse.urlencode({"dbfrom": "pmc", "db": "pubmed",
                                "tool": TOOL, "email": EMAIL}) + "".join(
        f"&id={u}" for u in pmc_uids)
    root = ET.fromstring(get(f"{EUTILS}/elink.fcgi?{q}"))
    time.sleep(SLEEP)
    out: dict[str, str] = {}
    for ls in root.findall(".//LinkSet"):
        src = ls.findtext(".//IdList/Id")
        tgt = ls.findtext(".//LinkSetDb/Link/Id")
        if src and tgt:
            out[src] = tgt
    return out


def efetch_abstracts(pmids: list[str]) -> dict[str, dict]:
    q = urllib.parse.urlencode({"db": "pubmed", "rettype": "abstract", "retmode": "xml",
                                "tool": TOOL, "email": EMAIL, "id": ",".join(pmids)})
    root = ET.fromstring(get(f"{EUTILS}/efetch.fcgi?{q}"))
    time.sleep(SLEEP)
    out: dict[str, dict] = {}
    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//PMID")
        title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
        abst = " ".join("".join(a.itertext()) for a in art.findall(".//Abstract/AbstractText"))
        out[pmid] = {"pmid": pmid, "title": title.strip(), "abstract": abst.strip()}
    return out


def main() -> None:
    tier = sys.argv[1] if len(sys.argv) > 1 else "medium"
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    term = TIERS[tier]

    # Count, then sample UIDs spread across the whole result set.
    q = urllib.parse.urlencode({"db": "pmc", "term": term, "retmax": "0",
                                "tool": TOOL, "email": EMAIL})
    total = int(ET.fromstring(get(f"{EUTILS}/esearch.fcgi?{q}")).findtext("Count"))
    time.sleep(SLEEP)
    n_off = 10
    per = max(1, want // n_off)
    step = max(per, total // n_off)
    pmc_uids: list[str] = []
    for k in range(n_off):
        pmc_uids += esearch_uids(term, retstart=k * step, retmax=per)
    pmc_uids = list(dict.fromkeys(pmc_uids))[:want]

    link = pmc_to_pubmed(pmc_uids)
    pmids = list(link.values())
    recs = {}
    for i in range(0, len(pmids), 40):
        recs.update(efetch_abstracts(pmids[i:i + 40]))

    rows = [recs[p] for p in pmids if p in recs]
    out = HERE / f"sample_{tier}.jsonl"
    with out.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"tier={tier} total={total:,} sampled_pmc={len(pmc_uids)} abstracts={len(rows)} -> {out}")


if __name__ == "__main__":
    main()
