import { Component, OnInit } from '@angular/core';
import { StockService } from '../../core/services/stock.service';
import { IndexData, Stock, MarketNews } from '../../core/models/stock.model';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { DecimalPipe, DatePipe } from '@angular/common';

@Component({
  selector: 'app-market-overview',
  templateUrl: './market-overview.component.html',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    LoadingSpinnerComponent,
    DecimalPipe,
    DatePipe
  ],
  styleUrls: ['./market-overview.component.scss']
})
export class MarketOverviewComponent implements OnInit {
  indices$: Observable<IndexData[]> = of([]);
  topGainers: Stock[] = [];
  topLosers: Stock[] = [];
  marketNews: MarketNews[] = [];
  
  isLoadingIndices = true;
  isLoadingGainers = true;
  isLoadingLosers = true;
  isLoadingNews = true;
  
  indicesError: string | null = null;
  gainersError: string | null = null;
  losersError: string | null = null;
  newsError: string | null = null;
  
  // Market sentiment indicator
  marketSentiment: 'bullish' | 'bearish' | 'neutral' = 'neutral';
  lastUpdated: Date = new Date();
  
  // Indices grouped by region for display
  indicesByRegion: Record<string, Record<string, string[]>> = {
    global: {
      'US MARKETS': [
        'Dow Jones Industrial Average', 'S&P 500', 'Nasdaq Composite'
      ],
      'EUROPEAN MARKETS': [
        'FTSE 100', 'DAX 30', 'CAC 40', 'Euro Stoxx 50'
      ],
      'ASIAN MARKETS': [
        'NIFTY 50', 'BSE SENSEX', 'Nikkei 225', 'Hang Seng Index', 
        'Shanghai Composite Index', 'Kospi Index', 'Taiwan Weighted Index',
        'S&P/ASX 200'
      ],
      'MIDDLE EAST MARKETS': [
        'Tadawul All Share Index', 'Dubai Financial Market General Index', 
        'Abu Dhabi Securities Exchange Index'
      ],
      'AMERICAS MARKETS': [
        'Bovespa', 'TSX Composite Index', 'IPC Mexico'
      ]
    },
    india: {
      'INDIAN MARKETS': [
        'NIFTY 50', 'BSE SENSEX', 'NIFTY BANK', 'NIFTY MIDCAP 50', 'NIFTY SMALLCAP 50',
        'S&P BSE - 100', 'S&P BSE - 200', 'S&P BSE Midcap', 'NIFTY Next 50', 
        'NIFTY 500', 'Nifty VIX', 'GIFT Nifty', 'NIFTY IT', 'NIFTY Auto', 'NIFTY Pharma'
      ]
    },
    us: {
      'US MARKETS': [
        'Dow Jones Industrial Average', 'S&P 500', 'Nasdaq Composite', 'Russell 2000',
        'Dow Jones Futures', 'S&P 500 CFD', 'Nasdaq CFD', 'NYSE Composite',
        'Dow Jones Transportation', 'Philadelphia Semiconductor', 'NYSE FANG+', 'Wilshire 5000'
      ],
      'CANADA MARKETS': [
        'TSX Composite Index', 'S&P/TSX Venture Composite'
      ]
    },
    europe: {
      'MAJOR EUROPEAN INDICES': [
        'FTSE 100', 'DAX 30', 'CAC 40', 'Euro Stoxx 50', 'IBEX 35'
      ],
      'WESTERN EUROPE': [
        'FTSE MIB', 'Swiss Market Index', 'AEX Index'
      ],
      'NORTHERN EUROPE': [
        'OMX Stockholm 30', 'OMX Copenhagen 20', 'Oslo OBX'
      ],
      'EASTERN & SOUTHERN EUROPE': [
        'MOEX Russia', 'BEL 20', 'Athens General'
      ]
    },
    asia: {
      'JAPAN': [
        'Nikkei 225', 'Topix Index'
      ],
      'CHINA & HONG KONG': [
        'Hang Seng Index', 'Shanghai Composite Index', 
        'Shenzhen Composite Index', 'SSE 50 Index'
      ],
      'KOREA & TAIWAN': [
        'Kospi Index', 'Taiwan Weighted Index'
      ],
      'INDIA': [
        'NIFTY 50', 'BSE SENSEX'
      ],
      'SOUTHEAST ASIA': [
        'Straits Times Index', 'SET Index', 'Jakarta Composite Index',
        'KLCI', 'PSEi', 'Colombo All Share Index'
      ]
    },
    middle_east: {
      'SAUDI ARABIA': [
        'Tadawul All Share Index'
      ],
      'UAE': [
        'Dubai Financial Market General Index', 'Abu Dhabi Securities Exchange Index'
      ],
      'QATAR & BAHRAIN': [
        'Qatar Exchange Index', 'Bahrain All Share Index'
      ],
      'OTHER MIDDLE EAST': [
        'Muscat Securities Market Index', 'Kuwait Stock Exchange Index'
      ]
    },
    americas: {
      'NORTH AMERICA': [
        'Dow Jones Industrial Average', 'S&P 500', 'Nasdaq Composite', 
        'TSX Composite Index', 'S&P/TSX Venture Composite'
      ],
      'BRAZIL': [
        'Bovespa'
      ],
      'OTHER LATIN AMERICA': [
        'IPC Mexico', 'Merval Index', 'S&P/BMV IPC', 
        'S&P Merval', 'S&P/CLX IPSA', 'S&P/BVL Peru General', 'Colcap'
      ]
    },
    australia: {
      'AUSTRALIA': [
        'ASX 200', 'All Ordinaries Index', 'S&P/ASX 50', 'S&P/ASX 300'
      ],
      'NEW ZEALAND': [
        'NZX 50'
      ]
    }
  };
  
