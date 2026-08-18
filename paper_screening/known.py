"""Load already-annotated PK-DB identifiers so they can be excluded from candidates."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PAPERS = ROOT / "pkdb_papers.txt"
DEFAULT_PMID_CSV = ROOT / "pkdb-api" / "pmid_to_pmcid.csv"


@dataclass
class KnownAnnotated:
    """PMIDs / PMCIDs already curated into PK-DB."""

    pmids: set[str] = field(default_factory=set)
    pmcids: set[str] = field(default_factory=set)  # normalized as PMC######

    def contains(self, *, pmid: str | None = None, pmcid: str | None = None) -> bool:
        if pmid and pmid.strip() in self.pmids:
            return True
        if pmcid:
            norm = _norm_pmcid(pmcid)
            if norm and norm in self.pmcids:
                return True
        return False


def _norm_pmcid(value: str) -> str:
    v = value.strip().upper()
    if not v:
        return ""
    if v.startswith("PMC"):
        return v
    if v.isdigit():
        return f"PMC{v}"
    return v


def load_known(
    papers_csv: Path | None = None,
    pmid_map_csv: Path | None = None,
) -> KnownAnnotated:
    known = KnownAnnotated()
    papers = papers_csv or DEFAULT_PAPERS
    pmid_map = pmid_map_csv or DEFAULT_PMID_CSV

    if papers.exists():
        with papers.open(newline="") as f:
            for row in csv.DictReader(f):
                pmid = (row.get("pmid") or "").strip()
                pmcid = _norm_pmcid(row.get("pmcid") or "")
                if pmid:
                    known.pmids.add(pmid)
                if pmcid:
                    known.pmcids.add(pmcid)

    if pmid_map.exists():
        with pmid_map.open(newline="") as f:
            for row in csv.DictReader(f):
                pmid = (row.get("pmid") or "").strip()
                pmcid = _norm_pmcid(row.get("pmcid") or "")
                if pmid:
                    known.pmids.add(pmid)
                if pmcid:
                    known.pmcids.add(pmcid)

    return known
