# PK-DB Viewer — Design Document

## Context

This document codifies a design language for **PK-DB Viewer** derived from the design
principles in GXL's ["Bringing the regulatory and clinical landscape to Paperclip"](https://gxl.ai/blog/adding-regulatory-clinical)
post. That post is a piece of scientific/evidence communication, and the way it presents
information is a design system in itself: **verifiable claims, side-by-side comparison,
and quantified deltas, expressed in restrained editorial typography.**

PK-DB Viewer has the same job as that blog post, in miniature. It puts an **original paper
on the left and PK-DB's extracted data on the right** and asks the reader to trust the
extraction. That is exactly the blog's "with vs. without, quoted verbatim, cited to a line
number" pattern. This document translates the blog's principles into concrete rules for our
codebase so the viewer *reads as evidence*, not just as a data dump.

The goal is not to repaint the app in the blog's palette. PK-DB Viewer already has a
deliberate warm, paper-like, teal-accented identity (`src/styles.css` `:root`). We keep that
identity and adopt the blog's **information-design principles** and **component patterns** on
top of it.

---

## Part 1 — Design principles (from the blog)

Six principles run through the post. They are ordered by how central they are to what PK-DB
Viewer does.

### P1. Every claim is verifiable at its source

The blog's defining move: the agent "quotes directly from the Drugs@FDA documents … providing
a line number to verify the quote exactly matches the FDA document." Evidence is never
paraphrased away from its origin — the reader can always click through to the primary text.

> **In this app:** the paper pane *is* the primary source. Every extracted value on the right
> should feel one glance away from the sentence it came from on the left. Preserve provenance
> aggressively: PubMed/PMC/DOI/PK-DB links, curator notes, and the "abstract-only vs. full
> text" distinction are first-class, not footnotes.

### P2. Comparison is the unit of insight

Nearly every result in the post is a two-column comparison: *with Paperclip* vs. *without*,
same question, same model. The layout (`.side-by-side`, `.btk-cmp-card`, `.cmp-table`) makes
the delta impossible to miss — the winning cell is green, the losing cell is red.

> **In this app:** the paper|data split pane is our core comparison. Treat the two panes as
> peers of equal weight. Any place we show "what the paper said" against "what was extracted"
> is a comparison and should use a shared two-column idiom.

### P3. Lead with the quantified takeaway

Each section opens with a **TL;DR** and a row of **stat cards** ("86%", "2.1×", "47%",
"$0.45") before any prose. The reader gets the magnitude first, the argument second.

> **In this app:** the Overview tab's stat tiles are this principle. Each study should lead
> with its countable facts — n groups, n individuals, n interventions, n timecourses — as
> big, tabular-numeral figures before the detailed tables.

### P4. Structure dense data into scannable tables

The regulatory landscape is overwhelming, so the post never presents it as prose. It uses
compact tables with dark headers, zebra striping, a heavy bottom rule, and semantic
`✓`/`✗` cells (the assay-compatibility matrix, the "What Each System Could Answer" table).

> **In this app:** Groups, Individuals, Interventions, and Outputs are all tables. They should
> share one table style — dark header, zebra rows, tabular numerals, a clear terminal rule —
> so the whole data pane reads as one instrument.

### P5. Restraint is the aesthetic

The visual system is almost entirely **neutral** (`#111827` ink, `#6b7280` muted, `#e5e7eb`
borders, `#f9fafb` cards) with color reserved for **meaning**: green = better, red = worse,
blue = a verbatim quote. Type is a clean sans (Inter) with a mono (JetBrains Mono) for
anything the reader might copy or verify. Nothing is decorative.

> **In this app:** color carries meaning, never mood. Our teal `--accent` marks
> interaction/emphasis; a green/amber/red semantic set marks better/caution/worse and
> full-text/abstract-only status. Mono is for values, IDs, units, and code — things the user
> verifies or copies.