  // Updated to use the new region names
  featuredIndices: Record<string, string[]> = {
    global: [
      'NIFTY 50', 'BSE SENSEX', 'Dow Jones Industrial Average', 'S&P 500', 'Nasdaq Composite', 
      'FTSE 100', 'DAX 30', 'CAC 40', 'Nikkei 225', 'Hang Seng Index', 'Shanghai Composite Index',
      'Straits Times Index', 'Taiwan Weighted Index', 'Kospi Index', 'SET Index', 'Jakarta Composite Index',
      'Tadawul All Share Index', 'Dubai Financial Market General Index', 'Bovespa', 'TSX Composite Index'
    ],
    india: [
      'NIFTY 50', 'BSE SENSEX', 'NIFTY BANK', 'NIFTY MIDCAP 50', 'NIFTY SMALLCAP 50', 
      'S&P BSE - 100', 'S&P BSE - 200', 'S&P BSE Midcap', 'NIFTY Next 50', 
      'NIFTY 500', 'Nifty VIX', 'GIFT Nifty', 'NIFTY IT', 'NIFTY Auto', 'NIFTY Pharma'
    ],
    us_americas: [
      'Dow Jones Industrial Average', 'S&P 500', 'Nasdaq Composite', 'Russell 2000',
      'Dow Jones Transportation', 'NYSE Composite', 'NYSE FANG+', 'Wilshire 5000',
      'Philadelphia Semiconductor', 'Bovespa', 'TSX Composite Index', 'Merval Index', 
      'IPC Mexico', 'S&P/TSX Composite', 'S&P/BMV IPC', 'S&P Merval', 
      'S&P/CLX IPSA', 'S&P/BVL Peru General', 'Colcap', 'S&P/TSX Venture Composite'
    ],
    europe: [
      'FTSE 100', 'DAX 30', 'CAC 40', 'Euro Stoxx 50', 'IBEX 35', 'FTSE MIB', 
      'Swiss Market Index', 'AEX Index', 'OMX Stockholm 30'
    ],
    asia_pacific: [
      'Nikkei 225', 'Topix Index', 'Hang Seng Index', 'Shanghai Composite Index', 
      'Shenzhen Composite Index', 'Taiwan Weighted Index', 'Kospi Index', 'NIFTY 50', 
      'BSE SENSEX', 'Straits Times Index', 'SET Index', 'Jakarta Composite Index',
      'KLCI', 'PSEi', 'Colombo All Share Index'
    ],
    middle_east: [
      'Tadawul All Share Index', 'Dubai Financial Market General Index', 'Abu Dhabi Securities Exchange Index',
      'Qatar Exchange Index', 'Bahrain All Share Index', 'Muscat Securities Market Index', 'Kuwait Stock Exchange Index'
    ],
    australia: [
      'ASX 200', 'All Ordinaries Index', 'S&P/ASX 50', 'S&P/ASX 300', 'NZX 50'
    ]
  };
  
