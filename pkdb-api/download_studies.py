#!/usr/bin/env python3
"""
Bulk-download every PK-DB study from the anonymous API and build a metadata CSV.

The PK-DB study `reference` block already carries the paper's PMID, title and
abstract, so no PubMed round-trip is needed for those. PMCIDs are looked up from
the mapping produced by resolve_pmcids.py (pmid_to_pmcid.csv); if that file is
missing, the pmcid column is left blank.

Outputs (written next to this script, in pkdb-api/):
  studies_full.json      -> the raw study records, exactly as the API returned
  studies_metadata.csv   -> pmid, pmcid, title, abstract  (one row per study)
"""
from __future__ import annotations

import csv
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

API = "https://pk-db.com/api/v1/studies/"
PAGE_SIZE = 100


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "pkdb-viewer/bulk-download"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def collect_studies() -> list[dict]:
    """Page through the API and return every full study record.

    PK-DB wraps results as {current_page, last_page, next_page_url,
    data: {count, data: [...studies...]}}.
    """
    studies: list[dict] = []
    url = f"{API}?format=json&page_size={PAGE_SIZE}"
    while url:
        payload = fetch_json(url)
        block = payload.get("data", {})
        total = block.get("count")
        studies.extend(block.get("data", []))
        print(f"  page {payload.get('current_page')}/{payload.get('last_page')}: "
              f"{len(studies)}/{total} studies collected")
        url = payload.get("next_page_url")
    return studies


def load_pmcid_map() -> dict[str, str]:
    """pmid -> pmcid from resolve_pmcids.py output (blank pmcids omitted)."""
    path = HERE / "pmid_to_pmcid.csv"
    if not path.exists():
        print(f"  note: {path.name} not found; pmcid column will be blank")
        return {}
    mapping: dict[str, str] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            pmid, pmcid = row.get("pmid", ""), row.get("pmcid", "")
            if pmid and pmcid:
                mapping[pmid] = pmcid
    return mapping


def main() -> None:
    print("Downloading studies from PK-DB API ...")
    studies = collect_studies()
    (HERE / "studies_full.json").write_text(json.dumps(studies, indent=2))
    print(f"Wrote {HERE / 'studies_full.json'} ({len(studies)} studies)")

    pmcid_map = load_pmcid_map()

    # One row per unique PMID. Studies without a real (numeric) PMID are
    # dropped, and studies that share a PMID collapse to a single row.
    rows = []
    seen: set[str] = set()
    for s in studies:
        ref = s.get("reference") or {}
        pmid = str(ref.get("pmid") or "").strip()
        if not pmid.isdigit() or pmid in seen:
            continue
        seen.add(pmid)
        rows.append({
            "pmid": pmid,
            "pmcid": pmcid_map.get(pmid, ""),
            "title": (ref.get("title") or "").strip(),
            "abstract": (ref.get("abstract") or "").strip(),
        })

    out = HERE / "studies_metadata.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pmid", "pmcid", "title", "abstract"])
        w.writeheader()
        w.writerows(rows)

    with_pmcid = sum(1 for r in rows if r["pmcid"])
    with_abstract = sum(1 for r in rows if r["abstract"])
    print("\n=== RESULT ===")
    print(f"unique pmids   : {len(rows)}")
    print(f"with pmcid     : {with_pmcid}")
    print(f"with abstract  : {with_abstract}")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