### P6. Name the source and the shape of every dataset

The post never shows a number without saying where it came from and how big it is:
"580K ClinicalTrials.gov", "`ls /fda/` → 225,411 documents", "n=12", "medians". Provenance
and sample size travel *with* the data.

> **In this app:** every count states its unit; every study states its source badge and
> curation status; every value that is estimated, abstract-only, or missing says so rather
> than rendering as a bare or blank number.

---

## Part 2 — Visual language

### Typography

PK-DB Viewer keeps its existing three-font system, mapped to the blog's roles:

| Role | Font token | Used for | Blog parallel |
|---|---|---|---|
| Reading | `--serif` | paper markdown, study & card titles | (paper = primary source) |
| Interface | `--sans` | all UI chrome, labels, tables | Inter |
| Verify/copy | `--mono` | values, units, IDs, tags, code | JetBrains Mono |

Type conventions carried over from the blog:

- **Section labels** are small, uppercase, letter-spaced (`.06em`), muted — e.g. tab labels,
  card headers, the "TL;DR"/overview labels. (Blog: `.col-label`, `.tldr-label`, `.q-label`.)
- **Numbers use tabular figures** (`font-variant-numeric: tabular-nums`) everywhere they sit
  in a column or a stat tile, so digits align. (Blog: `.pcfig-bar-value`, `.stat-card .num`.)
- **A readable measure.** Body/reading text targets ~`1.6` line-height and a bounded content
  width (the blog caps at `--bio-content-max: 960px`).

### Color

Keep the project palette as the identity layer. Add a **semantic layer** for the blog's
"color = meaning" principle. Suggested tokens (extend `:root` in `src/styles.css`):

| Meaning | Token (existing → add) | Value | Where it appears |
|---|---|---|---|
| Interaction / emphasis | `--accent` *(exists)* | `#0f6e72` | links, active tab, focus ring, chips |
| Emphasis text | `--accent-ink` *(exists)* | `#0a4f52` | headings, emphasized values |
| Positive / present / full-text | `--good` *(add)* | `#166534` on `#dcfce7` | ✓ cells, "full text" badge, verdicts |
| Caution / abstract-only / estimated | `--warn` *(exists)* | `#9a6b2f` | abstract-only notes, api-note box |
| Negative / absent / missing | `--bad` *(add)* | `#991b1b` on `#fee2e2` | ✗ cells, missing-data, errors |
| Verbatim / linked source | `--quote` *(add)* | `#1d4ed8` | source links, "as reported in the paper" spans |

Rules:

1. **Neutral by default.** Ink, muted, and line tokens do the vast majority of the work. A
   screen with no green/red/amber on it is correct, not unfinished.
2. **Color states a fact.** Green means *present/better/full-text*; red means *absent/worse*;
   amber means *caution/incomplete*; blue means *this is a source you can open*. Never use
   these hues decoratively.
3. **Pair hue with a non-color cue** (icon `✓`/`✗`, a word, a border) so meaning survives for
   colorblind readers and in the paper pane's print-like context.

### Surfaces, borders, spacing

Match the blog's calm, card-based rhythm to the project's existing tokens:

- **Cards/panels:** `--panel`/`--paper` fill, `1px solid --line` border, `7–12px` radius,
  the existing `--shadow`. (Blog `.stat-card`, `.tldr`, `.btk-cmp-card` are the same recipe:
  offset background + hairline border + `8px` radius.)
- **Dividers:** a hairline (`--line-soft`) between related blocks; a heavier rule between major
  sections. (Blog `.section-divider` vs `.major-divider` — 1px vs 3px.)
- **Terminal/code:** dark surface (`#1a1a2e`/`#1e293b`), `10px` radius, horizontally
  scrollable, mono. Reserve this treatment for genuinely code/filesystem-like content.

---

## Part 3 — Component patterns

