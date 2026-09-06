import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from './core/auth.guard';
import { LoginComponent } from './features/login/login.component';
import { HomeComponent } from './features/home/home.component';
import { ResolutionPlanCreatorComponent } from './features/resolution-plan-creator/resolution-plan-creator.component';
import { ResolutionPlanValidatorComponent } from './features/resolution-plan-validator/resolution-plan-validator.component';

const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'home', component: HomeComponent, canActivate: [AuthGuard] },
  { path: 'resolution-plan/create', component: ResolutionPlanCreatorComponent, canActivate: [AuthGuard] },
  { path: 'resolution-plan/validate', component: ResolutionPlanValidatorComponent, canActivate: [AuthGuard] },
  { path: '', pathMatch: 'full', redirectTo: 'home' },
  { path: '**', redirectTo: 'home' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
