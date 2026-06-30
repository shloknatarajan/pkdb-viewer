import type {
  Characteristica,
  IndexFile,
  Intervention,
  Output,
  Study,
} from "./types";

const BASE = import.meta.env.BASE_URL; // "./" in this build

export async function loadIndex(): Promise<IndexFile> {
  const r = await fetch(`${BASE}data/index.json`);
  if (!r.ok) throw new Error(`Could not load study index (${r.status})`);
  return r.json();
}

export async function loadStudy(sid: string): Promise<Study> {
  const r = await fetch(`${BASE}data/${sid}/study.json`);
  if (!r.ok) throw new Error(`Could not load study ${sid} (${r.status})`);
  return r.json();
}

export async function loadPaper(sid: string): Promise<string> {
  const r = await fetch(`${BASE}data/${sid}/paper.md`);
  if (!r.ok) throw new Error(`Could not load paper for ${sid} (${r.status})`);
  return r.text();
}

const num = (n: number) =>
  Number.isInteger(n) ? String(n) : Number(n.toPrecision(4)).toString();

/**
 * Render the numeric/categorical payload shared by characteristica and
 * interventions into one compact human-readable string, e.g.
 *   "54 (41–78) yr", "0.0075 gram", "Homo sapiens".
 */
export function formatValue(
  c: Characteristica | Intervention | Output
): string {
  if (c.choice) return c.choice.label || c.choice.name;
  const unit = c.unit ? ` ${c.unit}` : "";
  const central = c.value ?? c.mean ?? c.median;
  const parts: string[] = [];
  if (central != null) parts.push(num(central));
  if (c.min != null || c.max != null) {
    const lo = c.min != null ? num(c.min) : "?";
    const hi = c.max != null ? num(c.max) : "?";
    parts.push(`(${lo}–${hi})`);
  }
  if (c.sd != null) parts.push(`± ${num(c.sd)}`);
  else if (c.se != null) parts.push(`±se ${num(c.se)}`);
  if (parts.length === 0) return "—";
  return parts.join(" ") + unit;
}

export const label = (n?: { label?: string; name: string } | null) =>
  n ? n.label || n.name : "";
