#!/usr/bin/env python3
"""
PKDB viewer ingestion — from the curated CSV dump (PRIMARY source).

Why this replaces the live-API ingester
----------------------------------------
pk-db.com serves its measurement data (outputs, timecourses, scatters) from an
Elasticsearch backend that returns ZERO rows to anonymous callers. The
relational entities respond, but the actual PK numbers — the whole point — are
unretrievable from the API. So we ingest instead from the curated CSV dump the
PK-DB maintainers committed to their analysis repo:

    matthiaskoenig/pkdb_analysis @ develop
      -> tests/data/testdata_concise_false.zip

That zip is a `pkdb_analysis` export dated 2021-12-03 (8 CSVs, 661 studies). It
is the only public place the concentration-time and PK-parameter data is
actually retrievable. We use the 56 `licence=open` studies from it as the
viewer's study set, so study design AND findings come from one consistent
snapshot. Reference metadata + paper text still come from NCBI (reused from
ingest.py); for studies already on disk we reuse the saved reference/paper.

Output layout (unchanged, plus findings):
  public/data/index.json
  public/data/<sid>/study.json   # now includes outputs / timecourses / scatters
  public/data/<sid>/paper.md

Attribution: PK-DB (Grzegorzewski et al., Nucleic Acids Res. 2021,
doi:10.1093/nar/gkaa990). Terms: no restriction beyond the original data
owners; attribution required (see TERMS_OF_USE.md in the dump).

Usage:
  python ingest/ingest_dump.py                 # all 56 open studies
  python ingest/ingest_dump.py --limit 3       # smoke test
  python ingest/ingest_dump.py --sid PKDB00024
  python ingest/ingest_dump.py --no-paper      # skip NCBI; data only
"""
from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import math
import sys
import time
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

# Reuse the paper/reference NCBI pipeline from the live-API ingester.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ingest as live  # noqa: E402

ZIP_URL = (
    "https://raw.githubusercontent.com/matthiaskoenig/pkdb_analysis/"
    "develop/tests/data/testdata_concise_false.zip"
)
SNAPSHOT = "2021-12-03"
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "public" / "data"
CACHE = Path(__file__).resolve().parent / ".cache_testdata_concise_false.zip"

# PK-DB curator usernames -> display names (best-effort; falls back to username).
CURATORS = {
    "mkoenig": "Matthias König",
    "jbrandhorst": "Janosch Brandhorst",
    "jgrzegorzewski": "Jan Grzegorzewski",
    "deleftheriadou": "Dimitra Eleftheriadou",
    "kgreen": "Kathleen Green",
    "yduport": "Yannick Duport",
}

# Stat columns shared by characteristica / outputs.
STATS = ["value", "mean", "median", "min", "max", "sd", "se", "cv"]


# --------------------------------------------------------------------------- #
# Load the dump
# --------------------------------------------------------------------------- #
def load_zip() -> dict[str, list[dict]]:
    if CACHE.exists() and CACHE.stat().st_size > 1_000_000:
        blob = CACHE.read_bytes()
    else:
        print(f"downloading {ZIP_URL}", flush=True)
        blob = urllib.request.urlopen(ZIP_URL, timeout=120).read()
        CACHE.write_bytes(blob)
    tables: dict[str, list[dict]] = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for name in zf.namelist():
            if not name.endswith(".csv"):
                continue
            key = name[:-4]
            with zf.open(name) as fh:
                text = io.TextIOWrapper(fh, encoding="utf-8")
                tables[key] = list(csv.DictReader(text))
    return tables


# --------------------------------------------------------------------------- #
# Value coercion
# --------------------------------------------------------------------------- #
def s(v):
    v = (v or "").strip()
    return v or None


def num(v):
    v = (v or "").strip()
    if not v or v.lower() == "nan":
        return None
    try:
        f = float(v)
        return None if math.isnan(f) else (int(f) if f.is_integer() else f)
    except ValueError:
        return None


def parse_array(v):
    """Parse a stringified list like '[0.1, nan, 0.3]' -> [0.1, None, 0.3]."""
    v = (v or "").strip()
    if not v or v == "[]":
        return None
    try:
        vals = eval(v, {"__builtins__": {}}, {"nan": math.nan})  # noqa: S307
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(vals, (list, tuple)):
        return None
    return [None if (isinstance(x, float) and math.isnan(x)) else x for x in vals]


