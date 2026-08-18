"""End-to-end: NCBI keyword search → abstract fetch → rule-based score → ranked candidates."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .known import KnownAnnotated, load_known
from .ncbi import NcbiClient
from .queries import TIERS, build_term
from .score import ScoreResult, score_text


@dataclass
class Candidate:
    pmid: str
    pmcid: str
    title: str
    abstract: str
    year: str
    journal: str
    source: str  # "pmc_search" | "local"
    already_annotated: bool
    score: ScoreResult

    def as_dict(self) -> dict:
        return {
            "pmid": self.pmid,
            "pmcid": self.pmcid,
            "title": self.title,
            "abstract": self.abstract[:2000],
            "year": self.year,
            "journal": self.journal,
            "source": self.source,
            "already_annotated": self.already_annotated,
            **self.score.as_dict(),
        }


def search_candidates(
    *,
    tier: str = "params",
    oa_only: bool = True,
    limit: int = 200,
    retstart: int = 0,
    extra: str | None = None,
    exclude_known: bool = True,
    passed_only: bool = True,
    client: NcbiClient | None = None,
    known: KnownAnnotated | None = None,
) -> tuple[list[Candidate], dict]:
    """Search PMC, score abstracts, return ranked candidates + run metadata.

    Parameters
    ----------
    tier:
        One of ``queries.TIERS`` — default ``params`` (tier-3 funnel).
    oa_only:
        Restrict to PMC Open Access Subset (text-mineable).
    limit:
        Max PMC hits to fetch and score.
    exclude_known:
        Drop papers already in PK-DB.
    passed_only:
        Keep only scorer-passing papers in the returned list (metadata still
        records how many were rejected).
    """
    if tier not in TIERS:
        raise ValueError(f"unknown tier {tier!r}; choose from {sorted(TIERS)}")

    client = client or NcbiClient()
    known = known or load_known()
    term = build_term(tier, oa_only=oa_only, extra=extra)

    pmc_ids, total = client.esearch_ids(term, db="pmc", retmax=limit, retstart=retstart)
    meta = {
        "term": term,
        "tier": tier,
        "oa_only": oa_only,
        "pmc_total_for_term": total,
        "pmc_fetched": len(pmc_ids),
        "retstart": retstart,
    }
    if not pmc_ids:
        return [], meta

    records = client.fetch_pmc_records(pmc_ids)

    candidates: list[Candidate] = []
    n_known = n_reject = n_pass = n_no_abstract = 0
    for rec in records:
        pmid = rec.get("pmid") or ""
        pmcid = rec.get("pmcid") or ""
        if pmcid and not pmcid.upper().startswith("PMC"):
            pmcid = f"PMC{pmcid}"
        if not (rec.get("abstract") or "").strip():
            n_no_abstract += 1
        is_known = known.contains(pmid=pmid or None, pmcid=pmcid or None)
        if is_known:
            n_known += 1
            if exclude_known:
                continue
        result = score_text(rec.get("title") or "", abstract=rec.get("abstract") or "")
        if result.passed:
            n_pass += 1
        else:
            n_reject += 1
        if passed_only and not result.passed:
            continue
        candidates.append(
            Candidate(
                pmid=pmid,
                pmcid=pmcid,
                title=rec.get("title") or "",
                abstract=rec.get("abstract") or "",
                year=rec.get("year") or "",
                journal=rec.get("journal") or "",
                source="pmc_search",
                already_annotated=is_known,
                score=result,
            )
        )

    candidates.sort(key=lambda c: (-c.score.score, c.pmid))
    meta.update(
        {
            "records_summarized": len(records),
            "missing_abstract": n_no_abstract,
            "excluded_already_annotated": n_known if exclude_known else 0,
            "scored_pass": n_pass,
            "scored_reject": n_reject,
            "returned": len(candidates),
        }
    )
    return candidates, meta

def write_jsonl(candidates: list[Candidate], path: Path, meta: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        if meta:
            f.write(json.dumps({"_meta": meta}) + "\n")
        for c in candidates:
            f.write(json.dumps(c.as_dict(), ensure_ascii=False) + "\n")


def write_csv(candidates: list[Candidate], path: Path) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "score",
        "grade",
        "passed",
        "pmid",
        "pmcid",
        "year",
        "journal",
        "title",
        "already_annotated",
        "reasons",
    ]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for c in candidates:
            w.writerow(
                {
                    "score": round(c.score.score, 2),
                    "grade": c.score.grade,
                    "passed": c.score.passed,
                    "pmid": c.pmid,
                    "pmcid": c.pmcid,
                    "year": c.year,
                    "journal": c.journal,
                    "title": c.title,
                    "already_annotated": c.already_annotated,
                    "reasons": "; ".join(c.score.reasons),
                }
            )
