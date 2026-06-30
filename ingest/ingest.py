#!/usr/bin/env python3
"""
PKDB viewer ingestion.

For every open-access study in PK-DB (https://pk-db.com), download:
  - study metadata + reference (title, abstract, authors, journal, pmid, doi)
  - curator descriptions
  - groups (with characteristica / demographics)
  - individuals (with characteristica)
  - interventions (dosing, normalized units)
  - the full text of the original paper as markdown

and write it all out as static files the viewer reads directly:

  public/data/index.json            -> list of studies (for the picker)
  public/data/<sid>/study.json      -> all extracted data for one study
  public/data/<sid>/paper.md        -> the original paper as markdown

Paper text:
  We try the pubmed-markdown package first (per project goal). Its PMC HTML
  scraper is frequently blocked by NCBI's browser/reCAPTCHA check, so we fall
  back to NCBI's official BioC full-text API, which returns clean structured
  full text plus the article licence. If neither yields full text we keep the
  abstract so the paper pane is never empty.

Outputs / timecourses / scatters are NOT exposed by the anonymous PK-DB API
(they require a curator login; the official data export returns them empty for
anonymous users), so they are intentionally absent from the data panel.

Usage:
  python ingest.py                # all open studies, skip ones already done
  python ingest.py --limit 5      # first 5 (smoke test)
  python ingest.py --force        # re-fetch even if already present
  python ingest.py --sid PKDB00249  # one specific study
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://pk-db.com/api/v1/"
BIOC = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmcid}/unicode"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "public" / "data"
EMAIL = os.environ.get("NCBI_EMAIL", "shlok@gxl.ai")

USER_AGENT = "pkdb-viewer-ingest/1.0 (+%s)" % EMAIL


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
def _get(url: str, *, tries: int = 4, expect_json: bool = True):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read().decode("utf-8", "replace")
            return json.loads(raw) if expect_json else raw
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed after {tries} tries: {url}\n  {last}")


def api(path: str, **params) -> dict:
    params.setdefault("format", "json")
    qs = urllib.parse.urlencode(params)
    return _get(f"{API}{path}?{qs}")


def paged(path: str, **params):
    """Yield every item across an elastic-paginated PK-DB list endpoint."""
    params["page_size"] = params.get("page_size", 500)
    page = 1
    while True:
        d = api(path, page=page, **params)["data"]
        for item in d["data"]:
            yield item
        last = d.get("count", 0)
        got = page * params["page_size"]
        if got >= last or not d["data"]:
            break
        page += 1


# --------------------------------------------------------------------------- #
# PK-DB data
# --------------------------------------------------------------------------- #
def list_open_studies() -> list[dict]:
    out = []
    d = api("studies/", licence="open", page_size=300)["data"]
    out.extend(d["data"])
    # the open set is small (<100); one large page is enough, but guard anyway
    while len(out) < d["count"]:
        page = len(out) // 300 + 1
        more = api("studies/", licence="open", page_size=300, page=page + 1)["data"]
        if not more["data"]:
            break
        out.extend(more["data"])
    return out


def fetch_study_data(sid: str) -> dict:
    """Return the full extracted-data bundle for one study."""
    detail = api(f"studies/{sid}/")
    ref = detail.get("reference") or {}

    # A filter result-set (uuid) lets us bulk-fetch the related entities.
    flt = api("filter/", **{"studies__sid": sid, "concise": "false"})
    uuid = flt.get("uuid")

    groups = list(paged("groups/", uuid=uuid)) if uuid else []
    individuals = list(paged("individuals/", uuid=uuid)) if uuid else []
    interventions = (
        list(paged("interventions/", uuid=uuid, normed="true")) if uuid else []
    )

    return {
        "sid": detail.get("sid"),
        "name": detail.get("name"),
        "licence": detail.get("licence"),
        "access": detail.get("access"),
        "date": detail.get("date"),
        "counts": {
            "groups": detail.get("group_count"),
            "individuals": detail.get("individual_count"),
            "interventions": detail.get("intervention_count"),
            "outputs": detail.get("output_count"),
            "timecourses": detail.get("timecourse_count"),
        },
        "reference": {
            "pmid": ref.get("pmid"),
            "doi": ref.get("doi"),
            "title": ref.get("title"),
            "abstract": ref.get("abstract"),
            "journal": ref.get("journal"),
            "date": ref.get("date"),
            "authors": [
                f"{a.get('first_name','')} {a.get('last_name','')}".strip()
                for a in (ref.get("authors") or [])
            ],
        },
        "curators": [
            f"{c.get('first_name','')} {c.get('last_name','')}".strip()
            for c in (detail.get("curators") or [])
        ],
        "descriptions": [d.get("text") for d in (detail.get("descriptions") or [])],
        "substances": detail.get("substances") or [],
        "groups": groups,
        "individuals": individuals,
        "interventions": interventions,
    }


# --------------------------------------------------------------------------- #
# Paper text
# --------------------------------------------------------------------------- #
def pmcid_from_pmid(pmid: str) -> str | None:
    try:
        d = api("references/", pmid=pmid)  # may not carry pmcid; ignore
    except Exception:  # noqa: BLE001
        pass
    # NCBI id converter
    url = (
        "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
        f"?ids={pmid}&format=json&tool=pkdb-viewer&email={urllib.parse.quote(EMAIL)}"
    )
    try:
        d = _get(url)
        recs = d.get("records") or []
        if recs and recs[0].get("pmcid"):
            return recs[0]["pmcid"]
    except Exception:  # noqa: BLE001
        return None
    return None


def _bioc_to_markdown(bioc: list) -> tuple[str | None, str | None]:
    """Convert NCBI BioC JSON to markdown. Returns (markdown, licence)."""
    try:
        doc = bioc[0]["documents"][0]
    except (IndexError, KeyError, TypeError):
        return None, None
    licence = (doc.get("infons") or {}).get("license")
    parts: list[str] = []
    last_section = None
    for p in doc.get("passages", []):
        infons = p.get("infons") or {}
        ptype = infons.get("type") or ""
        section = infons.get("section_type") or ""
        text = (p.get("text") or "").strip()
        if not text:
            continue
        if section == "REF":
            continue  # references handled separately / omitted
        if ptype in ("front", "title"):
            parts.append(f"# {text}\n")
        elif ptype in ("abstract_title_1", "title_1"):
            parts.append(f"\n## {text}\n")
        elif ptype in ("title_2", "title_3"):
            parts.append(f"\n### {text}\n")
        elif ptype == "fig_caption":
            parts.append(f"\n> **Figure.** {text}\n")
        elif ptype == "table_caption":
            parts.append(f"\n**{text}**\n")
        elif ptype in ("table", "table_foot"):
            parts.append(f"\n```\n{text}\n```\n")
        else:  # abstract, paragraph, anything else
            if section and section != last_section and section in (
                "INTRO",
                "METHODS",
                "RESULTS",
                "DISCUSS",
                "CONCL",
            ) and not any(text.startswith(h) for h in ("#",)):
                pass
            parts.append(text + "\n")
        last_section = section
    md = "\n".join(parts).strip()
    return (md or None), licence


def fetch_paper_via_bioc(pmcid: str) -> tuple[str | None, str | None]:
    try:
        bioc = _get(BIOC.format(pmcid=pmcid))
    except Exception:  # noqa: BLE001
        return None, None
    if isinstance(bioc, list):
        return _bioc_to_markdown(bioc)
    return None, None  # BioC returns an HTML error string when not in the OA set


# --- efetch NXML fallback (recovers OA articles missing from the BioC set) --- #
import xml.etree.ElementTree as ET  # noqa: E402


def _nxml_text(el) -> str:
    """Flatten an NXML element's inline text (xref/italic/etc.)."""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def _nxml_table_to_md(tbl) -> str:
    rows = []
    for tr in tbl.iter("tr"):
        cells = [
            _nxml_text(c) for c in tr if c.tag in ("td", "th")
        ]
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def _nxml_sec(sec, level: int, parts: list[str]) -> None:
    for child in sec:
        tag = child.tag
        if tag == "title":
            t = _nxml_text(child)
            if t:
                parts.append("\n" + "#" * min(level, 6) + " " + t + "\n")
        elif tag == "sec":
            _nxml_sec(child, level + 1, parts)
        elif tag == "p":
            t = _nxml_text(child)
            if t:
                parts.append(t + "\n")
        elif tag in ("table-wrap", "fig"):
            cap = child.find(".//caption")
            label = child.find("label")
            head = " ".join(
                filter(None, [_nxml_text(label) if label is not None else "",
                              _nxml_text(cap) if cap is not None else ""])
            )
            if tag == "fig":
                if head:
                    parts.append(f"\n> **{head}**\n")
            else:
                if head:
                    parts.append(f"\n**{head}**\n")
                tbl = child.find(".//table")
                if tbl is not None:
                    md = _nxml_table_to_md(tbl)
                    if md:
                        parts.append("\n" + md + "\n")
        elif tag in ("list",):
            for item in child.findall(".//list-item"):
                t = _nxml_text(item)
                if t:
                    parts.append(f"- {t}")
            parts.append("")


