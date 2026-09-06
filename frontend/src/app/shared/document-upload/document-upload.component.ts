import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({ selector: 'app-document-upload', templateUrl: './document-upload.component.html', styleUrls: ['./document-upload.component.scss'] })
export class DocumentUploadComponent {
  @Input() label = 'Add documents'; @Output() documentsAdded = new EventEmitter<File>();
  addFiles(event: Event): void { const files = (event.target as HTMLInputElement).files; if (!files) return; Array.from(files).forEach(file => this.documentsAdded.emit(file)); (event.target as HTMLInputElement).value = ''; }
}