  selectedRegion: 'global' | 'india' | 'us_americas' | 'europe' | 'asia_pacific' | 'middle_east' | 'australia' = 'global';

  constructor(private stockService: StockService) { 
    // Update the featured indices for each region based on the complete list
    this.updateRegionalIndices();
  }
  
  /**
   * Updates the indices lists for each region based on the complete list provided
   */
  private updateRegionalIndices(): void {
    // Update Middle East indices
    this.featuredIndices['middle_east'] = [
      'Tadawul All Share Index', // Saudi Arabia
      'Dubai Financial Market General Index', // UAE (Dubai)
      'Abu Dhabi Securities Exchange Index', // UAE (Abu Dhabi)
      'Qatar Exchange Index', // Qatar
      'Bahrain All Share Index', // Bahrain
      'Muscat Securities Market Index', // Oman
      'Kuwait Stock Exchange Index' // Kuwait
    ];
    
    // Update Europe indices
    this.featuredIndices['europe'] = [
      'FTSE 100', // United Kingdom
      'DAX 30', // Germany
      'CAC 40', // France
      'IBEX 35', // Spain
      'FTSE MIB', // Italy
      'Euro Stoxx 50', // Eurozone
      'AEX Index', // Netherlands
      'OMX Stockholm 30', // Sweden
      'Swiss Market Index' // Switzerland
    ];
    
    // Update US & Americas indices
    this.featuredIndices['us_americas'] = [
      'Dow Jones Industrial Average', // US
      'S&P 500', // US
      'Nasdaq Composite', // US
      'Russell 2000', // US
      'Bovespa', // Brazil
      'TSX Composite Index', // Canada
      'Merval Index', // Argentina
      'IPC Mexico', // Mexico
      'S&P/TSX Venture Composite' // Canada
    ];
    
    // Update Asia-Pacific indices
    this.featuredIndices['asia_pacific'] = [
      'Nikkei 225', // Japan
      'Topix Index', // Japan
      'Hang Seng Index', // Hong Kong
      'Shanghai Composite Index', // China
      'Shenzhen Composite Index', // China
      'Kospi Index', // South Korea
      'ASX 200', // Australia
      'SSE 50 Index', // China
      'Straits Times Index', // Singapore
      'Taiwan Weighted Index', // Taiwan
      'SET Index', // Thailand
      'Jakarta Composite Index', // Indonesia
      'KLCI', // Malaysia
      'PSEi', // Philippines
      'Colombo All Share Index' // Sri Lanka
    ];
    
    // Update Australia indices
    this.featuredIndices['australia'] = [
      'ASX 200',
      'All Ordinaries Index',
      'S&P/ASX 50',
      'S&P/ASX 300',
      'NZX 50' // New Zealand
    ];
    
    // Update Global with a mix of all regions
    this.featuredIndices['global'] = [
      // Top global indices
      'NIFTY 50', 'BSE SENSEX', 
      'Dow Jones Industrial Average', 'S&P 500', 'Nasdaq Composite',
      'FTSE 100', 'DAX 30', 'CAC 40', 
      'Nikkei 225', 'Hang Seng Index', 'Shanghai Composite Index',
      'Tadawul All Share Index',
      'Bovespa',
      'ASX 200',
      'Straits Times Index'
    ];
  }

  ngOnInit(): void {
    this.loadIndices();
    this.loadTopGainers();
    this.loadTopLosers();
    this.loadMarketNews();
    this.calculateMarketSentiment();
  }