def node(sid, labels):
    sid = s(sid)
    if not sid:
        return None
    return {"sid": sid, "name": sid, "label": labels.get(sid, sid)}


def stats_block(row):
    return {k: num(row.get(k)) for k in STATS}


# --------------------------------------------------------------------------- #
# Reshape entities
# --------------------------------------------------------------------------- #
def build_groups(rows, labels):
    by_pk = defaultdict(list)
    for r in rows:
        by_pk[r["group_pk"]].append(r)
    groups = []
    for pk, rs in by_pk.items():
        head = rs[0]
        parent = s(head.get("group_parent_pk"))
        groups.append(
            {
                "pk": num(pk),
                "name": s(head.get("group_name")) or "group",
                "parent": {"pk": num(parent)} if parent else None,
                "count": num(head.get("group_count")),
                "characteristica": [
                    {
                        "pk": num(r.get("characteristica_pk")),
                        "count": num(r.get("count")),
                        "measurement_type": node(r.get("measurement_type"), labels),
                        "calculation_type": node(r.get("calculation_type"), labels),
                        "choice": node(r.get("choice"), labels),
                        "substance": node(r.get("substance"), labels),
                        **stats_block(r),
                        "unit": s(r.get("unit")),
                    }
                    for r in rs
                ],
            }
        )
    return groups


def build_individuals(rows, labels):
    by_pk = defaultdict(list)
    for r in rows:
        by_pk[r["individual_pk"]].append(r)
    out = []
    for pk, rs in by_pk.items():
        head = rs[0]
        gpk = s(head.get("individual_group_pk"))
        out.append(
            {
                "pk": num(pk),
                "name": s(head.get("individual_name")) or "individual",
                "group": {"pk": num(gpk)} if gpk else None,
                "characteristica": [
                    {
                        "pk": num(r.get("characteristica_pk")),
                        "measurement_type": node(r.get("measurement_type"), labels),
                        "calculation_type": node(r.get("calculation_type"), labels),
                        "choice": node(r.get("choice"), labels),
                        "substance": node(r.get("substance"), labels),
                        **stats_block(r),
                        "unit": s(r.get("unit")),
                    }
                    for r in rs
                ],
            }
        )
    return out


def build_interventions(rows, labels):
    out = []
    for r in rows:
        if s(r.get("normed")) not in ("True", "true", "1"):
            continue
        out.append(
            {
                "pk": num(r.get("intervention_pk")),
                "normed": True,
                "name": s(r.get("name")),
                "route": node(r.get("route"), labels),
                "form": node(r.get("form"), labels),
                "application": node(r.get("application"), labels),
                "time": s(r.get("time")),
                "time_end": s(r.get("time_end")),
                "time_unit": s(r.get("time_unit")),
                "measurement_type": node(r.get("measurement_type"), labels),
                "choice": node(r.get("choice"), labels),
                "substance": node(r.get("substance"), labels),
                **stats_block(r),
                "unit": s(r.get("unit")),
            }
        )
    return out


def build_outputs(rows, labels):
    """Scalar PK parameters (clearance, thalf, auc, cmax, ...). Normed only."""
    out = []
    for r in rows:
        if s(r.get("normed")) not in ("True", "true", "1"):
            continue
        out.append(
            {
                "pk": num(r.get("output_pk")),
                "measurement_type": node(r.get("measurement_type"), labels),
                "substance": node(r.get("substance"), labels),
                "tissue": node(r.get("tissue"), labels),
                "method": node(r.get("method"), labels),
                "calculation_type": node(r.get("calculation_type"), labels),
                "choice": node(r.get("choice"), labels),
                "label": s(r.get("label")),
                "time": num(r.get("time")),
                "time_unit": s(r.get("time_unit")),
                "intervention_pk": num(r.get("intervention_pk")),
                "group_pk": num(r.get("group_pk")),
                "individual_pk": num(r.get("individual_pk")),
                **stats_block(r),
                "unit": s(r.get("unit")),
            }
        )
    return out


