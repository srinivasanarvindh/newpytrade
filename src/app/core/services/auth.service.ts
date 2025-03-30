import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { Router } from '@angular/router';

interface User {
  id: string;
  username: string;
  email: string;
}

export type SocialProvider = 'google' | 'facebook' | 'twitter' | 'github';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();
  private apiUrl = environment.apiUrl;

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    this.checkAuthStatus();
  }

  checkAuthStatus(): void {
    const user = localStorage.getItem('user');
    if (user) {
      this.currentUserSubject.next(JSON.parse(user));
    }
  }

  login(email: string, password: string): Observable<any> {
    return this.http.post<{ user: User, token: string }>(`${this.apiUrl}/api/auth/login`, { email, password }).pipe(
      tap(response => {
        if (response.user && response.token) {
          localStorage.setItem('user', JSON.stringify(response.user));
          localStorage.setItem('token', response.token);
          this.currentUserSubject.next(response.user);
        }
      }),
      catchError(error => {
        console.error('Login error', error);
        return of({ error: error.error?.message || 'Login failed' });
      })
    );
  }

  /**
   * Initiates a social login by redirecting to the appropriate provider's OAuth flow
   * @param provider The social login provider (google, facebook, twitter, github)
   */
  socialLogin(provider: SocialProvider): void {
    // For most providers, we would use window.location.href, but for the Google login flow,
    // we can use our backend API as an intermediary
    window.location.href = `${this.apiUrl}/auth/social/${provider}`;
  }

  /**
   * Handles social login callback
   * This method is called when the user is redirected back from the social login provider
   */
  handleSocialLoginCallback(): Observable<any> {
    return this.http.get<{ user: User, token: string }>(`${this.apiUrl}/api/auth/status`).pipe(
      tap(response => {
        if (response && response.user) {
          localStorage.setItem('user', JSON.stringify(response.user));
          if (response.token) {
            localStorage.setItem('token', response.token);
          }
          this.currentUserSubject.next(response.user);
        }
      }),
      catchError(error => {
        console.error('Social login callback error', error);
        return of({ error: error.error?.message || 'Social login failed' });
      })
    );
  }

  logout(): void {
    // Send logout request to the server
    this.http.post(`${this.apiUrl}/api/auth/logout`, {}).subscribe({
      next: () => {
        this.clearAuthData();
      },
      error: (err) => {
        console.error('Logout error', err);
        this.clearAuthData();
      }
    });
  }

  private clearAuthData(): void {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    this.currentUserSubject.next(null);
    this.router.navigate(['/login']);
  }

  isLoggedIn(): boolean {
    return !!this.currentUserSubject.value;
  }

  register(username: string, email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/auth/register`, { username, email, password }).pipe(
      catchError(error => {
        console.error('Registration error', error);
        return of({ error: error.error?.message || 'Registration failed' });
      })
    );
  }
}
