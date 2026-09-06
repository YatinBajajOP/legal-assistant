import { Component } from '@angular/core';
interface Feature { title: string; copy: string; route?: string; locked?: boolean; }
@Component({ selector: 'app-home', templateUrl: './home.component.html', styleUrls: ['./home.component.scss'] })
export class HomeComponent {
  features: Feature[] = [
    { title: 'Resolution Plan Creator', copy: 'Create a structured plan from case documentation.', route: '/resolution-plan/create' },
    { title: 'Resolution Plan Validator', copy: 'Check contracts against an approved resolution plan.', route: '/resolution-plan/validate' },
    { title: 'Compliance Checker', copy: 'Surface priority compliance obligations.', locked: true }, { title: 'Claims Analysis', copy: 'Classify and review creditor claims.', locked: true }, { title: 'Case Document Intelligence', copy: 'Discover key facts across case files.', locked: true }, { title: 'Due Diligence Assistant', copy: 'Organise diligence questions and evidence.', locked: true }
  ];
}