def build_timecourses(rows, labels):
    out = []
    for r in rows:
        time = parse_array(r.get("time"))
        values = parse_array(r.get("value"))
        mean = parse_array(r.get("mean"))
        if not time or not (values or mean):
            continue
        out.append(
            {
                "pk": num(r.get("subset_pk")),
                "name": s(r.get("subset_name")),
                "label": s(r.get("label")),
                "measurement_type": node(r.get("measurement_type"), labels),
                "substance": node(r.get("substance"), labels),
                "tissue": node(r.get("tissue"), labels),
                "method": node(r.get("method"), labels),
                "intervention_pk": num(r.get("intervention_pk")),
                "group_pk": num(r.get("group_pk")),
                "individual_pk": num(r.get("individual_pk")),
                "time": time,
                "time_unit": s(r.get("time_unit")),
                "unit": s(r.get("unit")),
                "values": values,
                "mean": mean,
                "sd": parse_array(r.get("sd")),
            }
        )
    return out


def _axis(r, p, labels):
    return {
        "measurement_type": node(r.get(f"{p}_measurement_type"), labels),
        "substance": node(r.get(f"{p}_substance"), labels),
        "tissue": node(r.get(f"{p}_tissue"), labels),
        "label": s(r.get(f"{p}_label")),
        "unit": s(r.get(f"{p}_unit")),
        "values": parse_array(r.get(f"{p}_value")),
    }


def build_scatters(rows, labels):
    out = []
    for r in rows:
        out.append(
            {
                "pk": num(r.get("subset_pk")),
                "name": s(r.get("subset_name")),
                "x": _axis(r, "x", labels),
                "y": _axis(r, "y", labels),
            }
        )
    return out


# --------------------------------------------------------------------------- #
# Reference + paper
# --------------------------------------------------------------------------- #
def reference_from_disk(sid):
    p = DATA_DIR / sid / "study.json"
    if p.exists():
        j = json.loads(p.read_text())
        return j.get("reference"), j.get("paper"), j.get("substances")
    return None, None, None