  loadIndices(): void {
    this.isLoadingIndices = true;
    this.indices$ = this.stockService.getIndices().pipe(
      catchError(error => {
        console.error('Failed to load indices', error);
        this.indicesError = 'Failed to load market indices. Please try again later.';
        this.isLoadingIndices = false;
        return of([]);
      })
    );

    this.indices$.subscribe({
      next: (indices) => {
        this.isLoadingIndices = false;
        this.lastUpdated = new Date();
        this.calculateMarketSentiment();
      },
      error: () => {
        this.isLoadingIndices = false;
        this.indicesError = 'Failed to load market indices. Please try again later.';
      }
    });
  }

  loadTopGainers(): void {
    // In a real app, this would be a proper API call
    this.isLoadingGainers = true;
    setTimeout(() => {
      this.topGainers = [
        { symbol: 'AAPL', company: 'Apple Inc.', changePercent: 4.25 },
        { symbol: 'MSFT', company: 'Microsoft Corporation', changePercent: 3.82 },
        { symbol: 'GOOGL', company: 'Alphabet Inc.', changePercent: 3.14 },
        { symbol: 'AMZN', company: 'Amazon.com Inc.', changePercent: 2.95 },
        { symbol: 'TSLA', company: 'Tesla Inc.', changePercent: 2.63 },
      ];
      this.isLoadingGainers = false;
    }, 1000);
  }

  loadTopLosers(): void {
    // In a real app, this would be a proper API call
    this.isLoadingLosers = true;
    setTimeout(() => {
      this.topLosers = [
        { symbol: 'META', company: 'Meta Platforms Inc.', changePercent: -3.18 },
        { symbol: 'NFLX', company: 'Netflix Inc.', changePercent: -2.74 },
        { symbol: 'DIS', company: 'The Walt Disney Company', changePercent: -2.45 },
        { symbol: 'INTC', company: 'Intel Corporation', changePercent: -2.12 },
        { symbol: 'IBM', company: 'International Business Machines', changePercent: -1.87 },
      ];
      this.isLoadingLosers = false;
    }, 1500);
  }

  loadMarketNews(): void {
    // In a real app, this would be a proper API call
    this.isLoadingNews = true;
    setTimeout(() => {
      this.marketNews = [
        {
          title: 'Fed Signals Potential Rate Cut in Coming Months',
          date: new Date().toISOString(),
          source: 'Financial Times',
          url: '#',
          summary: 'The Federal Reserve has indicated it may be prepared to cut interest rates in the coming months as inflation shows signs of easing.'
        },
        {
          title: 'Tech Stocks Rally Amid Positive Earnings Reports',
          date: new Date().toISOString(),
          source: 'Wall Street Journal',
          url: '#',
          summary: 'Technology stocks surged following better-than-expected earnings reports from several major companies in the sector.'
        },
        {
          title: 'Oil Prices Stabilize After Recent Volatility',
          date: new Date().toISOString(),
          source: 'Bloomberg',
          url: '#',
          summary: 'Crude oil prices have stabilized after a period of significant volatility, providing relief to energy markets and related stocks.'
        },
        {
          title: 'Asian Markets Mixed as Economic Data Shows Uneven Recovery',
          date: new Date().toISOString(),
          source: 'Reuters',
          url: '#',
          summary: 'Asian stock markets showed mixed results as recent economic data points to an uneven recovery across different regional economies.'
        }
      ];
      this.isLoadingNews = false;
    }, 1200);
  }

  calculateMarketSentiment(): void {
    // In a real app, this would be calculated based on actual market data
    // For demonstration, we'll just use a random value
    const random = Math.random();
    if (random > 0.66) {
      this.marketSentiment = 'bullish';
    } else if (random > 0.33) {
      this.marketSentiment = 'neutral';
    } else {
      this.marketSentiment = 'bearish';
    }
  }

  changeRegion(region: 'global' | 'india' | 'us_americas' | 'europe' | 'asia_pacific' | 'middle_east' | 'australia'): void {
    this.selectedRegion = region;
    // In a real application, we would reload the data based on the selected region
    this.loadIndices();
    this.loadTopGainers();
    this.loadTopLosers();
  }

  trackBySymbol(index: number, item: Stock): string {
    return item.symbol;
  }

  trackByTitle(index: number, item: MarketNews): string {
    return item.title;
  }
}
