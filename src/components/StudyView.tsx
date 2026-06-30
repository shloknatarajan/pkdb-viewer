import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { loadPaper, loadStudy } from "../data";
import type { Study } from "../types";
import DataPanel from "./DataPanel";

export default function StudyView({ sid }: { sid: string }) {
  const [study, setStudy] = useState<Study | null>(null);
  const [paper, setPaper] = useState<string>("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setStudy(null);
    setPaper("");
    setErr(null);
    Promise.all([loadStudy(sid), loadPaper(sid)])
      .then(([s, p]) => {
        setStudy(s);
        setPaper(p);
      })
      .catch((e) => setErr(String(e)));
  }, [sid]);

  if (err)
    return (
      <main className="page">
        <a className="back" href="#/">← all studies</a>
        <div className="error">{err}</div>
      </main>
    );
  if (!study) return <main className="page"><div className="loading">Loading study…</div></main>;

  const ref = study.reference;
  const pmidUrl = ref.pmid ? `https://pubmed.ncbi.nlm.nih.gov/${ref.pmid}/` : null;
  const pmcUrl = study.paper.pmcid
    ? `https://www.ncbi.nlm.nih.gov/pmc/articles/${study.paper.pmcid}/`
    : null;
  const pkdbUrl = `https://pk-db.com/data/${study.sid}`;

  return (
    <div className="study">
      <div className="study-head">
        <a className="back" href="#/">← all studies</a>
        <div className="study-titlewrap">
          <h1 className="study-title">{ref.title || study.name}</h1>
          <div className="study-meta">
            {ref.authors.length > 0 && (
              <span className="authors">{ref.authors.join(", ")}</span>
            )}
            <span className="dot">·</span>
            {ref.journal && <span>{ref.journal}</span>}
            {ref.date && <span className="dot">·</span>}
            {ref.date && <span>{ref.date.slice(0, 4)}</span>}
          </div>
          <div className="study-links">
            <span className="tag">{study.name}</span>
            {pmidUrl && <a href={pmidUrl} target="_blank" rel="noreferrer">PubMed {ref.pmid}</a>}
            {pmcUrl && <a href={pmcUrl} target="_blank" rel="noreferrer">{study.paper.pmcid}</a>}
            {ref.doi && (
              <a href={`https://doi.org/${ref.doi}`} target="_blank" rel="noreferrer">
                doi:{ref.doi}
              </a>
            )}
            <a href={pkdbUrl} target="_blank" rel="noreferrer">PK-DB ↗</a>
          </div>
        </div>
      </div>

      <div className="split">
        <section className="pane pane-paper">
          <div className="pane-label">
            Original paper
            {study.paper.source === "abstract" ? (
              <span className="pane-note">abstract only — full text not in PMC OA</span>
            ) : (
              <span className="pane-note">
                full text via {study.paper.source}
                {study.paper.licence ? ` · ${study.paper.licence}` : ""}
              </span>
            )}
          </div>
          <article className="paper markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{paper}</ReactMarkdown>
          </article>
        </section>

        <section className="pane pane-data">
          <div className="pane-label">Extracted data</div>
          <DataPanel study={study} />
        </section>
      </div>
    </div>
  );
}
