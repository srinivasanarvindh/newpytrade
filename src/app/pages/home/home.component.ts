import { Component, OnInit } from '@angular/core';
import { StockService } from '../../core/services/stock.service';
import { IndexData, MarketNews, Stock } from '../../core/models/stock.model';
import { Observable, of, map, forkJoin } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { DecimalPipe, DatePipe } from '@angular/common';
import { StockSearchComponent } from '../../shared/components/stock-search/stock-search.component';
import { TopStocksTableComponent } from './top-stocks-table.component';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    LoadingSpinnerComponent,
    DecimalPipe,
    DatePipe,
    StockSearchComponent,
    TopStocksTableComponent
  ]
})
export class HomeComponent implements OnInit {
  // Data properties
  indices$: Observable<IndexData[]> = of([]);
  filteredIndices: IndexData[] = []; 
  marketNews: MarketNews[] = [];
  
  // Top stocks by market
  topNseStocks: Stock[] = [];
  topBseStocks: Stock[] = [];
  topNasdaqStocks: Stock[] = [];
  topNyseStocks: Stock[] = [];
  topFtseStocks: Stock[] = [];
  topDaxStocks: Stock[] = [];
  topNikkeiStocks: Stock[] = [];
  topShcompStocks: Stock[] = [];
  
  // State properties
  isLoadingIndices = true;
  isLoadingNews = true;
  isLoadingNseStocks = true;
  isLoadingBseStocks = true;
  isLoadingNasdaqStocks = true;
  isLoadingNyseStocks = true;
  isLoadingFtseStocks = true;
  isLoadingDaxStocks = true;
  isLoadingNikkeiStocks = true;
  isLoadingShcompStocks = true;
  indicesError: string | null = null;
  newsError: string | null = null;
  nseStocksError: string | null = null;
  bseStocksError: string | null = null;
  nasdaqStocksError: string | null = null;
  nyseStocksError: string | null = null;
  ftseStocksError: string | null = null;
  daxStocksError: string | null = null;
  nikkeiStocksError: string | null = null;
  shcompStocksError: string | null = null;
  
  // Market sentiment properties
  marketSentiment: 'bullish' | 'bearish' | 'neutral' = 'neutral';
  lastUpdated: Date = new Date();
  
  // Region selection
  selectedRegion: 'global' | 'india' | 'us_americas' | 'europe' | 'asia_pacific' | 'middle_east' | 'australia' = 'global';
  
  // Region-specific indices
  regionIndices: Record<string, string[]> = {
    'global': [
      'NIFTY 50',
      'BSE SENSEX',
      'Dow Jones Industrial Average',
      'S&P 500',
      'Nasdaq Composite',
      'FTSE 100',
      'DAX 30',
      'Nikkei 225'
    ],
    'india': [
      'NIFTY 50',
      'BSE SENSEX', 
      'NIFTY BANK',
      'NIFTY MIDCAP 50',
      'NIFTY SMALLCAP 50',
      'NIFTY IT',
      'NIFTY Pharma',
      'NIFTY Auto'
    ],
    'us_americas': [
      // US indices
      'Dow Jones Industrial Average',
      'S&P 500',
      'Nasdaq Composite',
      'Russell 2000',
      'NYSE Composite',
      'Dow Jones Transportation',
      'Philadelphia Semiconductor',
      // Americas indices
      'Bovespa',
      'TSX Composite Index',
      'IPC Mexico',
      'S&P/BMV IPC',
      'S&P Merval',
      'S&P/CLX IPSA',
      'S&P/BVL Peru General',
      'Colcap',
      'S&P/TSX Venture Composite'
    ],
    'europe': [
      'FTSE 100',
      'DAX 30',
      'CAC 40',
      'Euro Stoxx 50',
      'IBEX 35',
      'FTSE MIB',
      'Swiss Market Index'
    ],
    'asia_pacific': [
      'Nikkei 225',
      'Topix Index',
      'Hang Seng Index',
      'Shanghai Composite Index',
      'Shenzhen Composite Index',
      'Kospi Index',
      'Taiwan Weighted Index',
      'Straits Times Index',
      'SET Index', 
      'Jakarta Composite Index',
      'KLCI',
      'PSEi',
      'Colombo All Share Index',
      'SG Straits Times Index',
      'VN-Index',
      'CSE All-Share'
    ],
    'middle_east': [
      'Tadawul All Share Index',
      'Dubai Financial Market General Index',
      'Abu Dhabi Securities Exchange Index',
      'Qatar Exchange Index',
      'Bahrain All Share Index',
      'Muscat Securities Market Index',
      'Kuwait Stock Exchange Index'
    ],
    // 'americas' region is now merged with 'us' into 'us_americas'
    'australia': [
      'ASX 200',
      'All Ordinaries Index',
      'S&P/ASX 50',
      'S&P/ASX 300',
      'NZX 50'
    ]
  };
  