def _nxml_to_markdown(xml: str) -> str | None:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None
    art = root.find(".//article")
    if art is None:
        return None
    body = art.find(".//body")
    if body is None or len(list(body.iter("p"))) == 0:
        return None  # no machine-readable full text (scanned/historical)
    parts: list[str] = []
    title_el = art.find(".//article-title")
    if title_el is not None:
        parts.append(f"# {_nxml_text(title_el)}\n")
    abs = art.find(".//abstract")
    if abs is not None:
        parts.append("\n## Abstract\n")
        for p in abs.findall(".//p"):
            t = _nxml_text(p)
            if t:
                parts.append(t + "\n")
    for sec in body.findall("sec"):
        _nxml_sec(sec, 2, parts)
    # body paragraphs not wrapped in a sec
    for p in body.findall("p"):
        t = _nxml_text(p)
        if t:
            parts.append(t + "\n")
    md = "\n".join(parts).strip()
    return md if len(md) > 400 else None


def fetch_paper_via_efetch(pmcid: str) -> str | None:
    pmc_num = pmcid.replace("PMC", "")
    url = f"{EUTILS}?db=pmc&id={pmc_num}&rettype=xml&tool=pkdb-viewer&email={urllib.parse.quote(EMAIL)}"
    try:
        xml = _get(url, expect_json=False)
    except Exception:  # noqa: BLE001
        return None
    return _nxml_to_markdown(xml)


