import { Component, OnDestroy, OnInit } from '@angular/core';

@Component({ selector: 'app-ai-processing', templateUrl: './ai-processing.component.html', styleUrls: ['./ai-processing.component.scss'] })
export class AiProcessingComponent implements OnInit, OnDestroy {
  messages = ['Reviewing case documentation...', 'Analysing financial information...', 'Reviewing legal and contractual obligations...', 'Structuring the resolution framework...', 'Preparing the draft resolution plan...'];
  index = 0; private timer?: ReturnType<typeof setInterval>;
  ngOnInit(): void { this.timer = setInterval(() => this.index = (this.index + 1) % this.messages.length, 1800); }
  ngOnDestroy(): void { if (this.timer) clearInterval(this.timer); }
}