  // Featured indices (used as fallback)
  featuredIndices: string[] = [
    'NIFTY 50',
    'BSE SENSEX',
    'Dow Jones Industrial Average',
    'S&P 500',
    'Nasdaq Composite',
    'FTSE 100',
    'DAX 30',
    'Nikkei 225',
    'Hang Seng Index',
    'Shanghai Composite Index',
    'Tadawul All Share Index',
    'Bovespa',
    'ASX 200'
  ];

  /**
   * Coming Soon Message Property
   * 
   * This property stores a message that is displayed when the user navigates to a route
   * that is under development. The message is passed from the route data in app-routing.module.ts
   * via the 'message' property. When a message is present, the regular home page content is
   * hidden and replaced with a "coming soon" message UI.
   * 
   * @see HomeComponent.ngOnInit - Where the route data is checked for a message
   * @see home.component.html - Where the UI conditionally shows the coming soon message
   */
  comingSoonMessage: string | null = null;

constructor(
  private stockService: StockService,
  private route: ActivatedRoute
) { }

  /**
   * Component Initialization
   * 
   * This method is called when the component is initialized.
   * It performs the following tasks:
   * 1. Loads market indices data
   * 2. Loads market news data
   * 3. Loads top stocks for different markets
   * 4. Calculates the overall market sentiment based on indices
   * 5. Checks route data for any "coming soon" message to display
   * 
   * If a "coming soon" message is found in the route data, it will
   * be displayed instead of the regular home page content.
   */
  ngOnInit(): void {
    this.loadIndices();
    this.loadMarketNews();
    this.loadTopStocksByMarket();
    this.calculateMarketSentiment();
    
    // Check if we're on a "coming soon" page (placeholder route)
    this.route.data.subscribe(data => {
      if (data['message']) {
        this.comingSoonMessage = data['message'];
      }
    });
  }
  
  /**
   * Load top stocks for different markets
   * 
   * This method loads the top performing stocks for NSE, BSE, NASDAQ, and NYSE
   * It uses parallel requests with forkJoin to load all data efficiently
   */
  loadTopStocksByMarket(): void {
    // Set all loading states to true
    this.isLoadingNseStocks = true;
    this.isLoadingBseStocks = true;
    this.isLoadingNasdaqStocks = true;
    this.isLoadingNyseStocks = true;
    this.isLoadingFtseStocks = true;
    this.isLoadingDaxStocks = true;
    this.isLoadingNikkeiStocks = true;
    this.isLoadingShcompStocks = true;
    
    // Load top NSE stocks
    this.stockService.getTopStocksByMarket('nse', 10).subscribe({
      next: (stocks) => {
        this.topNseStocks = stocks;
        this.isLoadingNseStocks = false;
      },
      error: (error) => {
        console.error('Failed to load top NSE stocks', error);
        this.nseStocksError = 'Failed to load top NSE stocks';
        this.isLoadingNseStocks = false;
      }
    });
    
    // Load top BSE stocks
    this.stockService.getTopStocksByMarket('bse', 10).subscribe({
      next: (stocks) => {
        this.topBseStocks = stocks;
        this.isLoadingBseStocks = false;
      },
      error: (error) => {
        console.error('Failed to load top BSE stocks', error);
        this.bseStocksError = 'Failed to load top BSE stocks';
        this.isLoadingBseStocks = false;
      }
    });
    
    // Load top NASDAQ stocks
    this.stockService.getTopStocksByMarket('nasdaq', 10).subscribe({
      next: (stocks) => {
        this.topNasdaqStocks = stocks;
        this.isLoadingNasdaqStocks = false;
      },
      error: (error) => {
        console.error('Failed to load top NASDAQ stocks', error);
        this.nasdaqStocksError = 'Failed to load top NASDAQ stocks';
        this.isLoadingNasdaqStocks = false;
      }
    });
    
    // Load top NYSE stocks
    this.stockService.getTopStocksByMarket('nyse', 10).subscribe({
      next: (stocks) => {
        this.topNyseStocks = stocks;
        this.isLoadingNyseStocks = false;
      },
      error: (error) => {
        console.error('Failed to load top NYSE stocks', error);
        this.nyseStocksError = 'Failed to load top NYSE stocks';
        this.isLoadingNyseStocks = false;
      }
    });
    
    // Load top FTSE stocks
    this.stockService.getTopStocksByMarket('ftse', 10).subscribe({
      next: (stocks) => {
        this.topFtseStocks = stocks;
        this.isLoadingFtseStocks = false;
      },
      error: (error) => {
        console.error('Failed to load top FTSE stocks', error);
        this.ftseStocksError = 'Failed to load top FTSE stocks';
        this.isLoadingFtseStocks = false;
      }
    });
    
    // Load top DAX stocks
    this.stockService.getTopStocksByMarket('dax', 10).subscribe({
      next: (stocks) => {
        this.topDaxStocks = stocks;
        this.isLoadingDaxStocks = false;
      },
      error: (error) => {
        console.error('Failed to load top DAX stocks', error);
        this.daxStocksError = 'Failed to load top DAX stocks';
        this.isLoadingDaxStocks = false;
      }
    });
    
    // Load top Nikkei stocks
    this.stockService.getTopStocksByMarket('nikkei', 10).subscribe({
      next: (stocks) => {
        this.topNikkeiStocks = stocks;
        this.isLoadingNikkeiStocks = false;
      },
      error: (error) => {
        console.error('Failed to load top Nikkei stocks', error);
        this.nikkeiStocksError = 'Failed to load top Nikkei stocks';
        this.isLoadingNikkeiStocks = false;
      }
    });
    
    // Load top Shanghai Composite stocks
    this.stockService.getTopStocksByMarket('shcomp', 10).subscribe({
      next: (stocks) => {
        this.topShcompStocks = stocks;
        this.isLoadingShcompStocks = false;
      },
      error: (error) => {
        console.error('Failed to load top Shanghai Composite stocks', error);
        this.shcompStocksError = 'Failed to load top Shanghai Composite stocks';
        this.isLoadingShcompStocks = false;
      }
    });
  }