def reference_from_ncbi(study_row, fetch_paper):
    pmid = s(study_row.get("reference_pmid"))
    ref = {
        "pmid": pmid,
        "doi": None,
        "title": s(study_row.get("reference_title")),
        "abstract": None,
        "journal": None,
        "date": s(study_row.get("reference_date")),
        "authors": [],
    }
    # Pull journal/authors/abstract/doi from PubMed esummary + efetch.
    if pmid:
        try:
            url = (
                f"{live.EUTILS.replace('efetch', 'esummary')}?db=pubmed&id={pmid}"
                f"&retmode=json&tool=pkdb-viewer&email={live.EMAIL}"
            )
            d = live._get(url)
            rec = (d.get("result") or {}).get(pmid, {})
            ref["journal"] = rec.get("fulljournalname") or rec.get("source")
            ref["authors"] = [a.get("name") for a in rec.get("authors", []) if a.get("name")]
            for aid in rec.get("articleids", []):
                if aid.get("idtype") == "doi":
                    ref["doi"] = aid.get("value")
            if rec.get("pubdate") and not ref["date"]:
                ref["date"] = rec["pubdate"]
        except Exception:  # noqa: BLE001
            pass
    paper = {"source": "abstract", "licence": None, "pmcid": None}
    if fetch_paper:
        got = live.get_paper({"reference": ref, "name": study_row.get("name")})
        ref["abstract"] = ref["abstract"] or None
        paper = {"source": got["source"], "licence": got["licence"], "pmcid": got["pmcid"]}
        return ref, paper, got["markdown"]
    return ref, paper, live.abstract_markdown({"reference": ref, "name": study_row.get("name")})


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def ingest(tables, study_row, *, fetch_paper):
    sid = study_row["sid"]
    labels = {r["sid"]: r["label"] for r in tables.get("info_nodes", [])}

    def rows_for(table):
        return [r for r in tables.get(table, []) if r.get("study_sid") == sid]

    groups = build_groups(rows_for("groups"), labels)
    individuals = build_individuals(rows_for("individuals"), labels)
    interventions = build_interventions(rows_for("interventions"), labels)
    outputs = build_outputs(rows_for("outputs"), labels)
    timecourses = build_timecourses(rows_for("timecourses"), labels)
    scatters = build_scatters(rows_for("scatters"), labels)

    # reference + paper: reuse saved copy when present, else NCBI.
    ref, paper, subs = reference_from_disk(sid)
    paper_md = None
    if ref is None:
        ref, paper, paper_md = reference_from_ncbi(study_row, fetch_paper)
    if not subs:
        try:
            subs = [
                {"sid": x, "name": x, "label": labels.get(x, x)}
                for x in ast.literal_eval(study_row.get("substances") or "[]")
            ]
        except Exception:  # noqa: BLE001
            subs = []

    curators = []
    try:
        curators = [
            CURATORS.get(c, c) for c in ast.literal_eval(study_row.get("curators") or "[]")
        ]
    except Exception:  # noqa: BLE001
        pass

    counts = {
        "groups": len(groups),
        "individuals": len(individuals),
        "interventions": len(interventions),
        "outputs": len(outputs),
        "timecourses": len(timecourses),
        "scatters": len(scatters),
    }
    # Skip studies with no extracted entities in this snapshot (nothing to show).
    if not any(counts.values()):
        return None

    data = {
        "sid": sid,
        "name": s(study_row.get("name")),
        "licence": s(study_row.get("licence")),
        "access": s(study_row.get("access")),
        "date": s(study_row.get("date")),
        "snapshot": SNAPSHOT,
        "counts": counts,
        "reference": ref,
        "curators": curators,
        "descriptions": [],
        "substances": subs or [],
        "groups": groups,
        "individuals": individuals,
        "interventions": interventions,
        "outputs": outputs,
        "timecourses": timecourses,
        "scatters": scatters,
    }
    data["paper"] = paper or {"source": "abstract", "licence": None, "pmcid": None}
    data["_index"] = {
        "sid": sid,
        "name": data["name"],
        "title": ref.get("title"),
        "pmid": ref.get("pmid"),
        "journal": ref.get("journal"),
        "year": (ref.get("date") or "")[:4],
        "substances": [x.get("label") or x.get("name") for x in (subs or [])],
        "n_groups": counts["groups"],
        "n_individuals": counts["individuals"],
        "n_interventions": counts["interventions"],
        "n_outputs": counts["outputs"],
        "n_timecourses": counts["timecourses"],
        "paper_source": data["paper"]["source"],
        "paper_licence": data["paper"]["licence"],
    }

    outdir = DATA_DIR / sid
    outdir.mkdir(parents=True, exist_ok=True)
    if paper_md is not None:
        (outdir / "paper.md").write_text(paper_md)
    elif not (outdir / "paper.md").exists():
        (outdir / "paper.md").write_text(live.abstract_markdown({"reference": ref, "name": data["name"]}))
    (outdir / "study.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return data["_index"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sid", default=None)
    ap.add_argument("--no-paper", action="store_true", help="skip NCBI paper fetch")
    args = ap.parse_args()

    tables = load_zip()
    open_studies = [r for r in tables["studies"] if r.get("licence") == "open"]
    open_studies.sort(key=lambda r: r.get("name") or "")
    if args.sid:
        open_studies = [r for r in open_studies if r["sid"] == args.sid]
    if args.limit:
        open_studies = open_studies[: args.limit]
    print(f"{len(open_studies)} open studies from the {SNAPSHOT} dump", flush=True)

    index = []
    for i, row in enumerate(open_studies, 1):
        print(f"[{i}/{len(open_studies)}] {row['sid']} ({row.get('name')})", flush=True)
        try:
            entry = ingest(tables, row, fetch_paper=not args.no_paper)
            if entry is None:
                print("    - skipped (no entities in snapshot)", flush=True)
                continue
            index.append(entry)
            print(
                f"    groups={entry['n_groups']} indiv={entry['n_individuals']} "
                f"interv={entry['n_interventions']} outputs={entry['n_outputs']} "
                f"tc={entry['n_timecourses']} paper={entry['paper_source']}",
                flush=True,
            )
        except Exception as e:  # noqa: BLE001
            print(f"    ! failed: {e}", file=sys.stderr, flush=True)
        time.sleep(0.2)

    index.sort(key=lambda e: (e.get("name") or ""))
    (DATA_DIR / "index.json").write_text(
        json.dumps(
            {
                "generated": SNAPSHOT,
                "count": len(index),
                "note": (
                    "Open-access PK-DB studies from the curated CSV dump "
                    f"(matthiaskoenig/pkdb_analysis, {SNAPSHOT}). Includes outputs, "
                    "timecourses and scatters — unavailable from the live anonymous API."
                ),
                "studies": index,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"\nDone. index.json has {len(index)} studies.")


if __name__ == "__main__":
    main()
