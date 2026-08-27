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

export interface Output {
  pk: number;
  measurement_type?: Node | null;
  substance?: Node | null;
  tissue?: Node | null;
  method?: Node | null;
  calculation_type?: Node | null;
  choice?: Node | null;
  label?: string | null;
  time?: number | null;
  time_unit?: string | null;
  intervention_pk?: number | null;
  group_pk?: number | null;
  individual_pk?: number | null;
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

export interface Timecourse {
  pk: number;
  name?: string | null;
  label?: string | null;
  measurement_type?: Node | null;
  substance?: Node | null;
  tissue?: Node | null;
  method?: Node | null;
  intervention_pk?: number | null;
  group_pk?: number | null;
  individual_pk?: number | null;
  time: (number | null)[];
  time_unit?: string | null;
  unit?: string | null;
  values?: (number | null)[] | null;
  mean?: (number | null)[] | null;
  sd?: (number | null)[] | null;
}

export interface ScatterAxis {
  measurement_type?: Node | null;
  substance?: Node | null;
  tissue?: Node | null;
  label?: string | null;
  unit?: string | null;
  values?: (number | null)[] | null;
}

export interface Scatter {
  pk: number;
  name?: string | null;
  x: ScatterAxis;
  y: ScatterAxis;
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
  snapshot?: string;
  counts: Record<string, number | null>;
  reference: Reference;
  curators: string[];
  descriptions: string[];
  substances: Node[];
  groups: Group[];
  individuals: Individual[];
  interventions: Intervention[];
  outputs?: Output[];
  timecourses?: Timecourse[];
  scatters?: Scatter[];
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
  n_outputs?: number | null;
  n_timecourses?: number | null;
  paper_source: string;
  paper_licence?: string | null;
}

export interface IndexFile {
  generated: string;
  count: number;
  note: string;
  studies: IndexEntry[];
}

export interface ProposedEvidence {
  kind: string;
  source_path: string;
  start_line: number;
  end_line: number;
  quote: string;
}

export interface ProposedSummary {
  as_reported?: string | null;
  value?: number | null;
  values?: number[] | null;
  mean?: number | null;
  geometric_mean?: number | null;
  median?: number | null;
  minimum?: number | null;
  maximum?: number | null;
  sd?: number | null;
  se?: number | null;
  cv?: number | null;
  ci_lower?: number | null;
  ci_upper?: number | null;
  unit?: string | null;
}

export interface ProposedCharacteristic {
  local_id: string;
  name: string;
  choice?: string | null;
  substance_id?: string | null;
  count?: number | null;
  summary: ProposedSummary;
  evidence: ProposedEvidence[];
}

export interface ProposedGroup {
  local_id: string;
  name: string;
  parent_id?: string | null;
  count?: number | null;
  characteristics: ProposedCharacteristic[];
  evidence: ProposedEvidence[];
}

export interface ProposedSubstance {
  local_id: string;
  reported_name: string;
  normalized_id?: string | null;
  evidence: ProposedEvidence[];
}

export interface ProposedIntervention {
  local_id: string;
  name: string;
  substance_id?: string | null;
  intervention_type?: string | null;
  route?: string | null;
  formulation?: string | null;
  regimen?: string | null;
  dose: ProposedSummary;
  time: ProposedSummary;
  group_ids: string[];
  individual_ids: string[];
  evidence: ProposedEvidence[];
}

export interface ProposedOutput {
  local_id: string;
  measurement_type: string;
  substance_id?: string | null;
  matrix?: string | null;
  calculation_type?: string | null;
  group_id?: string | null;
  individual_id?: string | null;
  intervention_ids: string[];
  time: ProposedSummary;
  result: ProposedSummary;
  evidence: ProposedEvidence[];
}

export interface ProposedIssue {
  code: string;
  message: string;
  severity: "info" | "warning" | string;
  source_path: string;
  start_line: number;
  end_line: number;
}

export interface ProposedAnnotation {
  schema_version: number;
  document_id: string;
  existing_pkdb_sid?: string | null;
  status: string;
  reference: {
    title: string;
    authors: string[];
    journal?: string | null;
    publication_date?: string | null;
    doi?: string | null;
    pmid?: string | null;
    pmcid?: string | null;
    evidence: ProposedEvidence[];
  };
  study_design?: string | null;
  substances: ProposedSubstance[];
  groups: ProposedGroup[];
  individuals: unknown[];
  interventions: ProposedIntervention[];
  outputs: ProposedOutput[];
  timecourses: unknown[];
  scatters: unknown[];
  unresolved_issues: ProposedIssue[];
}