def fetch_paper_via_pubmed_markdown(pmcid: str) -> str | None:
    """Try the pubmed-markdown package. Returns None if blocked/captcha."""
    try:
        import pubmed_markdown as pm  # type: ignore
    except Exception:  # noqa: BLE001
        return None
    try:
        c = pm.PubMedMarkdown(save_dir="/tmp/pmtmp", email=EMAIL)
        md = c.pmcid_to_markdown(pmcid)
        if not isinstance(md, str):
            return None
        # Detect the reCAPTCHA / empty-page failure mode.
        if "reCAPTCHA" in md or "Checking your browser" in md or len(md) < 600:
            return None
        return md
    except Exception:  # noqa: BLE001
        return None


def abstract_markdown(study: dict) -> str:
    ref = study["reference"]
    lines = [f"# {ref.get('title') or study.get('name')}\n"]
    if ref.get("authors"):
        lines.append("*" + ", ".join(ref["authors"]) + "*\n")
    meta = []
    if ref.get("journal"):
        meta.append(ref["journal"])
    if ref.get("date"):
        meta.append(ref["date"])
    if meta:
        lines.append(" · ".join(meta) + "\n")
    if ref.get("abstract"):
        lines.append("\n## Abstract\n")
        lines.append(ref["abstract"])
    return "\n".join(lines)


def get_paper(study: dict) -> dict:
    """Returns {markdown, source, licence, pmcid}."""
    pmid = (study.get("reference") or {}).get("pmid")
    result = {"markdown": None, "source": None, "licence": None, "pmcid": None}
    pmcid = pmcid_from_pmid(pmid) if pmid else None
    result["pmcid"] = pmcid

    if pmcid:
        md = fetch_paper_via_pubmed_markdown(pmcid)
        if md:
            result.update(markdown=md, source="pubmed-markdown")
            return result
        md, licence = fetch_paper_via_bioc(pmcid)
        if md:
            result.update(markdown=md, source="bioc", licence=licence)
            return result
        md = fetch_paper_via_efetch(pmcid)
        if md:
            result.update(markdown=md, source="efetch")
            return result

    # Fallback: abstract only.
    result.update(markdown=abstract_markdown(study), source="abstract")
    return result


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def ingest_study(s: dict, *, force: bool) -> dict | None:
    sid = s["sid"]
    outdir = DATA_DIR / sid
    study_json = outdir / "study.json"
    paper_md = outdir / "paper.md"

    if study_json.exists() and paper_md.exists() and not force:
        existing = json.loads(study_json.read_text())
        print(f"  = {sid} already present, skipping")
        return existing.get("_index")

    print(f"  + {sid} ({s.get('name')}) ...", flush=True)
    data = fetch_study_data(sid)
    paper = get_paper(data)

    outdir.mkdir(parents=True, exist_ok=True)
    paper_md.write_text(paper["markdown"] or "")

    index_entry = {
        "sid": sid,
        "name": data.get("name"),
        "title": data["reference"].get("title"),
        "pmid": data["reference"].get("pmid"),
        "journal": data["reference"].get("journal"),
        "year": (data["reference"].get("date") or "")[:4],
        "substances": [
            (x.get("label") or x.get("name")) if isinstance(x, dict) else x
            for x in (data.get("substances") or [])
        ],
        "n_groups": data["counts"].get("groups"),
        "n_individuals": data["counts"].get("individuals"),
        "n_interventions": data["counts"].get("interventions"),
        "paper_source": paper["source"],
        "paper_licence": paper["licence"],
    }
    data["_index"] = index_entry
    data["paper"] = {
        "source": paper["source"],
        "licence": paper["licence"],
        "pmcid": paper["pmcid"],
    }
    study_json.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(
        f"    -> paper via {paper['source']}"
        f"{' ('+paper['licence']+')' if paper['licence'] else ''}; "
        f"{len(data['groups'])} groups, {len(data['individuals'])} indiv, "
        f"{len(data['interventions'])} interventions",
        flush=True,
    )
    return index_entry


