export type BackendDocumentStatus = 'pending' | 'extracting' | 'embedding' | 'completed' | 'failed';

export interface LegalDocumentPublic {
  id: string;
  original_filename: string;
  content_type?: string | null;
  document_type?: string | null;
  status: BackendDocumentStatus;
  error_message?: string | null;
  page_count?: number | null;
  chunk_count?: number | null;
  created_at: string;
  updated_at: string;
}

export interface LegalDocumentUploadResponse {
  document: LegalDocumentPublic;
  message: string;
}

export type GenerationStatus = 'pending' | 'retrieving' | 'answering' | 'rendering_docx' | 'completed' | 'failed';

export interface GenerationMetadata {
  question_count?: number;
  group_count?: number;
  llm_model?: string;
  embedding_model?: string;
  retrieval_top_k?: number;
}

export interface ResolutionPlanGenerationPublic {
  id: string;
  status: GenerationStatus;
  error_message?: string | null;
  generation_metadata?: GenerationMetadata | null;
  docx_path?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResolutionPlanGenerationDetail extends ResolutionPlanGenerationPublic {
  template_json?: unknown;
  source_document_ids: string[];
}
