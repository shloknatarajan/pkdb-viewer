#!/usr/bin/env python3
"""Download markdown for every PMCID in pmcids.txt.

Primary source: pubmed-markdown (PMC HTML). NCBI often returns a reCAPTCHA
interstitial, so we fall back to BioC then efetch NXML — same chain as
ingest/ingest.py.

Usage:
  ingest/.venv/bin/python variantAnnotations/download_papers.py
  ingest/.venv/bin/python variantAnnotations/download_papers.py --limit 5
  ingest/.venv/bin/python variantAnnotations/download_papers.py --force
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
# Prefer repo .env over any stale shell export of NCBI_EMAIL.
load_dotenv(ROOT / ".env", override=True)

sys.path.insert(0, str(ROOT / "ingest"))

from ingest import (  # noqa: E402
    EMAIL,
    fetch_paper_via_bioc,
    fetch_paper_via_efetch,
    fetch_paper_via_pubmed_markdown,
)

PMCIDS_PATH = HERE / "pmcids.txt"
OUT_DIR = HERE / "papers"
MANIFEST_PATH = OUT_DIR / "manifest.jsonl"


def load_pmcids() -> list[str]:
    return [ln.strip() for ln in PMCIDS_PATH.read_text().splitlines() if ln.strip()]


def already_done(force: bool) -> set[str]:
    if force or not MANIFEST_PATH.exists():
        return set()
    done: set[str] = set()
    for line in MANIFEST_PATH.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("ok") and rec.get("pmcid"):
            done.add(rec["pmcid"])
    return done


def fetch_one(pmcid: str) -> dict:
    md = fetch_paper_via_pubmed_markdown(pmcid)
    if md:
        return {"markdown": md, "source": "pubmed-markdown"}

    md, licence = fetch_paper_via_bioc(pmcid)
    if md:
        return {"markdown": md, "source": "bioc", "licence": licence}

    md = fetch_paper_via_efetch(pmcid)
    if md:
        return {"markdown": md, "source": "efetch"}

    return {"markdown": None, "source": None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0, help="Only process N PMCIDs")
    ap.add_argument("--force", action="store_true", help="Re-download even if present")
    ap.add_argument(
        "--delay",
        type=float,
        default=0.35,
        help="Seconds between downloads (NCBI politeness)",
    )
    args = ap.parse_args()

    email = os.environ.get("NCBI_EMAIL") or EMAIL
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pmcids = load_pmcids()
    if args.limit:
        pmcids = pmcids[: args.limit]

    done = already_done(args.force)
    todo = [p for p in pmcids if p not in done]
    print(f"NCBI_EMAIL: {email}")
    print(
        f"PMCIDs: {len(pmcids)} total, {len(done)} already done, {len(todo)} to fetch"
    )
    print(f"Output: {OUT_DIR}")

    ok = fail = 0
    t0 = time.time()
    with MANIFEST_PATH.open("a") as manifest:
        for i, pmcid in enumerate(todo, 1):
            try:
                result = fetch_one(pmcid)
            except Exception as e:  # noqa: BLE001
                result = {"markdown": None, "source": None, "error": str(e)}

            md = result.get("markdown")
            source = result.get("source")
            rec = {
                "pmcid": pmcid,
                "ok": bool(md),
                "source": source,
                "chars": len(md) if md else 0,
            }
            if result.get("licence"):
                rec["licence"] = result["licence"]
            if result.get("error"):
                rec["error"] = result["error"]

            if md:
                (OUT_DIR / f"{pmcid}.md").write_text(md)
                ok += 1
            else:
                fail += 1

            manifest.write(json.dumps(rec) + "\n")
            manifest.flush()

            elapsed = time.time() - t0
            rate = i / elapsed if elapsed else 0
            eta = (len(todo) - i) / rate if rate else 0
            print(
                f"[{i}/{len(todo)}] {pmcid} -> {source or 'FAIL'} "
                f"({rec['chars']} chars)  "
                f"ok={ok} fail={fail}  eta={eta/60:.1f}m",
                flush=True,
            )
            time.sleep(args.delay)

    print(f"Done. ok={ok} fail={fail}  wrote {OUT_DIR}")
    return 0 if fail == 0 or ok > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
