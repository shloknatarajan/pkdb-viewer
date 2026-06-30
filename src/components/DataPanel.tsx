import { useMemo, useState } from "react";
import { formatValue, label } from "../data";
import type { Characteristica, Output, Study, Timecourse } from "../types";

type Tab =
  | "overview"
  | "groups"
  | "individuals"
  | "interventions"
  | "outputs"
  | "timecourses";

export default function DataPanel({ study }: { study: Study }) {
  const allTabs: { id: Tab; label: string; n: number }[] = [
    { id: "overview", label: "Overview", n: 0 },
    { id: "groups", label: "Groups", n: study.groups.length },
    { id: "individuals", label: "Individuals", n: study.individuals.length },
    {
      id: "interventions",
      label: "Interventions",
      n: study.interventions.length,
    },
    { id: "outputs", label: "Outputs", n: study.outputs?.length ?? 0 },
    {
      id: "timecourses",
      label: "Time-courses",
      n: study.timecourses?.length ?? 0,
    },
  ];
  const tabs = allTabs.filter((t) => t.id === "overview" || t.n > 0);
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="data">
      <div className="tabs">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
            {t.id !== "overview" && <span className="tab-n">{t.n}</span>}
          </button>
        ))}
      </div>

      <div className="data-body">
        {tab === "overview" && <Overview study={study} />}
        {tab === "groups" && <Groups study={study} />}
        {tab === "individuals" && <Individuals study={study} />}
        {tab === "interventions" && <Interventions study={study} />}
        {tab === "outputs" && <Outputs study={study} />}
        {tab === "timecourses" && <Timecourses study={study} />}
      </div>
    </div>
  );
}

