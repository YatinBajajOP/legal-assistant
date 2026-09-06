import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { interval, Observable, of } from 'rxjs';
import { delay, startWith, switchMap, takeWhile } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { ValidationResult } from '../shared/models';
import {
  LegalDocumentPublic,
  LegalDocumentUploadResponse,
  ResolutionPlanGenerationDetail,
  ResolutionPlanGenerationPublic
} from './resolution-plan.models';

const TERMINAL_DOCUMENT_STATUSES = new Set(['completed', 'failed']);
const TERMINAL_GENERATION_STATUSES = new Set(['completed', 'failed']);
const POLL_INTERVAL_MS = 2500;

@Injectable({ providedIn: 'root' })
export class ResolutionPlanService {
  private readonly baseUrl = `${environment.backendUrl}/resolution-plan`;

  constructor(private readonly http: HttpClient) {}

  uploadDocument(file: File, documentType?: string): Observable<LegalDocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    let params = new HttpParams();
    if (documentType) {
      params = params.set('document_type', documentType);
    }
    return this.http.post<LegalDocumentUploadResponse>(`${this.baseUrl}/documents`, formData, { params });
  }

  getDocument(documentId: string): Observable<LegalDocumentPublic> {
    return this.http.get<LegalDocumentPublic>(`${this.baseUrl}/documents/${documentId}`);
  }

  /** Emits the document's status every poll tick until it reaches a terminal state. */
  pollDocumentUntilDone(documentId: string): Observable<LegalDocumentPublic> {
    return interval(POLL_INTERVAL_MS).pipe(
      startWith(0),
      switchMap(() => this.getDocument(documentId)),
      takeWhile(doc => !TERMINAL_DOCUMENT_STATUSES.has(doc.status), true)
    );
  }

  createGeneration(documentIds: string[]): Observable<ResolutionPlanGenerationPublic> {
    return this.http.post<ResolutionPlanGenerationPublic>(`${this.baseUrl}/generations`, {
      document_ids: documentIds
    });
  }

  getGeneration(generationId: string): Observable<ResolutionPlanGenerationDetail> {
    return this.http.get<ResolutionPlanGenerationDetail>(`${this.baseUrl}/generations/${generationId}`);
  }

  /** Emits the generation's status every poll tick until it reaches a terminal state. */
  pollGenerationUntilDone(generationId: string): Observable<ResolutionPlanGenerationDetail> {
    return interval(POLL_INTERVAL_MS).pipe(
      startWith(0),
      switchMap(() => this.getGeneration(generationId)),
      takeWhile(gen => !TERMINAL_GENERATION_STATUSES.has(gen.status), true)
    );
  }

  getDownloadUrl(generationId: string): string {
    return `${this.baseUrl}/generations/${generationId}/download`;
  }

  // Resolution Plan Validator still uses mocked data; not part of the backend integration scope.
  validate(): Observable<ValidationResult> {
    return of<ValidationResult>({ status: 'Aligned with observations', findings: [
      { id: 1, severity: 'High', title: 'Payment timetable requires confirmation', explanation: 'The contract payment schedule does not explicitly mirror the phased distribution timetable in the resolution plan.', contractReference: 'Clause 7.2', planReference: 'Section 4.1', recommendation: 'Add a schedule that maps each payment milestone to the approved distribution timetable.' },
      { id: 2, severity: 'Medium', title: 'Termination language is broader than approved', explanation: 'Termination rights may permit action outside the conditions contemplated by the resolution framework.', contractReference: 'Clause 11', planReference: 'Section 6.3', recommendation: 'Limit termination rights to the specific events and notices set out in the plan.' },
      { id: 3, severity: 'Low', title: 'Reporting cadence is unspecified', explanation: 'The contract requires reporting but does not state a submission cadence.', contractReference: 'Clause 9.1', planReference: 'Section 7.2', recommendation: 'Specify monthly reporting in line with the monitoring framework.' }
    ] }).pipe(delay(3800));
  }
}