/**
 * App Routing Module
 * 
 * This module defines all application routes and navigation configuration.
 * It includes routes for:
 * - Main pages (home, markets, indices, screener)
 * - Company details pages
 * - Trading strategy pages
 * - Resource pages (learning center, blog, etc.)
 * - Legal pages (terms, privacy, etc.)
 * - Placeholder routes with "coming soon" messages for features in development
 */
import { NgModule } from '@angular/core';
import { RouterModule, Routes, ExtraOptions } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { CompanyDetailComponent } from './pages/company-detail/company-detail.component';
import { MarketOverviewComponent } from './pages/market-overview/market-overview.component';
import { IndicesComponent } from './pages/indices/indices.component';
import { ScreenerComponent } from './pages/screener/screener.component';

// Import types for route guard function
import { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

/**
 * Route Guard: Symbol Validation
 * 
 * This guard function prevents reserved application routes from being treated as stock symbols.
 * When a user navigates to a URL like /AAPL, we want to treat it as a stock symbol.
 * However, we need to prevent treating reserved paths like /login or /portfolio as stock symbols.
 * 
 * @param route - The activated route snapshot containing route parameters
 * @param state - The router state snapshot
 * @returns boolean - True if the path is a valid stock symbol (not a reserved path)
 */
const isValidSymbolGuard = (route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean => {
  const symbol = route.paramMap.get('symbol');
  // List of all reserved paths that should not be treated as stock symbols
  const reservedPaths = [
    'assets', 
    'favicon.ico', 
    'portfolio', 
    'screener', 
    'watchlist', 
    'settings', 
    'notifications',
    'account',
    'login',
    'register',
    'dashboard',
    'help',
    'about',
    'contact',
    'privacy',
    'terms',
    'stocks',
    'market-overview',
    'indices',
    'company',
    'stock',
    'sectors',
    'news',
    'sentiment',
    'alerts',
    'strategies',
    'learning',
    'academy',
    'blog',
    'api',
    'disclaimer',
    'cookies',
    'security',
    'swing-trading',
    'tools'
  ];
  return !reservedPaths.includes(symbol?.toLowerCase() || '');
};

/**
 * Application Routes Configuration
 * 
 * Defines all routes for the PyTrade application, organized in categories:
 * 1. Core Pages - Main application pages
 * 2. Feature Pages - Trading tools and market analysis
 * 3. Strategy Pages - Different trading strategy information
 * 4. Resource Pages - Learning resources and documentation
 * 5. Legal Pages - Terms, privacy, disclaimer pages
 * 6. Authentication - Login and account pages
 * 7. Dynamic Routes - Stock symbol and company pages
 * 
 * Routes with { data: { message: '...' } } display a "coming soon" message
 * using the HomeComponent as a placeholder until the feature is implemented.
 */
export const routes: Routes = [
  // 1. Core Pages
  { path: '', component: HomeComponent, pathMatch: 'full' },
  { path: 'market-overview', component: MarketOverviewComponent },
  { path: 'indices', component: IndicesComponent },
  { path: 'indices/:name', component: IndicesComponent },
  { path: 'stocks', component: MarketOverviewComponent },
  
  // 2. Feature Pages (Some with placeholders)
  { path: 'portfolio', component: HomeComponent }, // Placeholder until implemented
  { path: 'screener', loadComponent: () => import('./pages/screener/screener.component').then(m => m.ScreenerComponent) },
  { path: 'watchlist', component: HomeComponent }, // Placeholder until implemented
  { path: 'sectors', component: HomeComponent, data: { message: 'Sector Analysis coming soon' } },
  { path: 'news', component: HomeComponent, data: { message: 'Market News coming soon' } },
  { path: 'sentiment', component: HomeComponent, data: { message: 'Market Sentiment coming soon' } },
  { path: 'alerts', component: HomeComponent, data: { message: 'Price Alerts coming soon' } },
  
  // 3. Strategy Pages
  { path: 'strategies/intraday', component: HomeComponent, data: { message: 'Intraday Trading Strategies coming soon' } },
  { path: 'strategies/swing', loadComponent: () => import('./pages/swing-trading/swing-trading.component').then(m => m.SwingTradingComponent) },
  { path: 'swing-trading', loadComponent: () => import('./pages/swing-trading/swing-trading.component').then(m => m.SwingTradingComponent) },
  { path: 'tools', loadComponent: () => import('./pages/tools/toolspage.component').then(m => m.ToolspageComponent) },
  { path: 'strategies/positional', component: HomeComponent, data: { message: 'Positional Trading Strategies coming soon' } },
  { path: 'strategies/options', component: HomeComponent, data: { message: 'Options Trading Strategies coming soon' } },
  { path: 'strategies/ai', component: HomeComponent, data: { message: 'AI-Powered Trading Strategies coming soon' } },
  
  // 4. Resource Pages
  { path: 'learning', component: HomeComponent, data: { message: 'Learning Center coming soon' } },
  { path: 'academy', component: HomeComponent, data: { message: 'Trading Academy coming soon' } },
  { path: 'blog', component: HomeComponent, data: { message: 'Market Blog coming soon' } },
  { path: 'help', component: HomeComponent, data: { message: 'Help & Support coming soon' } },
  { path: 'api', component: HomeComponent, data: { message: 'API Documentation coming soon' } },
  
  // 5. Legal Pages
  { path: 'terms', component: HomeComponent, data: { message: 'Terms of Service' } },
  { path: 'privacy', component: HomeComponent, data: { message: 'Privacy Policy' } },
  { path: 'disclaimer', component: HomeComponent, data: { message: 'Disclaimer' } },
  { path: 'cookies', component: HomeComponent, data: { message: 'Cookie Policy' } },
  { path: 'security', component: HomeComponent, data: { message: 'Security Information' } },
  
  // 6. Authentication Pages
  { path: 'login', loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent) },
  
  // 7. Dynamic Routes (Stock symbols and company details)
  { path: 'company/:symbol', component: CompanyDetailComponent },
  { path: 'stock/:symbol', component: CompanyDetailComponent },
  { 
    path: ':symbol', 
    component: CompanyDetailComponent, 
    canActivate: [isValidSymbolGuard],
    // This route allows direct navigation to stock via /SYMBOL (e.g., /AAPL)
  },
  
  // Fallback route (redirects to home for any undefined routes)
  { path: '**', redirectTo: '' }
];

// Define routing configuration with standard HTML5 routing
const routerConfig: ExtraOptions = {
  useHash: false, // Use standard HTML5 routing instead of hash-based
  scrollPositionRestoration: 'enabled'
};

@NgModule({
  imports: [RouterModule.forRoot(routes, routerConfig)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
