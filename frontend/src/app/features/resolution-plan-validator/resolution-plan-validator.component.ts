import { Component } from '@angular/core';
import { ResolutionPlanService } from '../../core/resolution-plan.service';
import { CaseDocument, Finding, ValidationResult } from '../../shared/models';
type ValidatorStage = 'input' | 'processing' | 'results';
@Component({ selector: 'app-resolution-plan-validator', templateUrl: './resolution-plan-validator.component.html', styleUrls: ['./resolution-plan-validator.component.scss'] })
export class ResolutionPlanValidatorComponent {
  stage: ValidatorStage = 'input'; selectedPlan = ''; document?: CaseDocument; result?: ValidationResult; expandedId?: number; error = '';
  constructor(private readonly plans: ResolutionPlanService) {}
  addDocument(file: File): void { this.document = { id: Date.now(), name: file.name, size: `${Math.max(1, Math.round(file.size / 1024))} KB`, status: 'Ready' }; }
  validate(): void { if (!this.selectedPlan || !this.document) { this.error = 'Select a resolution plan and add a contract to continue.'; return; } this.error = ''; this.stage = 'processing'; this.plans.validate().subscribe(result => { this.result = result; this.stage = 'results'; }); }
  toggle(finding: Finding): void { this.expandedId = this.expandedId === finding.id ? undefined : finding.id; }
}