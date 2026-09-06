import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({ selector: 'app-login', templateUrl: './login.component.html', styleUrls: ['./login.component.scss'] })
export class LoginComponent {
  loading = false;
  constructor(private readonly auth: AuthService, private readonly router: Router) { if (auth.isAuthenticated) router.navigateByUrl('/home'); }
  continueWithGoogle(): void { this.loading = true; this.auth.signInWithGoogle().subscribe(() => this.router.navigateByUrl('/home')); }
}