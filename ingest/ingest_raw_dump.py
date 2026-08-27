#!/usr/bin/env python3
"""Build a lossless, study-partitioned JSON dump of the PK-DB snapshot.

Unlike ``ingest_dump.py``, this script does not filter by licence, discard
non-normalized rows, reshape records for the viewer, or fetch paper Markdown.
Every row in the source CSV tables is written to the corresponding study JSON.

Output:
  research_data/raw_data/index.json
  research_data/raw_data/info_nodes.json
  research_data/raw_data/pkdb/PKDBxxxxx/study.json
  research_data/raw_data/pmid/<numeric PMID>/study.json
  research_data/raw_data/legacy/<source study sid>/study.json

Reference identifiers are enriched, when available, from the repository's
saved live-API capture, PMID-to-PMCID mapping, and existing viewer data. No
missing identifier or bibliographic value is inferred.
"""
from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import math
import re
import shutil
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "research_data" / "raw_data"
CACHE = Path(__file__).resolve().parent / ".cache_testdata_concise_false.zip"
ZIP_URL = (
    "https://raw.githubusercontent.com/matthiaskoenig/pkdb_analysis/"
    "develop/tests/data/testdata_concise_false.zip"
)
SNAPSHOT = "2021-12-03"
SOURCE_REPOSITORY = "matthiaskoenig/pkdb_analysis"
SOURCE_PATH = "tests/data/testdata_concise_false.zip"
TABLES = (
    "groups",
    "individuals",
    "interventions",
    "outputs",
    "timecourses",
    "scatters",
)
BOOLEAN_COLUMNS = {"normed", "calculated"}
NUMERIC_COLUMNS = {
    "count",
    "value",
    "mean",
    "median",
    "min",
    "max",
    "sd",
    "se",
    "cv",
    "time",
    "time_end",
}
SAFE_SID = re.compile(r"^[A-Za-z0-9_.-]+$")


