import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { CommonModule, DecimalPipe } from '@angular/common';
import { HttpErrorInterceptor } from './core/interceptors/http-error.interceptor';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';

// Import components
import { AppComponent } from './app.component';
import { HomeComponent } from './pages/home/home.component';
import { CompanyDetailComponent } from './pages/company-detail/company-detail.component';
import { MarketOverviewComponent } from './pages/market-overview/market-overview.component';
import { IndicesComponent } from './pages/indices/indices.component';

// Import shared components
import { SharedModule } from './shared/shared.module';

@NgModule({
  declarations: [
    HomeComponent,
    CompanyDetailComponent,
    MarketOverviewComponent,
    IndicesComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    RouterModule.forRoot(routes),
    ReactiveFormsModule,
    FormsModule,
    CommonModule,
    SharedModule
  ],
  providers: [
    provideRouter(routes),
    // Uncomment when error interceptor is properly converted to class instead of function
    // {
    //   provide: HTTP_INTERCEPTORS,
    //   useClass: HttpErrorInterceptor,
    //   multi: true
    // }
    DecimalPipe
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }