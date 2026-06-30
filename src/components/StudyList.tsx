import { useEffect, useMemo, useState } from "react";
import { loadIndex } from "../data";
import type { IndexFile } from "../types";

export default function StudyList() {
  const [idx, setIdx] = useState<IndexFile | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    loadIndex()
      .then(setIdx)
      .catch((e) => setErr(String(e)));
  }, []);

  const studies = useMemo(() => {
    if (!idx) return [];
    const needle = q.trim().toLowerCase();
    if (!needle) return idx.studies;
    return idx.studies.filter((s) =>
      [s.name, s.title, s.journal, s.pmid, ...(s.substances || [])]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(needle)
    );
  }, [idx, q]);

  if (err)
    return (
      <main className="page">
        <div className="error">{err}</div>
        <p className="muted">
          Run the ingestion first: <code>npm run ingest</code>
        </p>
      </main>
    );
  if (!idx)
    return (
      <main className="page">
        <div className="loading">Loading studies…</div>
      </main>
    );

  return (
    <main className="page">
      <div className="list-head">
        <div>
          <h1>Open-access studies</h1>
          <p className="muted">
            {idx.count} open-access PK-DB studies · generated {idx.generated}
          </p>
        </div>
        <input
          className="search"
          placeholder="Search title, drug, journal, PMID…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          autoFocus
        />
      </div>

      <div className="grid">
        {studies.map((s) => (
          <a
            className="card"
            key={s.sid}
            href={`#/study/${encodeURIComponent(s.sid)}`}
          >
            <div className="card-top">
              <span className="card-name">{s.name}</span>
              {s.year && <span className="card-year">{s.year}</span>}
            </div>
            <div className="card-title">{s.title || "(untitled)"}</div>
            {s.journal && <div className="card-journal">{s.journal}</div>}
            {s.substances?.length > 0 && (
              <div className="chips">
                {s.substances.slice(0, 6).map((sub) => (
                  <span className="chip" key={sub}>
                    {sub}
                  </span>
                ))}
              </div>
            )}
            <div className="card-foot">
              <span title="subject groups">{s.n_groups ?? 0} groups</span>
              <span title="individuals">
                {s.n_individuals ?? 0} individuals
              </span>
              <span title="interventions">
                {s.n_interventions ?? 0} interventions
              </span>
              <span
                className={`src src-${s.paper_source}`}
                title={`Paper text source: ${s.paper_source}`}
              >
                {s.paper_source === "abstract" ? "abstract only" : "full text"}
              </span>
            </div>
          </a>
        ))}
        {studies.length === 0 && (
          <p className="muted">No studies match “{q}”.</p>
        )}
      </div>
    </main>
  );
}
