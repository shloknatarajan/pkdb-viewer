"""PKDB annotation candidate screening — keyword / logic only (no LLMs).

Public API
----------
- ``search_candidates`` — PMC esearch → abstracts → rule score → ranked list
- ``screen_local_dir`` — score a folder of markdown papers the same way
- ``score_text`` / ``score_markdown`` — score one record
"""
from .known import KnownAnnotated, load_known
from .local import screen_local_dir
from .pipeline import Candidate, search_candidates, write_csv, write_jsonl
from .queries import TIERS, build_term
from .score import ScoreResult, score_markdown, score_text

__all__ = [
    "Candidate",
    "KnownAnnotated",
    "ScoreResult",
    "TIERS",
    "build_term",
    "load_known",
    "score_markdown",
    "score_text",
    "screen_local_dir",
    "search_candidates",
    "write_csv",
    "write_jsonl",
]
