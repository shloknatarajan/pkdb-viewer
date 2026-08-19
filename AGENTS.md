# Repository Guidelines

## Project Structure & Module Organization

This repository combines a static PK-DB viewer with data-ingestion and paper-screening tools.

- `src/` contains the React/TypeScript application. Put reusable UI in `src/components/`, shared interfaces in `src/types.ts`, and data-loading helpers in `src/data.ts`.
- `public/` holds generated study JSON and paper Markdown consumed by the viewer. Treat these as generated assets; update them through an ingestion script when possible.
- `ingest/` contains the current and legacy Python ingestion pipelines.
- `paper_screening/` is a stdlib-based CLI for finding and ranking candidate papers.
- `scope_estimation/`, `pkdb-api/`, and `variantAnnotations/` contain research scripts, snapshots, and source datasets. The latter includes hundreds of downloaded papers.
- `docs/` records design decisions and scope-estimation methodology.

## PK-DB Domain Context

[PK-DB](https://pk-db.com/) is an open database of clinical and preclinical pharmacokinetics data, structured for reuse and computational modeling. A study represents one publication or trial. Subjects are modeled as groups and/or individuals with characteristics such as species, sex, age, body weight, and health status. Interventions describe substances, doses, routes, forms, timing, or other experimental changes. Results include scalar outputs (for example AUC, clearance, Cmax, or half-life), concentration timecourses, and scatter correlations.

Preserve this structure when changing ingestion or UI code: retain units, substances, subject and intervention links, source identifiers, curator notes, and the distinction between reported and missing data. Do not infer values absent from the source. This viewer uses a static, curated snapshot rather than treating the live API as authoritative at runtime; see `README.md` for dataset provenance and known API limitations.

## Build and Development Commands

- `npm install` installs frontend dependencies.
- `npm run dev` starts the Vite development server at `http://localhost:5173`.
- `npm run build` runs strict TypeScript checks and creates the static `dist/` build.
- `npm run preview` serves the production build locally.
- `npm run lint` checks TypeScript and React code with ESLint.
- `npm run format:check` verifies Prettier formatting; `npm run format` rewrites files.
- `npm run ingest` rebuilds data with the configured Python virtual environment. See `README.md` for targeted ingestion and paper-screening commands.

## Coding Style & Naming Conventions

Use strict TypeScript and functional React components. Prettier enforces 80-column lines, semicolons, double quotes, and ES5 trailing commas. Use two-space indentation in TS/TSX and JSON. Name components and interfaces in `PascalCase`, functions and variables in `camelCase`, and Python modules/functions in `snake_case`. Keep domain types centralized and avoid duplicating formatting or fetch logic in components.
