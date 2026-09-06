import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({ selector: 'app-shell', templateUrl: './app-shell.component.html', styleUrls: ['./app-shell.component.scss'] })
export class AppShellComponent {
  constructor(private readonly auth: AuthService, private readonly router: Router) {}
  signOut(): void { this.auth.signOut(); this.router.navigateByUrl('/login'); }
}