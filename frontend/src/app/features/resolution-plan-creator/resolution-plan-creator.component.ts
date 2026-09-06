import { Component, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { ResolutionPlanService } from '../../core/resolution-plan.service';
import { BackendDocumentStatus, ResolutionPlanGenerationDetail } from '../../core/resolution-plan.models';
import { CaseDocument, DocumentStatus } from '../../shared/models';

type CreatorStage = 'upload' | 'processing' | 'review';

function mapDocumentStatus(status: BackendDocumentStatus): DocumentStatus {
  if (status === 'completed') return 'Ready';
  if (status === 'failed') return 'Error';
  return 'Processing';
}

@Component({ selector: 'app-resolution-plan-creator', templateUrl: './resolution-plan-creator.component.html', styleUrls: ['./resolution-plan-creator.component.scss'] })
export class ResolutionPlanCreatorComponent implements OnDestroy {
  stage: CreatorStage = 'upload';
  documents: CaseDocument[] = [];
  error = '';
  generation?: ResolutionPlanGenerationDetail;

  private nextLocalId = 1;
  private readonly subscriptions = new Subscription();

  constructor(private readonly plans: ResolutionPlanService) {}

  get canGenerate(): boolean {
    return this.documents.length > 0 && this.documents.every(document => document.status === 'Ready');
  }

  get downloadUrl(): string | null {
    return this.generation?.status === 'completed' ? this.plans.getDownloadUrl(this.generation.id) : null;
  }

  addDocument(file: File): void {
    const localId = this.nextLocalId++;
    const placeholder: CaseDocument = {
      id: localId,
      name: file.name,
      size: `${Math.max(1, Math.round(file.size / 1024))} KB`,
      status: 'Uploading'
    };
    this.documents = [...this.documents, placeholder];
    this.error = '';

    const sub = this.plans
      .uploadDocument(file)
      .pipe(
        switchMap(response => {
          this.patchDocument(localId, {
            backendId: response.document.id,
            status: mapDocumentStatus(response.document.status)
          });
          return this.plans.pollDocumentUntilDone(response.document.id);
        })
      )
      .subscribe({
        next: document =>
          this.patchDocument(localId, {
            status: mapDocumentStatus(document.status),
            errorMessage: document.error_message ?? undefined
          }),
        error: () => this.patchDocument(localId, { status: 'Error', errorMessage: 'Upload failed. Please try again.' })
      });
    this.subscriptions.add(sub);
  }

  removeDocument(id: number): void {
    this.documents = this.documents.filter(document => document.id !== id);
  }

  generate(): void {
    if (!this.documents.length) {
      this.error = 'Add at least one case document to continue.';
      return;
    }
    if (!this.canGenerate) {
      this.error = 'Wait for all documents to finish processing before generating.';
      return;
    }
    this.error = '';
    this.stage = 'processing';
    this.generation = undefined;

    const documentIds = this.documents.map(document => document.backendId).filter((id): id is string => !!id);

    const sub = this.plans
      .createGeneration(documentIds)
      .pipe(switchMap(generation => this.plans.pollGenerationUntilDone(generation.id)))
      .subscribe({
        next: generation => {
          this.generation = generation;
          if (generation.status === 'completed' || generation.status === 'failed') {
            this.stage = 'review';
          }
        },
        error: () => {
          this.error = 'We could not generate the plan. Please try again.';
          this.stage = 'upload';
        }
      });
    this.subscriptions.add(sub);
  }

  startOver(): void {
    this.stage = 'upload';
    this.documents = [];
    this.generation = undefined;
    this.error = '';
  }

  private patchDocument(id: number, patch: Partial<CaseDocument>): void {
    this.documents = this.documents.map(document => (document.id === id ? { ...document, ...patch } : document));
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }
}