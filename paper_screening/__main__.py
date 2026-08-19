#!/usr/bin/env python3
"""CLI for PKDB annotation-candidate screening (keyword / logic only).

Examples
--------
Search PMC Open Access for high-precision clinical-PK candidates::

    python -m paper_screening search --tier params --limit 100 \\
        --out paper_screening/out/candidates.jsonl

Include weak/rejected hits for debugging the scorer::

    python -m paper_screening search --tier params --limit 50 --all \\
        --out paper_screening/out/debug.jsonl

Score a local folder of markdown papers (e.g. downloaded PMC)::

    python -m paper_screening local --dir path/to/papers --limit 200 \\
        --out paper_screening/out/local_ranked.jsonl

Score a single title/abstract::

    python -m paper_screening score --title "..." --abstract "..."
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .local import screen_local_dir
from .pipeline import search_candidates, write_csv, write_jsonl
from .queries import TIERS
from .score import score_text


def _add_common_filters(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--include-known",
        action="store_true",
        help="Keep papers already annotated in PK-DB (default: exclude them)",
    )
    p.add_argument(
        "--all",
        action="store_true",
        help="Return rejects/weak hits too (default: passed-only)",
    )


def cmd_search(args: argparse.Namespace) -> int:
    cands, meta = search_candidates(
        tier=args.tier,
        oa_only=not args.all_pmc,
        limit=args.limit,
        retstart=args.retstart,
        extra=args.extra,
        exclude_known=not args.include_known,
        passed_only=not args.all,
    )
    out = Path(args.out)
    write_jsonl(cands, out, meta=meta)
    if args.csv:
        write_csv(cands, Path(args.csv))
    print(json.dumps(meta, indent=2))
    print(f"wrote {len(cands)} candidates -> {out}")
    if cands:
        print("\nTop hits:")
        for c in cands[:10]:
            print(f"  {c.score.score:5.1f}  {c.score.grade:8s}  {c.pmcid or c.pmid:14s}  {c.title[:90]}")
    return 0


def cmd_local(args: argparse.Namespace) -> int:
    cands, meta = screen_local_dir(
        Path(args.dir),
        glob=args.glob,
        exclude_known=not args.include_known,
        passed_only=not args.all,
        limit=args.limit,
    )
    out = Path(args.out)
    write_jsonl(cands, out, meta=meta)
    if args.csv:
        write_csv(cands, Path(args.csv))
    print(json.dumps(meta, indent=2))
    print(f"wrote {len(cands)} candidates -> {out}")
    if cands:
        print("\nTop hits:")
        for c in cands[:10]:
            print(f"  {c.score.score:5.1f}  {c.score.grade:8s}  {c.pmcid or Path(c.source).name:14s}  {c.title[:90]}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    text = ""
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
        from .score import score_markdown

        result = score_markdown(text, path=args.file)
    else:
        result = score_text(args.title or "", abstract=args.abstract or "")
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.passed else 1


def cmd_tiers(_: argparse.Namespace) -> int:
    from .queries import build_term

    for name in TIERS:
        print(f"== {name} ==")
        print(f"  oa:  {build_term(name, oa_only=True)}")
        print(f"  all: {build_term(name, oa_only=False)}")
        print()
    return 0


def cmd_selftest(_: argparse.Namespace) -> int:
    """Offline assertions on known-good / known-bad abstracts (no network)."""
    cases = [
        (
            True,
            "Pharmacokinetics of midazolam in healthy volunteers",
            "Plasma concentration-time profiles after a single oral dose. Cmax, AUC and half-life reported.",
        ),
        (
            False,
            "Machine learning radiomics model with AUC 0.95",
            "XGBoost classifier and ROC analysis. Area under the ROC curve was 0.95. SHAP values shown.",
        ),
        (
            False,
            "Deep learning prediction of mortality",
            "Radiomics deep-learning signature. ROC yielded AUC of 0.89 for prediction.",
        ),
    ]
    failed = 0
    for expect_pass, title, abstract in cases:
        r = score_text(title, abstract)
        status = "ok" if r.passed == expect_pass else "FAIL"
        if status == "FAIL":
            failed += 1
        print(f"{status:4s} expect_pass={expect_pass} got={r.passed} score={r.score:.1f} :: {title[:70]}")
    print("selftest", "PASSED" if failed == 0 else f"FAILED ({failed})")
    return 0 if failed == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="paper_screening",
        description="Keyword/logic pipeline to find PKDB-annotatable papers (no LLMs).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="Search PMC and rank candidates")
    p_search.add_argument(
        "--tier",
        default="params",
        choices=sorted(TIERS),
        help="Search funnel tier (default: params = clinical PK with reported params)",
    )
    p_search.add_argument("--limit", type=int, default=100, help="Max PMC hits to fetch")
    p_search.add_argument("--retstart", type=int, default=0, help="esearch offset")
    p_search.add_argument(
        "--all-pmc",
        action="store_true",
        help="Search all PMC (not just Open Access Subset)",
    )
    p_search.add_argument("--extra", default=None, help="Extra AND clause for the esearch term")
    p_search.add_argument(
        "--out",
        default="paper_screening/out/candidates.jsonl",
        help="Output JSONL path",
    )
    p_search.add_argument("--csv", default=None, help="Also write a CSV summary")
    _add_common_filters(p_search)
    p_search.set_defaults(func=cmd_search)

    p_local = sub.add_parser("local", help="Score a directory of local markdown papers")
    p_local.add_argument("--dir", required=True, help="Directory of .md files")
    p_local.add_argument("--glob", default="*.md", help="Glob under --dir (default: *.md)")
    p_local.add_argument("--limit", type=int, default=None, help="Max files to score")
    p_local.add_argument(
        "--out",
        default="paper_screening/out/local_ranked.jsonl",
        help="Output JSONL path",
    )
    p_local.add_argument("--csv", default=None, help="Also write a CSV summary")
    _add_common_filters(p_local)
    p_local.set_defaults(func=cmd_local)

    p_score = sub.add_parser("score", help="Score one title/abstract or file")
    p_score.add_argument("--title", default="")
    p_score.add_argument("--abstract", default="")
    p_score.add_argument("--file", default=None, help="Markdown/text file to score")
    p_score.set_defaults(func=cmd_score)

    p_tiers = sub.add_parser("tiers", help="Print NCBI query strings for each tier")
    p_tiers.set_defaults(func=cmd_tiers)

    p_self = sub.add_parser("selftest", help="Offline scorer sanity checks (no network)")
    p_self.set_defaults(func=cmd_selftest)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