def read_zip(path: Path | None) -> bytes:
    if path:
        return path.read_bytes()
    if CACHE.exists() and CACHE.stat().st_size > 1_000_000:
        return CACHE.read_bytes()
    print(f"Downloading {ZIP_URL}", flush=True)
    request = urllib.request.Request(
        ZIP_URL,
        headers={"User-Agent": "pkdb-viewer-raw-dump/1.0"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    CACHE.write_bytes(data)
    return data


def load_archive(blob: bytes) -> tuple[dict[str, list[dict[str, str]]], dict[str, str]]:
    tables: dict[str, list[dict[str, str]]] = {}
    documents: dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        for name in archive.namelist():
            if name.endswith(".csv"):
                with archive.open(name) as handle:
                    text = io.TextIOWrapper(handle, encoding="utf-8-sig")
                    tables[Path(name).stem] = list(csv.DictReader(text))
            elif Path(name).name in {"README.md", "TERMS_OF_USE.md"}:
                documents[Path(name).name] = archive.read(name).decode("utf-8")
    return tables, documents


def parse_array(value: str) -> list[Any] | None:
    try:
        parsed = eval(  # noqa: S307 - globals and builtins are explicitly disabled
            value,
            {"__builtins__": {}},
            {"nan": math.nan},
        )
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(parsed, (list, tuple)):
        return None
    return [
        None if isinstance(item, float) and math.isnan(item) else item
        for item in parsed
    ]


def coerce_value(column: str, value: str | None) -> Any:
    """Convert explicit CSV types while preserving identifiers as strings."""
    if value is None:
        return None
    value = value.strip()
    if not value or value.lower() == "nan":
        return None
    if value.startswith("[") and value.endswith("]"):
        parsed = parse_array(value)
        if parsed is not None:
            return parsed
    if column in BOOLEAN_COLUMNS:
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
    if column.endswith("_pk") or column in NUMERIC_COLUMNS:
        try:
            number = float(value)
        except ValueError:
            return value
        if math.isnan(number):
            return None
        return int(number) if number.is_integer() else number
    return value


def coerce_row(row: dict[str | None, str]) -> dict[str, Any]:
    # Pandas wrote its dataframe index as an unnamed first CSV column.
    return {
        column: coerce_value(column, value)
        for column, value in row.items()
        if column
    }


def parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def format_authors(authors: Any) -> list[str]:
    formatted = []
    for author in authors or []:
        if isinstance(author, str):
            name = author.strip()
        elif isinstance(author, dict):
            name = " ".join(
                str(author.get(key) or "").strip()
                for key in ("first_name", "last_name")
            ).strip()
            name = name or str(author.get("name") or "").strip()
        else:
            name = ""
        if name:
            formatted.append(name)
    return formatted


def first(*values: Any) -> Any:
    return next((value for value in values if value not in (None, "", [])), None)


def identifier_namespace(sid: str, pmid: str | None) -> str:
    if re.fullmatch(r"PKDB[0-9]+", sid):
        return "pkdb"
    if sid.isdigit() and sid == pmid:
        return "pmid"
    return "legacy"


def normalized_text(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def canonical_pkdb_sid(
    study: dict[str, str],
    live_studies: list[dict[str, Any]],
) -> str | None:
    sid = study["sid"]
    if re.fullmatch(r"PKDB[0-9]+", sid):
        return sid

    pmid = study.get("reference_pmid") or None
    name = normalized_text(study.get("name"))
    title = normalized_text(study.get("reference_title"))
    candidates = set()
    for live in live_studies:
        live_sid = str(live.get("sid") or "")
        if not re.fullmatch(r"PKDB[0-9]+", live_sid):
            continue
        live_ref = live.get("reference") or {}
        same_reference = bool(pmid) and str(live_ref.get("pmid") or "") == pmid
        same_name_and_title = (
            bool(name)
            and bool(title)
            and normalized_text(live.get("name")) == name
            and normalized_text(live_ref.get("title")) == title
        )
        if same_reference or same_name_and_title:
            candidates.add(live_sid)
    return next(iter(candidates)) if len(candidates) == 1 else None


def reference_metadata(
    study: dict[str, str],
    pmcid_by_pmid: dict[str, str],
    live_by_sid: dict[str, dict[str, Any]],
    live_by_name: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    sid = study["sid"]
    name = study.get("name") or ""
    viewer = load_json(
        ROOT / "app_data" / "pkdb_annotations" / sid / "study.json", {}
    )
    viewer_ref = viewer.get("reference") or {}
    live = live_by_sid.get(sid) or live_by_name.get(name) or {}
    live_ref = live.get("reference") or {}

    pmid = first(study.get("reference_pmid"), viewer_ref.get("pmid"), live_ref.get("pmid"))
    pmid = str(pmid) if pmid is not None else None
    pmcid = first(
        pmcid_by_pmid.get(pmid or ""),
        (viewer.get("paper") or {}).get("pmcid"),
    )
    doi = first(viewer_ref.get("doi"), live_ref.get("doi"))

    reference = {
        "title": first(
            study.get("reference_title"),
            viewer_ref.get("title"),
            live_ref.get("title"),
        ),
        "date": first(
            study.get("reference_date"),
            viewer_ref.get("date"),
            live_ref.get("date"),
        ),
        "journal": first(viewer_ref.get("journal"), live_ref.get("journal")),
        "authors": format_authors(first(viewer_ref.get("authors"), live_ref.get("authors"))),
        "abstract": first(viewer_ref.get("abstract"), live_ref.get("abstract")),
    }
    identifiers = {
        "source_study_sid": sid,
        "pmid": pmid,
        "pmcid": pmcid,
        "doi": doi,
    }
    return identifiers, reference


def unique_count(rows: list[dict[str, Any]], key: str) -> int:
    return len({row[key] for row in rows if row.get(key) is not None})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--zip",
        type=Path,
        help="use a local testdata_concise_false.zip instead of downloading",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sid", help="generate a single study")
    args = parser.parse_args()

    tables, source_documents = load_archive(read_zip(args.zip))
    studies = tables["studies"]
    if args.sid:
        studies = [study for study in studies if study["sid"] == args.sid]
    if args.limit:
        studies = studies[: args.limit]

    pmcid_rows = load_json(ROOT / "pkdb-api" / "studies_pmids.json", [])
    pmcid_by_pmid = {
        str(row["pmid"]): str(row["pmcid"])
        for row in pmcid_rows
        if row.get("pmid") and row.get("pmcid")
    }
    # The CSV is authoritative when present and includes records resolved after
    # the JSON study list was generated.
    pmcid_csv = ROOT / "pkdb-api" / "pmid_to_pmcid.csv"
    if pmcid_csv.exists():
        with pmcid_csv.open(encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if row.get("pmid") and row.get("pmcid"):
                    pmcid_by_pmid[row["pmid"]] = row["pmcid"]

    live_studies = load_json(ROOT / "pkdb-api" / "studies_full.json", [])
    live_by_sid = {str(study.get("sid")): study for study in live_studies}
    live_by_name = {str(study.get("name")): study for study in live_studies}

    rows_by_study: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for table_name in TABLES:
        grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        for raw_row in tables.get(table_name, []):
            row = coerce_row(raw_row)
            study_sid = row.pop("study_sid", None)
            if study_sid:
                grouped[str(study_sid)].append(row)
        for sid, rows in grouped.items():
            rows_by_study.setdefault(sid, {})[table_name] = rows

    full_build = not args.sid and not args.limit
    build_dir = RAW_DIR.with_name(".raw_data_build") if full_build else RAW_DIR
    if full_build and build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for number, study in enumerate(studies, 1):
        sid = study["sid"]
        if not SAFE_SID.fullmatch(sid):
            raise ValueError(f"Unsafe study sid: {sid!r}")
        study_rows = rows_by_study.get(sid, {})
        data_tables = {name: study_rows.get(name, []) for name in TABLES}
        identifiers, reference = reference_metadata(
            study,
            pmcid_by_pmid,
            live_by_sid,
            live_by_name,
        )
        identifiers["pkdb_sid"] = canonical_pkdb_sid(study, live_studies)
        namespace = identifier_namespace(sid, identifiers["pmid"])
        relative_path = f"{namespace}/{sid}/study.json"
        counts = {name: len(rows) for name, rows in data_tables.items()}
        entity_counts = {
            "groups": unique_count(data_tables["groups"], "group_pk"),
            "individuals": unique_count(data_tables["individuals"], "individual_pk"),
            "interventions": unique_count(data_tables["interventions"], "intervention_pk"),
            "outputs": unique_count(data_tables["outputs"], "output_pk"),
            "timecourses": unique_count(data_tables["timecourses"], "subset_pk"),
            "scatters": unique_count(data_tables["scatters"], "subset_pk"),
        }
        record = {
            "schema_version": 1,
            "snapshot": SNAPSHOT,
            "source": {
                "repository": SOURCE_REPOSITORY,
                "path": SOURCE_PATH,
                "url": ZIP_URL,
            },
            "sid": sid,
            "namespace": namespace,
            "name": study.get("name") or None,
            "licence": study.get("licence") or None,
            "access": study.get("access") or None,
            "date": study.get("date") or None,
            "creator": study.get("creator") or None,
            "curators": parse_list(study.get("curators")),
            "substances": parse_list(study.get("substances")),
            "identifiers": identifiers,
            "reference": reference,
            "row_counts": counts,
            "entity_counts": entity_counts,
            **data_tables,
        }
        output_dir = build_dir / namespace / sid
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "study.json").write_text(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        )
        index.append(
            {
                "sid": sid,
                "namespace": namespace,
                "path": relative_path,
                "name": record["name"],
                "licence": record["licence"],
                "date": record["date"],
                "title": reference["title"],
                **identifiers,
                "row_counts": counts,
                "entity_counts": entity_counts,
            }
        )
        print(f"[{number}/{len(studies)}] {sid}: {counts['outputs']} output rows")

    index.sort(key=lambda entry: (entry.get("name") or "", entry["sid"]))
    (build_dir / "index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "snapshot": SNAPSHOT,
                "source": {
                    "repository": SOURCE_REPOSITORY,
                    "path": SOURCE_PATH,
                    "url": ZIP_URL,
                },
                "count": len(index),
                "studies": index,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    info_nodes = [coerce_row(row) for row in tables.get("info_nodes", [])]
    (build_dir / "info_nodes.json").write_text(
        json.dumps(info_nodes, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    for filename, content in source_documents.items():
        (build_dir / f"SOURCE_{filename}").write_text(content)
    if full_build:
        if RAW_DIR.exists():
            shutil.rmtree(RAW_DIR)
        build_dir.replace(RAW_DIR)
    print(f"Done: wrote {len(index)} studies to {RAW_DIR}")


if __name__ == "__main__":
    main()
