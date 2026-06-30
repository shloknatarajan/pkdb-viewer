export interface Node {
  sid: string;
  name: string;
  label?: string;
}

export interface Characteristica {
  pk: number;
  count?: number;
  measurement_type?: Node | null;
  calculation_type?: Node | null;
  choice?: Node | null;
  substance?: Node | null;
  value?: number | null;
  mean?: number | null;
  median?: number | null;
  min?: number | null;
  max?: number | null;
  sd?: number | null;
  se?: number | null;
  cv?: number | null;
  unit?: string | null;
}

export interface Group {
  pk: number;
  name: string;
  parent?: { pk: number; name: string } | null;
  count?: number;
  characteristica: Characteristica[];
}

export interface Individual {
  pk: number;
  name: string;
  group?: { pk: number; name: string; count?: number } | null;
  characteristica: Characteristica[];
}

export interface Intervention {
  pk: number;
  normed?: boolean;
  name: string;
  route?: Node | null;
  form?: Node | null;
  application?: Node | null;
  time?: string | null;
  time_end?: string | null;
  time_unit?: string | null;
  measurement_type?: Node | null;
  choice?: Node | null;
  substance?: Node | null;
  value?: number | null;
  mean?: number | null;
  median?: number | null;
  min?: number | null;
  max?: number | null;
  sd?: number | null;
  se?: number | null;
  cv?: number | null;
  unit?: string | null;
}

export interface Reference {
  pmid?: string | null;
  doi?: string | null;
  title?: string | null;
  abstract?: string | null;
  journal?: string | null;
  date?: string | null;
  authors: string[];
}

export interface Study {
  sid: string;
  name: string;
  licence: string;
  access: string;
  date?: string;
  counts: Record<string, number | null>;
  reference: Reference;
  curators: string[];
  descriptions: string[];
  substances: Node[];
  groups: Group[];
  individuals: Individual[];
  interventions: Intervention[];
  paper: { source: string; licence: string | null; pmcid: string | null };
}

export interface IndexEntry {
  sid: string;
  name: string;
  title?: string | null;
  pmid?: string | null;
  journal?: string | null;
  year?: string;
  substances: string[];
  n_groups?: number | null;
  n_individuals?: number | null;
  n_interventions?: number | null;
  paper_source: string;
  paper_licence?: string | null;
}

export interface IndexFile {
  generated: string;
  count: number;
  note: string;
  studies: IndexEntry[];
}
