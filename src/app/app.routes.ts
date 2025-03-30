import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { CompanyDetailComponent } from './pages/company-detail/company-detail.component';
import { MarketOverviewComponent } from './pages/market-overview/market-overview.component';
import { IndicesComponent } from './pages/indices/indices.component';

export const routes: Routes = [
  // Core Pages
  { path: '', component: HomeComponent, pathMatch: 'full' },
  { path: 'market-overview', component: MarketOverviewComponent },
  { path: 'indices', component: IndicesComponent },
  { path: 'indices/:name', component: IndicesComponent },
  { path: 'stocks', component: MarketOverviewComponent },
  
  // Feature Pages (Some with placeholders)
  { path: 'portfolio', component: HomeComponent }, // Placeholder until implemented
  { 
    path: 'screener', 
    loadComponent: () => import('./pages/screener/screener.component').then(m => m.ScreenerComponent) 
  },
  { path: 'watchlist', component: HomeComponent }, // Placeholder until implemented
  
  // Strategy Pages
  { 
    path: 'tools', 
    loadComponent: () => import('./pages/tools/toolspage.component').then(m => m.ToolspageComponent) 
  },
  { 
    path: 'tools/swing-trading', 
    loadComponent: () => import('./pages/swing-trading/swing-trading.component').then(m => m.SwingTradingComponent) 
  },
  { 
    path: 'swing-trading', 
    loadComponent: () => import('./pages/swing-trading/swing-trading.component').then(m => m.SwingTradingComponent) 
  },
  
  // Dynamic Routes (Stock symbols and company details)
  { path: 'company/:symbol', component: CompanyDetailComponent },
  { path: 'stock/:symbol', component: CompanyDetailComponent },
  
  // Fallback route (redirects to home for any undefined routes)
  { path: '**', redirectTo: '' }
];