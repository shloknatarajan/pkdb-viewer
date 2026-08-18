"""Screen a directory of local markdown / text paper files with the keyword scorer."""
from __future__ import annotations

import re
from pathlib import Path

from .known import KnownAnnotated, load_known
from .pipeline import Candidate
from .score import score_markdown

_PMCID_IN_NAME = re.compile(r"(PMC\d+)", re.IGNORECASE)
_PMID_IN_NAME = re.compile(r"(?:PMID)?[_\-]?(\d{6,9})", re.IGNORECASE)


def _ids_from_path(path: Path) -> tuple[str, str]:
    name = path.stem
    pmc = ""
    m = _PMCID_IN_NAME.search(name)
    if m:
        pmc = m.group(1).upper()
    pmid = ""
    # Prefer explicit PMID prefix; otherwise leave blank to avoid false IDs
    m = re.search(r"PMID[_\-]?(\d{6,9})", name, re.IGNORECASE)
    if m:
        pmid = m.group(1)
    return pmid, pmc


def screen_local_dir(
    directory: Path,
    *,
    glob: str = "*.md",
    exclude_known: bool = True,
    passed_only: bool = True,
    known: KnownAnnotated | None = None,
    limit: int | None = None,
) -> tuple[list[Candidate], dict]:
    """Score every matching file under ``directory`` (non-recursive by default pattern)."""
    directory = Path(directory)
    known = known or load_known()
    paths = sorted(directory.glob(glob))
    if limit is not None:
        paths = paths[:limit]

    candidates: list[Candidate] = []
    n_known = n_pass = n_reject = n_empty = 0
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            n_empty += 1
            continue
        if not text.strip():
            n_empty += 1
            continue
        pmid, pmcid = _ids_from_path(path)
        # Also scan file header for ids
        head = text[:2000]
        if not pmcid:
            m = _PMCID_IN_NAME.search(head)
            if m:
                pmcid = m.group(1).upper()
        if not pmid:
            m = re.search(r"\bPMID[:\s]+(\d{6,9})\b", head, re.IGNORECASE)
            if m:
                pmid = m.group(1)

        is_known = known.contains(pmid=pmid or None, pmcid=pmcid or None)
        if is_known:
            n_known += 1
            if exclude_known:
                continue

        result = score_markdown(text, path=str(path))
        if result.passed:
            n_pass += 1
        else:
            n_reject += 1
        if passed_only and not result.passed:
            continue

        # Title: first heading or filename
        title_m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = title_m.group(1).strip() if title_m else path.stem
        abs_m = re.search(
            r"(?is)^(?:#{1,3}\s*)?abstract\s*\n(.+?)(?=\n#{1,3}\s|\nintroduction\b|\Z)",
            text,
        )
        abstract = abs_m.group(1).strip()[:2000] if abs_m else text[:500]

        candidates.append(
            Candidate(
                pmid=pmid,
                pmcid=pmcid,
                title=title,
                abstract=abstract,
                year="",
                journal="",
                source=f"local:{path}",
                already_annotated=is_known,
                score=result,
            )
        )

    candidates.sort(key=lambda c: (-c.score.score, c.source))
    meta = {
        "directory": str(directory),
        "glob": glob,
        "files_seen": len(paths),
        "empty_or_unreadable": n_empty,
        "excluded_already_annotated": n_known if exclude_known else 0,
        "scored_pass": n_pass,
        "scored_reject": n_reject,
        "returned": len(candidates),
    }
    return candidates, meta
