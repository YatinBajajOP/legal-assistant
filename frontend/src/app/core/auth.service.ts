import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { delay, tap } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly key = 'solvency-ai-authenticated';
  private readonly authenticated = new BehaviorSubject<boolean>(localStorage.getItem(this.key) === 'true');
  readonly isAuthenticated$ = this.authenticated.asObservable();

  get isAuthenticated(): boolean { return this.authenticated.value; }

  signInWithGoogle(): Observable<void> {
    return of(undefined).pipe(delay(650), tap(() => { localStorage.setItem(this.key, 'true'); this.authenticated.next(true); }));
  }

  signOut(): void { localStorage.removeItem(this.key); this.authenticated.next(false); }
}