Each pattern below states the principle it serves and how it maps to our existing components
(`src/components/DataPanel.tsx`, `StudyView.tsx`, `StudyList.tsx`).

### Split comparison pane — *serves P1, P2*

The paper|data split (`StudyView.tsx` `.split`) is the app's `.side-by-side`. Treat the two
panes as equal-weight peers. The divider is functional and draggable; neither side is
"secondary." This is where verifiability lives — the reader checks the right against the left.

### Stat tiles — *serves P3*

The Overview stat cards (`DataPanel.tsx` `.stat`) are the blog's `.stat-card` / `.stat-row`.
Lead each study and each data tab with its counts as large tabular numerals + a small muted
label. Prefer a `repeat(auto-fit)` / 2–4 column row that collapses gracefully on the
`880px` breakpoint (the blog collapses `4 → 2 → 1`).

### Data tables — *serves P4, P6*

Groups / Individuals / Interventions / Outputs should share one table component/style:

- dark header row (ink background, light text), muted uppercase column labels;
- zebra striping on alternating rows; a heavier rule on the last row to "close" the table;
- **tabular-nums** on every numeric column; **mono** for IDs, units, and raw values;
- semantic cells for presence/absence and status (green ✓ / red ✗ / amber caution), never a
  blank cell where "not reported" is the actual finding — say so.

### Provenance & status badges — *serves P1, P6*

Source links (PubMed/PMC/DOI/PK-DB) and the **full-text vs. abstract-only** badge are
first-class. Model badges on the blog's semantic chips: green "full text", amber
"abstract-only", neutral for source name. Curator notes and the api-note box carry the same
"here's the caveat" role as the blog's parenthetical "(NOT the specific results)" honesty.

### Sparklines / figures — *serves P3, P4*

Timecourse sparklines (`TimecourseChart`, inline SVG) are our `.pcfig-bar` figures: small,
labeled, tabular values, one accent color against neutral. Keep them minimal — axis-light,
value-labeled, readable at card size — matching the blog's compact bar figures.

### TL;DR / summary block — *serves P3* (new, optional)

The blog opens sections with a `.tldr` block: an offset card, an uppercase "TL;DR" label, one
tight paragraph of the takeaway. A study-level summary block (curator abstract or key findings)
at the top of the data pane would bring PK-DB Viewer fully in line with "lead with the
takeaway."

---

## Part 4 — Applying this to the codebase

- **Single source of truth stays in `src/styles.css` `:root`.** Add the semantic tokens
  (`--good`, `--bad`, `--quote`, and light-tint companions) alongside the existing palette;
  do not scatter hex values through components. (Today several semantic colors are hardcoded
  inline in `styles.css` — e.g. error `#a23b2d`, api-note `#fbf6ec`/`#ecdfc6`. Fold these into
  named tokens.)
- **One table style, one card style, one chip style.** Reuse across all `DataPanel` tabs so
  the data pane reads as one instrument (P4).
- **Every number gets a unit and, where relevant, an `n`.** Extend `formatValue()`/`label()`
  in `src/data.ts` so estimated/abstract-only/missing values render explicitly rather than
  blank (P6).
- **Color only when it means something.** Audit existing uses of teal/amber to confirm each
  states interaction or status, not decoration (P5).

## Verification

This is a documentation change; verify by review and by checking token references resolve:

1. **Read-through:** confirm each principle (P1–P6) names a real component or token in
   `src/styles.css` / `src/components/`. Paths and token names above should match the code.
2. **When implementing token additions:** after editing `:root`, run `npm run dev` and confirm
   the app renders unchanged (new tokens are additive until adopted), then adopt them in one
   component (e.g. the Outputs table's ✓/✗ cells) and visually diff against a study with
   missing/estimated values.
3. **Contrast check:** verify `--good`/`--bad`/`--warn` text-on-tint pairs meet WCAG AA, and
   that every semantic hue is paired with a non-color cue (icon or word) per P5/P-color rule 3.
