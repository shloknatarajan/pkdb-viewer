import { useMemo, useState } from "react";
import { formatValue, label } from "../data";
import type { Characteristica, Study } from "../types";

type Tab = "overview" | "groups" | "individuals" | "interventions";

export default function DataPanel({ study }: { study: Study }) {
  const tabs: { id: Tab; label: string; n: number }[] = [
    { id: "overview", label: "Overview", n: 0 },
    { id: "groups", label: "Groups", n: study.groups.length },
    { id: "individuals", label: "Individuals", n: study.individuals.length },
    { id: "interventions", label: "Interventions", n: study.interventions.length },
  ];
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
        <Stat n={c.outputs} label="outputs" muted />
        <Stat n={c.timecourses} label="time-courses" muted />
      </div>

      {study.substances?.length > 0 && (
        <section className="block">
          <h3>Substances</h3>
          <div className="chips">
            {study.substances.map((s) => (
              <span className="chip" key={s.sid}>{s.label || s.name}</span>
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
        Outputs (PK parameters such as AUC, clearance, half-life) and time-courses
        are not served by the anonymous PK-DB API and are therefore not shown here.
      </p>
    </div>
  );
}

function Stat({ n, label, muted }: { n?: number | null; label: string; muted?: boolean }) {
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
              {ch.substance && <span className="sub"> · {label(ch.substance)}</span>}
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
            {g.count != null && <span className="group-count">n = {g.count}</span>}
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
              {iv.time != null ? `${iv.time}${iv.time_unit ? " " + iv.time_unit : ""}` : "—"}
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
                .map((ch) => [ch.measurement_type!.sid, ch]),
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