  loadIndices(): void {
    this.isLoadingIndices = true;
    this.indices$ = this.stockService.getIndices().pipe(
      tap(indices => {
        this.processIndices(indices);
        this.isLoadingIndices = false;
      }),
      catchError(error => {
        console.error('Failed to load indices', error);
        this.indicesError = 'Failed to load market indices';
        this.isLoadingIndices = false;
        return of([]);
      })
    );
  }
  
  processIndices(indices: IndexData[]): void {
    // Filter indices based on selected region
    this.filterIndicesByRegion(indices);
    
    // Calculate market sentiment based on all indices
    this.calculateMarketSentiment();
    
    // Update the last updated timestamp
    this.lastUpdated = new Date();
  }
  
  filterIndicesByRegion(indices: IndexData[]): void {
    const regionSpecificIndices = this.regionIndices[this.selectedRegion] || this.featuredIndices;
    
    this.filteredIndices = indices.filter(index => 
      regionSpecificIndices.includes(index.name)
    );
    
    // If we don't have enough indices for the region, use the featured ones as fallback
    if (this.filteredIndices.length < 3) {
      this.filteredIndices = indices.filter(index => 
        this.featuredIndices.includes(index.name)
      );
    }
  }
  
  calculateMarketSentiment(): void {
    // This would ideally be calculated based on multiple factors
    // For now, we'll use a simple rule based on the available indices
    
    let positiveCount = 0;
    let negativeCount = 0;
    
    this.indices$.subscribe(indices => {
      indices.forEach(index => {
        if (index.change >= 0) {
          positiveCount++;
        } else {
          negativeCount++;
        }
      });
      
      // Calculate sentiment based on the ratio
      const totalIndices = indices.length;
      if (totalIndices > 0) {
        const positiveRatio = positiveCount / totalIndices;
        
        if (positiveRatio >= 0.6) {
          this.marketSentiment = 'bullish';
        } else if (positiveRatio <= 0.4) {
          this.marketSentiment = 'bearish';
        } else {
          this.marketSentiment = 'neutral';
        }
      }
    });
  }
  
  changeRegion(region: 'global' | 'india' | 'us_americas' | 'europe' | 'asia_pacific' | 'middle_east' | 'australia'): void {
    this.selectedRegion = region;
    
    // Re-filter the indices based on the new region
    this.indices$.subscribe(indices => {
      this.filterIndicesByRegion(indices);
    });
  }

  loadMarketNews(): void {
    // Mock market news for now - in a real app, this would come from an API
    this.isLoadingNews = true;
    setTimeout(() => {
      this.marketNews = [
        {
          title: 'Market Recap: Stocks Rally as Tech Leads Gains',
          date: new Date().toISOString(),
          source: 'Financial Times',
          url: '#',
          summary: 'Tech stocks led the market higher as investors assessed the latest economic data.'
        },
        {
          title: 'Central Bank Maintains Interest Rates',
          date: new Date().toISOString(),
          source: 'Wall Street Journal',
          url: '#',
          summary: 'The central bank decided to keep interest rates unchanged in its latest policy meeting.'
        },
        {
          title: 'Global Markets: Asian Stocks Mixed, Europe Opens Higher',
          date: new Date().toISOString(),
          source: 'Bloomberg',
          url: '#',
          summary: 'Asian stocks were mixed while European markets opened higher amid improving economic indicators.'
        }
      ];
      this.isLoadingNews = false;
    }, 1000);
  }
  
  /**
   * Safely determine if a stock's change is positive
   * This helper method handles potential undefined/null values
   */
  isChangePositive(stock: Stock): boolean {
    return (stock.change ?? 0) >= 0;
  }
  
  /**
   * Get the appropriate class for the stock change
   */
  getChangeClass(stock: Stock): string {
    return this.isChangePositive(stock) ? 'positive' : 'negative';
  }
  
  /**
   * Get the appropriate icon for the stock change
   */
  getChangeIcon(stock: Stock): string {
    return this.isChangePositive(stock) ? 'fa-caret-up' : 'fa-caret-down';
  }
}
