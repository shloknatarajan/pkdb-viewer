#!/usr/bin/env python3
"""Export PK-DB annotations for papers with full text in Paperclip."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW_DATA = ROOT / "research_data" / "raw_data"
COVERAGE = RAW_DATA / "paperclip_coverage.csv"
OUTPUT = ROOT / "paperclip_full_text_annotations"
INDEX = OUTPUT / "index.csv"

INDEX_FIELDS = [
    "pmcid",
    "pmid",
    "raw_sid",
    "pkdb_sid",
    "study_name",
    "title",
    "raw_data_path",
    "paperclip_document_path",
    "annotation_path",
]


def main() -> None:
    with COVERAGE.open(newline="", encoding="utf-8") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["paperclip_text_availability"] == "full_text"
        ]

    OUTPUT.mkdir(exist_ok=True)
    index_rows: list[dict[str, str]] = []
    for row in sorted(rows, key=lambda item: item["pmcid"]):
        pmcid = row["pmcid"]
        if not pmcid:
            raise ValueError(f"full-text row has no PMCID: {row['raw_sid']}")

        source = RAW_DATA / row["raw_data_path"]
        if not source.is_file():
            raise FileNotFoundError(source)

        destination_dir = OUTPUT / pmcid
        destination_dir.mkdir(exist_ok=True)
        destination = destination_dir / "annotation.json"
        shutil.copyfile(source, destination)

        index_rows.append(
            {
                "pmcid": pmcid,
                "pmid": row["pmid"],
                "raw_sid": row["raw_sid"],
                "pkdb_sid": row["pkdb_sid"],
                "study_name": row["study_name"],
                "title": row["title"],
                "raw_data_path": row["raw_data_path"],
                "paperclip_document_path": row["paperclip_document_path"],
                "annotation_path": f"{pmcid}/annotation.json",
            }
        )

    with INDEX.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(index_rows)

    print(f"Exported {len(index_rows)} annotations to {OUTPUT}")


if __name__ == "__main__":
    main()
