"""Rule-based keyword scorer for PKDB annotation relevance.

No LLM calls. Scores title + abstract (+ optional full text) using positive /
negative lexical signals and the abstract term signature of
pkdb-api/pkdb_papers.txt.

Design notes:
- "AUC" is heavily contaminated by ML/radiomics ROC-AUC papers → gated.
- "clearance" alone is weak (renal/bacterial/viral).
- Concentration-time + human dosing cues are strong positives.
- Abstracts that frame PD / assay / CYP-phenotyping without PK params score lower
  (still may pass if params appear).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# ---------------------------------------------------------------------------
# Pattern libraries
# ---------------------------------------------------------------------------

def _alt(terms: Iterable[str]) -> re.Pattern[str]:
    return re.compile("|".join(terms), re.IGNORECASE)


# Strong PK framing
PK_CORE = _alt(
    [
        r"\bpharmacokinetic(?:s|al)?\b",
        r"\bpk\s*(?:profile|parameter|study|studies|analysis)\b",
        r"\bconcentration[-\s]?time\b",
        r"\bplasma\s+concentration(?:s)?\b",
        r"\bserum\s+concentration(?:s)?\b",
        r"\bdisposition\b.{0,40}\b(?:drug|compound|metabolite)\b",
    ]
)

# Numeric PK endpoints PK-DB actually curates
PK_PARAMS = _alt(
    [
        r"\bcmax\b",
        r"\btmax\b",
        r"\bauc(?:inf|0|τ|tau|ss)?\b",
        r"\barea\s+under\s+(?:the\s+)?(?:plasma\s+|serum\s+|concentration[-\s]?time\s+)?curve\b",
        r"\bhalf[-\s]?life\b",
        r"\bt1/?2\b",
        r"\bvolume\s+of\s+distribution\b",
        r"\bvd(?:ss|z|β|beta)?\b",
        r"\bbioavailability\b",
        r"\babsolute\s+bioavailability\b",
        r"\bclearance\b",  # gated below when non-PK sense dominates
        r"\bcl(?:/f)?\b",
    ]
)

# Human / clinical study cues
CLINICAL = _alt(
    [
        r"\bhealthy\s+volunteers?\b",
        r"\bhealthy\s+subjects?\b",
        r"\bhealthy\s+(?:adult|chinese|japanese|male|female)\b",
        r"\bsingle\s+dose\b",
        r"\bmultiple\s+dose(?:s)?\b",
        r"\boral\s+administration\b",
        r"\bintravenous\s+(?:administration|infusion|bolus)\b",
        r"\bsteady[-\s]?state\b",
        r"\bhuman\s+(?:subjects?|volunteers?|participants?)\b",
        r"\bphase\s+[i1]\b",
        r"\bcrossover\b",
        r"\bbioequivalence\b",
        r"\bdrug[-\s]?drug\s+interaction\b",
        r"\bplasma\s+(?:levels?|profiles?)\b",
    ]
)

# Explicit figure/curve language (proxy for digitizable time-courses)
CURVE = _alt(
    [
        r"\bconcentration[-\s]?time\s+(?:curve|profile|plot|graph|figure)\b",
        r"\bpk\s+profile(?:s)?\b",
        r"\bplasma\s+concentration[-\s]?time\b",
        r"\btimecourse(?:s)?\b",
        r"\btime[-\s]?course(?:s)?\b",
    ]
)

# --- Hard / soft negatives (precision killers from labeling) ---

# ML / radiomics where AUC ≠ PK AUC
ML_AUC_CONTEXT = _alt(
    [
        r"\bradiomic",
        r"\bmachine[\s-]?learning\b",
        r"\bdeep[\s-]?learning\b",
        r"\bneural\s+network",
        r"\bclassifier\b",
        r"\bclassification\s+model\b",
        r"\broc\b",
        r"\bauroc\b",
        r"\barea\s+under\s+(?:the\s+)?roc\b",
        r"\bauc\s+of\s+the\s+roc\b",
        r"\breceiver[\s-]?operating\b",
        r"\bpredict(?:ion|ive)\s+model\b",
        r"\bxgboost\b",
        r"\brandom\s+forest\b",
        r"\bsvm\b",
        r"\bshap\b",
    ]
)

NON_PK_CLEARANCE = _alt(
    [
        r"\bbacterial\s+clearance\b",
        r"\bviral\s+clearance\b",
        r"\btumor\s+clearance\b",
        r"\bmucus\s+clearance\b",
        r"\bneutrophil\s+clearance\b",
        r"\bpathogen\s+clearance\b",
    ]
)

# Soft penalties (still may pass if real PK signals are strong)
SOFT_NEG = _alt(
    [
        r"\bnanoparticle",
        r"\bnanomedicine\b",
        r"\bliposom",
        r"\bin\s+vitro\b",
        r"\bmurine\b",
        r"\bmouse\b",
        r"\brats?\b",
        r"\bthis\s+review\b",
        r"\bwe\s+review\b",
        r"\bnarrative\s+review\b",
        r"\bsystematic\s+review\b",
        r"\bmeta[\s-]?analysis\b",
        r"\beducational\b",
    ]
)

# Require at least one of these families for a pass (when not hard-rejected)
_PARAM_TOKEN = re.compile(
    r"\b(?:cmax|tmax|half[-\s]?life|t1/?2|bioavailability|vd(?:ss|z)?|"
    r"volume\s+of\s+distribution|auc(?:inf|0|ss)?|clearance|cl(?:/f)?)\b",
    re.IGNORECASE,
)


@dataclass
class ScoreBreakdown:
    pk_core: int = 0
    pk_params: int = 0
    clinical: int = 0
    curve: int = 0
    soft_neg: int = 0
    hard_reject: bool = False
    reject_reasons: list[str] = field(default_factory=list)
    hit_terms: list[str] = field(default_factory=list)


@dataclass
class ScoreResult:
    score: float
    passed: bool
    grade: str  # "strong" | "moderate" | "weak" | "reject"
    breakdown: ScoreBreakdown
    reasons: list[str]

    def as_dict(self) -> dict:
        return {
            "score": round(self.score, 2),
            "passed": self.passed,
            "grade": self.grade,
            "reasons": self.reasons,
            "breakdown": {
                "pk_core": self.breakdown.pk_core,
                "pk_params": self.breakdown.pk_params,
                "clinical": self.breakdown.clinical,
                "curve": self.breakdown.curve,
                "soft_neg": self.breakdown.soft_neg,
                "hard_reject": self.breakdown.hard_reject,
                "reject_reasons": self.breakdown.reject_reasons,
                "hit_terms": self.breakdown.hit_terms,
            },
        }


def _count_hits(pattern: re.Pattern[str], text: str, limit: int = 8) -> tuple[int, list[str]]:
    hits = pattern.findall(text)
    # normalize to unique-ish strings
    seen: list[str] = []
    for h in hits:
        s = h if isinstance(h, str) else h[0]
        s = s.lower().strip()
        if s and s not in seen:
            seen.append(s)
        if len(seen) >= limit:
            break
    return len(seen), seen


def score_text(title: str, abstract: str = "", fulltext: str = "") -> ScoreResult:
    """Score a paper from title/abstract and optional full-text markdown/plain text."""
    title = title or ""
    abstract = abstract or ""
    # Prefer abstract for ranking; use a capped slice of fulltext so huge .md
    # files don't dominate (and keep runtime cheap).
    body = f"{title}\n{abstract}"
    if fulltext:
        body = f"{body}\n{fulltext[:20000]}"

    bd = ScoreBreakdown()
    reasons: list[str] = []

    # --- hard rejects ---
    ml_n, ml_hits = _count_hits(ML_AUC_CONTEXT, body)
    has_auc = bool(re.search(r"\bauc\b", body, re.IGNORECASE))
    has_true_pk = bool(PK_CORE.search(body)) or bool(
        re.search(r"\b(?:cmax|half[-\s]?life|bioavailability|concentration[-\s]?time)\b", body, re.I)
    )
    if ml_n >= 2 and has_auc and not has_true_pk:
        bd.hard_reject = True
        bd.reject_reasons.append("ml_auc_context:" + ",".join(ml_hits[:4]))
    elif ml_n >= 1 and has_auc and not has_true_pk and not _PARAM_TOKEN.search(body):
        # Single ML cue + AUC with no real PK endpoint → reject
        bd.hard_reject = True
        bd.reject_reasons.append("likely_roc_auc:" + ",".join(ml_hits[:3]))

    np_n, np_hits = _count_hits(NON_PK_CLEARANCE, body)
    if np_n and not has_true_pk:
        bd.hard_reject = True
        bd.reject_reasons.append("non_pk_clearance:" + ",".join(np_hits[:3]))

    if bd.hard_reject:
        return ScoreResult(
            score=0.0,
            passed=False,
            grade="reject",
            breakdown=bd,
            reasons=bd.reject_reasons,
        )

    # --- positives ---
    bd.pk_core, core_hits = _count_hits(PK_CORE, body)
    bd.pk_params, param_hits = _count_hits(PK_PARAMS, body)
    bd.clinical, clin_hits = _count_hits(CLINICAL, body)
    bd.curve, curve_hits = _count_hits(CURVE, body)
    bd.soft_neg, soft_hits = _count_hits(SOFT_NEG, body)
    bd.hit_terms = core_hits + param_hits + clin_hits + curve_hits

    # Weighted score (tuned so classic clinical PK abstracts clear easily,
    # ML/ROC abstracts don't).
    score = (
        2.5 * min(bd.pk_core, 3)
        + 1.5 * min(bd.pk_params, 5)
        + 1.2 * min(bd.clinical, 4)
        + 1.5 * min(bd.curve, 2)
        - 1.0 * min(bd.soft_neg, 3)
    )

    # Extra boost when pharmacokinetics + at least one param co-occur
    if bd.pk_core and bd.pk_params:
        score += 1.5
        reasons.append("pk_core+params")
    if bd.curve and (bd.pk_core or bd.pk_params):
        score += 1.0
        reasons.append("concentration_time_curve")
    if bd.clinical and bd.pk_params:
        score += 0.8
        reasons.append("clinical+params")

    if soft_hits:
        reasons.append("soft_penalty:" + ",".join(soft_hits[:3]))

    # Pass logic: need real PK framing OR (params + clinical)
    passed = score >= 4.0 and (
        bd.pk_core >= 1
        or (bd.pk_params >= 2 and bd.clinical >= 1)
        or (bd.curve >= 1 and bd.pk_params >= 1)
    )

    if score >= 8.0 and passed:
        grade = "strong"
    elif passed:
        grade = "moderate"
    elif score > 0:
        grade = "weak"
    else:
        grade = "reject"
        passed = False

    if core_hits:
        reasons.append("core:" + ",".join(core_hits[:3]))
    if param_hits:
        reasons.append("params:" + ",".join(param_hits[:4]))
    if clin_hits:
        reasons.append("clinical:" + ",".join(clin_hits[:3]))

    return ScoreResult(
        score=score,
        passed=passed,
        grade=grade,
        breakdown=bd,
        reasons=reasons,
    )


def score_markdown(text: str, *, path: str | None = None) -> ScoreResult:
    """Score a local markdown / plain-text paper file.

    Heuristically splits a title from the first heading if present.
    """
    title = ""
    body = text
    # Common pubmed-markdown / pandoc title forms
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        title = m.group(1).strip()
    else:
        m = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", text, re.IGNORECASE | re.MULTILINE)
        if m:
            title = m.group(1).strip()
    # Prefer an Abstract section if present for scoring density
    abs_m = re.search(
        r"(?is)^(?:#{1,3}\s*)?abstract\s*\n(.+?)(?=\n#{1,3}\s|\nintroduction\b|\Z)",
        text,
    )
    abstract = abs_m.group(1).strip() if abs_m else ""
    result = score_text(title, abstract=abstract, fulltext=text)
    if path:
        result.reasons = [f"path:{path}", *result.reasons]
    return result
