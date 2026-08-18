#!/usr/bin/env python3
"""
Resolve how many PK-DB studies have a PMCID (PubMed Central full-text record).

Steps:
  1. Page through the anonymous PK-DB studies API and collect every study's
     PMID (from study.reference.pmid).
  2. Convert PMID -> PMCID with pubmed_markdown.get_pmcid_from_pmid, which wraps
     NCBI's ID Converter API (batches of 200).
  3. Write the mapping + a summary into this folder (pkdb-api/).

Outputs (written next to this script):
  studies_pmids.json   -> [{sid, pmid}, ...] for all studies
  pmid_to_pmcid.csv    -> sid, pmid, pmcid   (pmcid blank if none)
  summary.json         -> counts
"""
from __future__ import annotations

import csv
import json
import os
import urllib.request
from pathlib import Path

import time

from dotenv import load_dotenv
import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
load_dotenv(ROOT / ".env", override=True)

API = "https://pk-db.com/api/v1/studies/"
EMAIL = os.environ.get("NCBI_EMAIL", "shlok@gxl.ai")
PAGE_SIZE = 100


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "pkdb-viewer/pmcid-resolver"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def collect_studies() -> list[dict]:
    """Return [{sid, pmid}] for every study in the API.

    PK-DB wraps results as {current_page, last_page, next_page_url,
    data: {count, data: [...studies...]}}.
    """
    studies: list[dict] = []
    url = f"{API}?format=json&page_size={PAGE_SIZE}"
    while url:
        payload = fetch_json(url)
        block = payload.get("data", {})
        total = block.get("count")
        for s in block.get("data", []):
            ref = s.get("reference") or {}
            studies.append({"sid": s.get("sid"), "pmid": ref.get("pmid")})
        print(f"  page {payload.get('current_page')}/{payload.get('last_page')}: "
              f"{len(studies)}/{total} studies collected")
        url = payload.get("next_page_url")
    return studies


IDCONV = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"


def convert_pmids(pmids: list[str], batch_size: int = 100) -> dict[str, str | None]:
    """PMID -> PMCID via NCBI ID Converter, same endpoint pubmed_markdown wraps.

    Unlike the library, a failed batch is RETRIED (backoff) rather than
    silently mapped to None, so throttling can't undercount PMCIDs. Raises if a
    batch never succeeds, so the final count is trustworthy.
    """
    out: dict[str, str | None] = {}
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i + batch_size]
        params = {
            "tool": "pkdb-viewer",
            "email": EMAIL,
            "ids": ",".join(batch),
            "format": "json",
        }
        for attempt in range(6):
            try:
                r = requests.get(IDCONV, params=params, timeout=60)
                r.raise_for_status()
                records = r.json().get("records", [])
                for rec in records:
                    pmid = str(rec.get("pmid")).strip() if rec.get("pmid") else None
                    if pmid:
                        out[pmid] = rec.get("pmcid") or None
                for p in batch:
                    out.setdefault(p, None)
                break
            except Exception as e:  # noqa: BLE001 - retry any transient failure
                if attempt == 5:
                    raise RuntimeError(
                        f"batch at index {i} failed after 6 tries: {e}"
                    ) from e
                time.sleep(1.5 * (attempt + 1))
        print(f"  converted {min(i + batch_size, len(pmids))}/{len(pmids)} PMIDs")
        time.sleep(0.4)
    return out


def main() -> None:
    print("Collecting studies from PK-DB API ...")
    studies = collect_studies()
    (HERE / "studies_pmids.json").write_text(json.dumps(studies, indent=2))

    # Some studies carry a non-numeric placeholder in the pmid slot
    # (e.g. "PVLDrugs", "Villesen2006"); those aren't real PMIDs and a single
    # bad id makes NCBI reject the whole batch, so drop them before converting.
    with_pmid = [s for s in studies if s["pmid"] and str(s["pmid"]).isdigit()]
    non_numeric = [s for s in studies if s["pmid"] and not str(s["pmid"]).isdigit()]
    pmids = sorted({s["pmid"] for s in with_pmid})
    print(f"\n{len(studies)} studies total, {len(with_pmid)} with a numeric PMID "
          f"({len(pmids)} unique), {len(non_numeric)} with a non-numeric ref id, "
          f"{len(studies) - len(with_pmid) - len(non_numeric)} with no pmid")

    print("Converting PMID -> PMCID via NCBI ID Converter ...")
    mapping = convert_pmids(pmids)

    rows = []
    for s in studies:
        pmid = s["pmid"]
        pmcid = mapping.get(pmid) if pmid else None
        rows.append({"sid": s["sid"], "pmid": pmid or "", "pmcid": pmcid or ""})

    with (HERE / "pmid_to_pmcid.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["sid", "pmid", "pmcid"])
        w.writeheader()
        w.writerows(rows)

    studies_with_pmcid = sum(1 for r in rows if r["pmcid"])
    pmids_with_pmcid = sum(1 for p in pmids if mapping.get(p))
    summary = {
        "studies_total": len(studies),
        "studies_with_pmid": len(with_pmid),
        "studies_with_pmcid": studies_with_pmcid,
        "unique_pmids": len(pmids),
        "unique_pmids_with_pmcid": pmids_with_pmcid,
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2))

    print("\n=== RESULT ===")
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {HERE}/pmid_to_pmcid.csv and summary.json")


if __name__ == "__main__":
    main()
