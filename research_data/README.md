# Research data

This directory contains offline datasets used for ingestion, analysis, and
research. It is not served by Vite and is not included in production builds.

- `raw_data/` contains the complete study-partitioned PK-DB snapshot, including
  records that are not displayed by the web application.

Treat these files as generated assets. Rebuild the raw snapshot with
`ingest/ingest_raw_dump.py` rather than editing it by hand when possible.
