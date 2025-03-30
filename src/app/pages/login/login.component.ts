import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService, SocialProvider } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink]
})
export class LoginComponent implements OnInit {
  loginForm: FormGroup;
  isSubmitting = false;
  error: string | null = null;
  socialLoginInProgress = false;
  
  constructor(
    private formBuilder: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.loginForm = this.formBuilder.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]]
    });
  }

  ngOnInit(): void {
    // Check if we're returning from a social login callback
    this.route.queryParams.subscribe(params => {
      if (params['code'] || params['oauth_token'] || params['state']) {
        this.handleSocialLoginCallback();
      }
    });

    // If already logged in, redirect to home
    if (this.authService.isLoggedIn()) {
      this.router.navigate(['/']);
    }
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      return;
    }

    this.isSubmitting = true;
    this.error = null;
    
    const { email, password } = this.loginForm.value;
    
    this.authService.login(email, password).subscribe({
      next: (response) => {
        if (response.error) {
          this.error = response.error;
          this.isSubmitting = false;
          return;
        }
        
        // Successful login
        this.router.navigate(['/']);
      },
      error: (err) => {
        this.error = err.message || 'An error occurred during login';
        this.isSubmitting = false;
      }
    });
  }

  /**
   * Initiate social login with a provider
   */
  socialLogin(provider: SocialProvider): void {
    this.socialLoginInProgress = true;
    this.error = null;
    this.authService.socialLogin(provider);
  }

  /**
   * Handle the callback from social login providers
   */
  private handleSocialLoginCallback(): void {
    this.socialLoginInProgress = true;
    this.error = null;
    
    this.authService.handleSocialLoginCallback().subscribe({
      next: (response) => {
        if (response.error) {
          this.error = response.error;
          this.socialLoginInProgress = false;
          return;
        }
        
        // Successful login
        this.router.navigate(['/']);
      },
      error: (err) => {
        this.error = err.message || 'An error occurred during social login';
        this.socialLoginInProgress = false;
      }
    });
  }
}