function Overview({ study }: { study: Study }) {
  const c = study.counts;
  return (
    <div className="overview">
      <div className="stat-row">
        <Stat n={c.groups} label="groups" />
        <Stat n={c.individuals} label="individuals" />
        <Stat n={c.interventions} label="interventions" />
        <Stat n={c.outputs} label="outputs" />
        <Stat n={c.timecourses} label="time-courses" />
        {(c.scatters ?? 0) > 0 && <Stat n={c.scatters} label="scatters" />}
      </div>

      {study.substances?.length > 0 && (
        <section className="block">
          <h3>Substances</h3>
          <div className="chips">
            {study.substances.map((s) => (
              <span className="chip" key={s.sid}>
                {s.label || s.name}
              </span>
            ))}
          </div>
        </section>
      )}

      {study.descriptions?.length > 0 && (
        <section className="block">
          <h3>Curator notes</h3>
          <ul className="notes">
            {study.descriptions.map((d, i) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
        </section>
      )}

      {study.curators?.length > 0 && (
        <section className="block">
          <h3>Curators</h3>
          <p className="muted">{study.curators.join(", ")}</p>
        </section>
      )}

      <p className="api-note">
        Findings (outputs, time-courses, scatters) are sourced from the curated
        PK-DB CSV dump
        {study.snapshot ? ` (snapshot ${study.snapshot})` : ""} committed to{" "}
        <code>matthiaskoenig/pkdb_analysis</code>, because the live anonymous
        PK-DB API returns these measurements empty.
      </p>
    </div>
  );
}

function Stat({
  n,
  label,
  muted,
}: {
  n?: number | null;
  label: string;
  muted?: boolean;
}) {
  return (
    <div className={`stat ${muted ? "stat-muted" : ""}`}>
      <span className="stat-n">{n ?? 0}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

function CharaTable({ chara }: { chara: Characteristica[] }) {
  if (!chara || chara.length === 0)
    return <p className="muted small">No characteristics recorded.</p>;
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Property</th>
          <th>Value</th>
          <th>n</th>
        </tr>
      </thead>
      <tbody>
        {chara.map((ch) => (
          <tr key={ch.pk}>
            <td>
              {label(ch.measurement_type)}
              {ch.substance && (
                <span className="sub"> · {label(ch.substance)}</span>
              )}
            </td>
            <td className="val">{formatValue(ch)}</td>
            <td className="muted small">{ch.count ?? ""}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Groups({ study }: { study: Study }) {
  if (study.groups.length === 0)
    return <p className="muted">No groups recorded for this study.</p>;
  return (
    <div className="groups">
      {study.groups.map((g) => (
        <div className="group-card" key={g.pk}>
          <div className="group-head">
            <span className="group-name">{g.name}</span>
            {g.count != null && (
              <span className="group-count">n = {g.count}</span>
            )}
            {g.parent && <span className="muted small">⊂ {g.parent.name}</span>}
          </div>
          <CharaTable chara={g.characteristica} />
        </div>
      ))}
    </div>
  );
}

function Interventions({ study }: { study: Study }) {
  if (study.interventions.length === 0)
    return <p className="muted">No interventions recorded.</p>;
  return (
    <table className="data-table wide">
      <thead>
        <tr>
          <th>Name</th>
          <th>Substance</th>
          <th>Dose</th>
          <th>Route</th>
          <th>Form</th>
          <th>Application</th>
          <th>Time</th>
        </tr>
      </thead>
      <tbody>
        {study.interventions.map((iv) => (
          <tr key={iv.pk}>
            <td>{iv.name}</td>
            <td>{label(iv.substance) || "—"}</td>
            <td className="val">{formatValue(iv)}</td>
            <td>{label(iv.route) || "—"}</td>
            <td>{label(iv.form) || "—"}</td>
            <td>{label(iv.application) || "—"}</td>
            <td className="muted small">
              {iv.time != null
                ? `${iv.time}${iv.time_unit ? " " + iv.time_unit : ""}`
                : "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Individuals({ study }: { study: Study }) {
  const indivs = study.individuals;
  // Build columns from the union of measurement types present across individuals.
  const columns = useMemo(() => {
    const seen = new Map<string, string>();
    for (const ind of indivs)
      for (const ch of ind.characteristica || []) {
        const key = ch.measurement_type?.sid;
        if (key && !seen.has(key)) seen.set(key, label(ch.measurement_type));
      }
    // species is constant/uninteresting per-row; keep informative demographics.
    return [...seen.entries()].filter(([sid]) => sid !== "species");
  }, [indivs]);

  if (indivs.length === 0)
    return <p className="muted">No individual-level data for this study.</p>;

  return (
    <div className="indiv-wrap">
      <table className="data-table wide">
        <thead>
          <tr>
            <th>Individual</th>
            <th>Group</th>
            {columns.map(([sid, name]) => (
              <th key={sid}>{name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {indivs.map((ind) => {
            const byType = new Map(
              (ind.characteristica || [])
                .filter((ch) => ch.measurement_type?.sid)
                .map((ch) => [ch.measurement_type!.sid, ch])
            );
            return (
              <tr key={ind.pk}>
                <td>{ind.name}</td>
                <td className="muted small">{ind.group?.name ?? "—"}</td>
                {columns.map(([sid]) => {
                  const ch = byType.get(sid);
                  return (
                    <td key={sid} className="val">
                      {ch ? formatValue(ch) : "—"}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const ROWS_PER_GROUP = 200;

function Outputs({ study }: { study: Study }) {
  const outputs = useMemo(() => study.outputs ?? [], [study.outputs]);
  // Group by measurement type; push raw "concentration" points (which duplicate
  // the time-courses) to the end so the PK parameters lead.
  const groups = useMemo(() => {
    const by = new Map<string, { name: string; rows: Output[] }>();
    for (const o of outputs) {
      const key = o.measurement_type?.sid ?? "—";
      if (!by.has(key))
        by.set(key, { name: label(o.measurement_type) || key, rows: [] });
      by.get(key)!.rows.push(o);
    }
    return [...by.entries()].sort((a, b) => {
      const ac = a[0] === "concentration" ? 1 : 0;
      const bc = b[0] === "concentration" ? 1 : 0;
      if (ac !== bc) return ac - bc;
      return b[1].rows.length - a[1].rows.length;
    });
  }, [outputs]);

  if (outputs.length === 0)
    return <p className="muted">No outputs recorded for this study.</p>;

  return (
    <div className="outputs">
      {groups.map(([sid, g]) => (
        <section className="block" key={sid}>
          <h3>
            {g.name} <span className="tab-n">{g.rows.length}</span>
          </h3>
          <table className="data-table wide">
            <thead>
              <tr>
                <th>Substance</th>
                <th>Tissue</th>
                <th>Value</th>
                <th>Method</th>
                <th>iv</th>
              </tr>
            </thead>
            <tbody>
              {g.rows.slice(0, ROWS_PER_GROUP).map((o) => (
                <tr key={o.pk}>
                  <td>{label(o.substance) || "—"}</td>
                  <td className="muted small">{label(o.tissue) || "—"}</td>
                  <td className="val">{formatValue(o)}</td>
                  <td className="muted small">{label(o.method) || "—"}</td>
                  <td className="muted small">{o.intervention_pk ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {g.rows.length > ROWS_PER_GROUP && (
            <p className="muted small">
              + {g.rows.length - ROWS_PER_GROUP} more rows not shown
            </p>
          )}
        </section>
      ))}
    </div>
  );
}

function Timecourses({ study }: { study: Study }) {
  const curves = study.timecourses ?? [];
  if (curves.length === 0)
    return <p className="muted">No time-courses recorded for this study.</p>;
  return (
    <div className="tc-grid">
      {curves.map((tc) => (
        <TimecourseChart key={tc.pk} tc={tc} />
      ))}
    </div>
  );
}

function TimecourseChart({ tc }: { tc: Timecourse }) {
  const ys = tc.mean && tc.mean.some((v) => v != null) ? tc.mean : tc.values;
  const pts: [number, number][] = [];
  const xs = tc.time || [];
  for (let i = 0; i < xs.length; i++) {
    const x = xs[i];
    const y = ys?.[i];
    if (x != null && y != null) pts.push([x, y]);
  }
  const W = 280;
  const H = 120;
  const P = 4;
  let body;
  if (pts.length < 2) {
    body = <p className="muted small">Not enough points to plot.</p>;
  } else {
    const xmin = Math.min(...pts.map((p) => p[0]));
    const xmax = Math.max(...pts.map((p) => p[0]));
    const ymax = Math.max(...pts.map((p) => p[1]));
    const sx = (x: number) =>
      P + ((x - xmin) / (xmax - xmin || 1)) * (W - 2 * P);
    const sy = (y: number) => H - P - (y / (ymax || 1)) * (H - 2 * P);
    const d = pts
      .map(
        (p, i) =>
          `${i ? "L" : "M"}${sx(p[0]).toFixed(1)},${sy(p[1]).toFixed(1)}`
      )
      .join(" ");
    body = (
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="spark"
        preserveAspectRatio="none"
      >
        <path d={d} fill="none" />
        {pts.map((p, i) => (
          <circle key={i} cx={sx(p[0])} cy={sy(p[1])} r={1.6} />
        ))}
      </svg>
    );
  }
  return (
    <div className="tc-card">
      <div className="tc-head">
        <span className="tc-sub">
          {label(tc.substance) || tc.label || "curve"}
        </span>
        {tc.tissue && <span className="muted small">{label(tc.tissue)}</span>}
      </div>
      {body}
      <div className="tc-foot muted small">
        {label(tc.measurement_type) || "concentration"}
        {tc.unit ? ` · ${tc.unit}` : ""}
        {tc.time_unit ? ` · vs time (${tc.time_unit})` : ""}
        {tc.intervention_pk != null ? ` · iv ${tc.intervention_pk}` : ""}
      </div>
    </div>
  );
}
