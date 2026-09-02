# Paperclip full-text annotations

This folder contains the PK-DB annotations for the papers classified as
`full_text` in
[`research_data/raw_data/paperclip_coverage.csv`](../research_data/raw_data/paperclip_coverage.csv).

Each PMCID directory contains an `annotation.json` copied byte-for-byte from
the canonical PK-DB snapshot under `research_data/raw_data/`. `index.csv` maps
the exported file back to its raw-data record and Paperclip document path.

Regenerate the collection with:

```bash
python3 ingest/export_paperclip_annotations.py
```
