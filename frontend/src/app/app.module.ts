import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { LoginComponent } from './features/login/login.component';
import { HomeComponent } from './features/home/home.component';
import { ResolutionPlanCreatorComponent } from './features/resolution-plan-creator/resolution-plan-creator.component';
import { ResolutionPlanValidatorComponent } from './features/resolution-plan-validator/resolution-plan-validator.component';
import { AppShellComponent } from './shared/app-shell/app-shell.component';
import { DocumentUploadComponent } from './shared/document-upload/document-upload.component';
import { AiProcessingComponent } from './shared/ai-processing/ai-processing.component';

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    HomeComponent,
    ResolutionPlanCreatorComponent,
    ResolutionPlanValidatorComponent,
    AppShellComponent,
    DocumentUploadComponent,
    AiProcessingComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    HttpClientModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
