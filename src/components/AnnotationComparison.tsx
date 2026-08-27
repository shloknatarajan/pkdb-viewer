import { useMemo, useState } from "react";
import { formatValue, label } from "../data";
import type { ProposedAnnotation, ProposedSummary, Study } from "../types";

type Section = "overview" | "subjects" | "interventions" | "outputs" | "issues";

const sections: { id: Section; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "subjects", label: "Subjects" },
  { id: "interventions", label: "Interventions" },
  { id: "outputs", label: "Outputs" },
  { id: "issues", label: "Review notes" },
];

function formatSummary(summary: ProposedSummary): string {
  if (summary.as_reported) return summary.as_reported;
  const central =
    summary.value ?? summary.mean ?? summary.geometric_mean ?? summary.median;
  if (central == null) return "—";
  return `${central}${summary.unit ? ` ${summary.unit}` : ""}`;
}

function substanceName(proposal: ProposedAnnotation, id?: string | null) {
  return (
    proposal.substances.find((substance) => substance.local_id === id)
      ?.reported_name ?? "—"
  );
}

function ComparisonHeader({
  kind,
  title,
  detail,
}: {
  kind: "curated" | "proposed";
  title: string;
  detail: string;
}) {
  return (
    <div className={`comparison-source comparison-source-${kind}`}>
      <span className="comparison-source-kind">
        {kind === "curated" ? "Curated snapshot" : "Proposed evidence pass"}
      </span>
      <strong>{title}</strong>
      <span>{detail}</span>
    </div>
  );
}

function CountStrip({ values }: { values: [string, number][] }) {
  return (
    <div className="comparison-counts">
      {values.map(([name, value]) => (
        <div key={name}>
          <strong>{value}</strong>
          <span>{name}</span>
        </div>
      ))}
    </div>
  );
}

function CuratedOverview({ study }: { study: Study }) {
  return (
    <>
      <CountStrip
        values={[
          ["groups", study.groups.length],
          ["people", study.individuals.length],
          ["interventions", study.interventions.length],
          ["outputs", study.outputs?.length ?? 0],
        ]}
      />
      <section className="comparison-block">
        <h3>Substances</h3>
        <div className="chips">
          {study.substances.map((substance) => (
            <span className="chip" key={substance.sid}>
              {label(substance)}
            </span>
          ))}
        </div>
      </section>
      <section className="comparison-block">
        <h3>Record</h3>
        <dl className="comparison-facts">
          <div>
            <dt>Study ID</dt>
            <dd>{study.sid}</dd>
          </div>
          <div>
            <dt>Snapshot</dt>
            <dd>{study.snapshot ?? "—"}</dd>
          </div>
          <div>
            <dt>Curators</dt>
            <dd>{study.curators.join(", ") || "—"}</dd>
          </div>
        </dl>
      </section>
    </>
  );
}

function ProposedOverview({ proposal }: { proposal: ProposedAnnotation }) {
  return (
    <>
      <CountStrip
        values={[
          ["groups", proposal.groups.length],
          ["people", proposal.individuals.length],
          ["interventions", proposal.interventions.length],
          ["outputs", proposal.outputs.length],
        ]}
      />
      <section className="comparison-block">
        <h3>Substances</h3>
        <div className="chips chips-proposed">
          {proposal.substances.map((substance) => (
            <span className="chip" key={substance.local_id}>
              {substance.reported_name}
            </span>
          ))}
        </div>
      </section>
      <section className="comparison-block">
        <h3>Study design</h3>
        <p>{proposal.study_design || "—"}</p>
      </section>
    </>
  );
}

