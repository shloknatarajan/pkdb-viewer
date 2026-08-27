# Application data

This directory contains static data required by the web application. Vite uses
`app_data/` as its public directory, so everything here is copied into the
production build and served from the site root.

- `pkdb_annotations/` contains the curated PK-DB study index, study JSON, and
  paper Markdown used by the viewer.
- `proposed_annotations/` contains proposed annotation JSON displayed alongside
  existing PK-DB annotations.

Treat these files as generated assets. Rebuild PK-DB annotations with the
scripts in `ingest/` rather than editing study snapshots by hand when possible.