def upgrade_papers() -> None:
    """Retry full-text retrieval for studies currently at abstract-only."""
    index_path = DATA_DIR / "index.json"
    index = {e["sid"]: e for e in json.loads(index_path.read_text())["studies"]}
    targets = sorted(p.parent for p in DATA_DIR.glob("*/study.json"))
    upgraded = 0
    for outdir in targets:
        sid = outdir.name
        data = json.loads((outdir / "study.json").read_text())
        if data.get("paper", {}).get("source") != "abstract":
            continue
        pmcid = data.get("paper", {}).get("pmcid")
        if not pmcid:
            continue
        md = fetch_paper_via_pubmed_markdown(pmcid)
        source, licence = "pubmed-markdown", None
        if not md:
            md, licence = fetch_paper_via_bioc(pmcid)
            source = "bioc"
        if not md:
            md = fetch_paper_via_efetch(pmcid)
            source, licence = "efetch", None
        if md:
            (outdir / "paper.md").write_text(md)
            data["paper"]["source"] = source
            data["paper"]["licence"] = licence
            if sid in index:
                index[sid]["paper_source"] = source
                index[sid]["paper_licence"] = licence
            (outdir / "study.json").write_text(
                json.dumps(data, indent=2, ensure_ascii=False)
            )
            upgraded += 1
            print(f"  ^ {sid} ({data.get('name')}) upgraded -> {source}", flush=True)
        time.sleep(0.4)
    out = sorted(index.values(), key=lambda e: (e.get("name") or ""))
    payload = json.loads(index_path.read_text())
    payload["studies"] = out
    index_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\nUpgraded {upgraded} studies to full text.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--sid", default=None)
    ap.add_argument(
        "--upgrade-papers",
        action="store_true",
        help="Re-attempt full text for studies currently stored as abstract-only "
        "(uses the saved PMCID; does not re-fetch PK-DB data).",
    )
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.upgrade_papers:
        upgrade_papers()
        return

    print("Fetching open-access study list ...", flush=True)
    studies = list_open_studies()
    print(f"  {len(studies)} open-access studies", flush=True)

    if args.sid:
        studies = [s for s in studies if s["sid"] == args.sid]
    if args.limit:
        studies = studies[: args.limit]

    index: list[dict] = []
    # preserve any already-built entries not in this run
    index_path = DATA_DIR / "index.json"
    existing_index = {}
    if index_path.exists():
        for e in json.loads(index_path.read_text()).get("studies", []):
            existing_index[e["sid"]] = e

    for i, s in enumerate(studies, 1):
        print(f"[{i}/{len(studies)}]", end=" ")
        try:
            entry = ingest_study(s, force=args.force)
            if entry:
                existing_index[entry["sid"]] = entry
        except Exception as e:  # noqa: BLE001
            print(f"  ! {s['sid']} failed: {e}", file=sys.stderr, flush=True)
        time.sleep(0.4)  # be polite to NCBI / PK-DB

    index = sorted(existing_index.values(), key=lambda e: (e.get("name") or ""))
    index_path.write_text(
        json.dumps(
            {
                "generated": time.strftime("%Y-%m-%d"),
                "count": len(index),
                "note": "Open-access PK-DB studies. Outputs/timecourses are "
                "not available via the anonymous PK-DB API.",
                "studies": index,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"\nDone. index.json has {len(index)} studies.")


if __name__ == "__main__":
    main()