function CuratedSubjects({ study }: { study: Study }) {
  return (
    <>
      {study.groups.map((group) => (
        <section className="comparison-block" key={group.pk}>
          <h3>
            {group.name} {group.count != null && <span>n = {group.count}</span>}
          </h3>
          <table className="comparison-table">
            <tbody>
              {group.characteristica.map((item) => (
                <tr key={item.pk}>
                  <th>{label(item.measurement_type)}</th>
                  <td>{formatValue(item)}</td>
                  <td>{item.count ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
      <p className="comparison-footnote">
        {study.individuals.length} individual records with linked measurements.
      </p>
    </>
  );
}

function ProposedSubjects({ proposal }: { proposal: ProposedAnnotation }) {
  return (
    <>
      {proposal.groups.map((group) => (
        <section className="comparison-block" key={group.local_id}>
          <h3>
            {group.name} {group.count != null && <span>n = {group.count}</span>}
          </h3>
          <table className="comparison-table">
            <tbody>
              {group.characteristics.map((item) => (
                <tr key={item.local_id}>
                  <th>{item.name}</th>
                  <td>{item.choice || formatSummary(item.summary)}</td>
                  <td>{item.count ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
      <p className="comparison-footnote">
        No individual records; the supplied text does not identify patient-level
        values.
      </p>
    </>
  );
}

function CuratedInterventions({ study }: { study: Study }) {
  return (
    <div className="comparison-cards">
      {study.interventions.map((intervention) => (
        <article key={intervention.pk}>
          <h3>{intervention.name}</h3>
          <strong>{label(intervention.substance) || "—"}</strong>
          <p>{formatValue(intervention)}</p>
          <span>
            {[label(intervention.route), label(intervention.form)]
              .filter(Boolean)
              .join(" · ")}
          </span>
        </article>
      ))}
    </div>
  );
}

function ProposedInterventions({ proposal }: { proposal: ProposedAnnotation }) {
  return (
    <div className="comparison-cards">
      {proposal.interventions.map((intervention) => (
        <article key={intervention.local_id}>
          <h3>{intervention.name}</h3>
          <strong>{substanceName(proposal, intervention.substance_id)}</strong>
          <p>{formatSummary(intervention.dose)}</p>
          <span>{intervention.regimen || intervention.formulation || "—"}</span>
        </article>
      ))}
    </div>
  );
}

function CuratedOutputs({ study }: { study: Study }) {
  const groups = useMemo(() => {
    const byType = new Map<string, NonNullable<Study["outputs"]>>();
    for (const output of study.outputs ?? []) {
      const name = label(output.measurement_type) || "Unspecified output";
      byType.set(name, [...(byType.get(name) ?? []), output]);
    }
    return [...byType.entries()];
  }, [study.outputs]);
  return (
    <div className="comparison-output-groups">
      {groups.map(([name, outputs]) => (
        <section key={name}>
          <h3>
            {name} <span>{outputs.length}</span>
          </h3>
          {outputs.map((output) => (
            <div className="comparison-output" key={output.pk}>
              <strong>{formatValue(output)}</strong>
              <span>{label(output.substance) || "—"}</span>
              <code>individual {output.individual_pk ?? "—"}</code>
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}

function ProposedOutputs({ proposal }: { proposal: ProposedAnnotation }) {
  const groups = useMemo(() => {
    const byType = new Map<string, ProposedAnnotation["outputs"]>();
    for (const output of proposal.outputs)
      byType.set(output.measurement_type, [
        ...(byType.get(output.measurement_type) ?? []),
        output,
      ]);
    return [...byType.entries()];
  }, [proposal.outputs]);
  return (
    <div className="comparison-output-groups">
      {groups.map(([name, outputs]) => (
        <section key={name}>
          <h3>
            {name} <span>{outputs.length}</span>
          </h3>
          {outputs.map((output) => (
            <div className="comparison-output" key={output.local_id}>
              <strong>{formatSummary(output.result)}</strong>
              <span>{substanceName(proposal, output.substance_id)}</span>
              <code>{output.local_id}</code>
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}

function CuratedIssues() {
  return (
    <div className="comparison-empty">
      <strong>No structured review notes</strong>
      <p>The curated snapshot does not expose unresolved issues.</p>
    </div>
  );
}

function ProposedIssues({ proposal }: { proposal: ProposedAnnotation }) {
  return (
    <div className="issue-list">
      {proposal.unresolved_issues.map((issue) => (
        <article className={`issue issue-${issue.severity}`} key={issue.code}>
          <div>
            <span>{issue.severity}</span>
            <code>{issue.code}</code>
          </div>
          <p>{issue.message}</p>
          <small>
            Source lines {issue.start_line}–{issue.end_line}
          </small>
        </article>
      ))}
    </div>
  );
}

export default function AnnotationComparison({
  study,
  proposal,
}: {
  study: Study;
  proposal: ProposedAnnotation;
}) {
  const [section, setSection] = useState<Section>("overview");
  return (
    <div className="comparison">
      <nav className="comparison-tabs" aria-label="Annotation section">
        {sections.map((item) => (
          <button
            key={item.id}
            className={section === item.id ? "active" : ""}
            onClick={() => setSection(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <div className="comparison-grid">
        <section className="comparison-column comparison-column-curated">
          <ComparisonHeader
            kind="curated"
            title={`${study.name} · ${study.sid}`}
            detail={`PK-DB snapshot ${study.snapshot ?? "unknown"}`}
          />
          <div className="comparison-body">
            {section === "overview" && <CuratedOverview study={study} />}
            {section === "subjects" && <CuratedSubjects study={study} />}
            {section === "interventions" && (
              <CuratedInterventions study={study} />
            )}
            {section === "outputs" && <CuratedOutputs study={study} />}
            {section === "issues" && <CuratedIssues />}
          </div>
        </section>
        <section className="comparison-column comparison-column-proposed">
          <ComparisonHeader
            kind="proposed"
            title={`${proposal.document_id} · schema v${proposal.schema_version}`}
            detail={`${proposal.status} · evidence-linked extraction`}
          />
          <div className="comparison-body">
            {section === "overview" && <ProposedOverview proposal={proposal} />}
            {section === "subjects" && <ProposedSubjects proposal={proposal} />}
            {section === "interventions" && (
              <ProposedInterventions proposal={proposal} />
            )}
            {section === "outputs" && <ProposedOutputs proposal={proposal} />}
            {section === "issues" && <ProposedIssues proposal={proposal} />}
          </div>
        </section>
      </div>
    </div>
  );
}
