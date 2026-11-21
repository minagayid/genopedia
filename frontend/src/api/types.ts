export interface User {
  id: number;
  email: string;
  full_name: string | null;
  email_verified: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface AnalysisListItem {
  id: number;
  name: string;
  input_format: string;
  molecule: string;
  record_count: number;
  variant_count: number;
  total_bases: number;
  sequence_sha256: string;
  created_at: string;
}

export interface QualityReport {
  identifier: string;
  length: number;
  gc_fraction: number;
  ambiguous_count: number;
  invalid_symbols: string[];
  mean_quality: number | null;
  status: string;
  warnings: string[];
}

export interface Variant {
  chromosome: string;
  position: number;
  reference: string;
  observed: string;
  quality: number | null;
  variant_type: string;
  interpretation: string;
  metadata: Record<string, unknown>;
}

export interface SequenceAnomaly {
  identifier: string;
  category: string;
  severity: string;
  evidence: string;
  suggested_action: string;
  safety: string;
}

export interface CorrectionSuggestion {
  [key: string]: unknown;
}

export interface AnalysisSummary {
  records: QualityReport[];
  variants: Variant[];
  sequence_anomalies: SequenceAnomaly[];
  correction_plan: CorrectionSuggestion[];
  safety: string;
}

export interface StoredRecord {
  identifier: string;
  description: string;
  source_format: string;
  sequence: string;
  truncated: boolean;
}

export interface AnalysisDetail extends AnalysisListItem {
  summary: AnalysisSummary;
  records: StoredRecord[];
  report_url: string;
}

export interface ComparisonResult {
  chromosome: string;
  reference_length: number;
  sample_length: number;
  variant_count: number;
  variants: Variant[];
  safety: string;
}

export interface AIStatus {
  available: boolean;
  state: string;
  model: string | null;
  message: string;
}
