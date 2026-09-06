export type DocumentStatus = 'Uploading' | 'Ready' | 'Processing' | 'Error';
export type Severity = 'Critical' | 'High' | 'Medium' | 'Low';

export interface CaseDocument {
  id: number;
  name: string;
  size: string;
  status: DocumentStatus;
  backendId?: string;
  errorMessage?: string;
}
export interface Finding {
  id: number; severity: Severity; title: string; explanation: string;
  contractReference: string; planReference: string; recommendation: string;
}
export interface ValidationResult { status: 'Aligned with observations'; findings: Finding[]; }