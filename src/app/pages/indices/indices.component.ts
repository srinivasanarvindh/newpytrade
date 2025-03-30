import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { StockService } from '../../core/services/stock.service';
import { IndexData, Stock, PriceData, StockData } from '../../core/models/stock.model';
import { Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { StockChartComponent } from '../../shared/components/stock-chart/stock-chart.component';

@Component({
  selector: 'app-indices',
  templateUrl: './indices.component.html',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    LoadingSpinnerComponent,
    StockChartComponent
  ],
  styleUrls: ['./indices.component.scss']
})
export class IndicesComponent implements OnInit {
  indices$: Observable<IndexData[]> = of([]);
  selectedIndex: IndexData | null = null;
  indexConstituents: Stock[] = [];
  
  isLoadingIndices = true;
  isLoadingConstituents = false;
  isLoadingChart = false;
  
  indicesError: string | null = null;
  constituentsError: string | null = null;
  chartError: string | null = null;
  
  selectedRegion: 'global' | 'india' | 'us_americas' | 'europe' | 'asia_pacific' | 'middle_east' | 'australia' = 'global';
  searchTerm: string = '';
  
  // Chart data properties
  indexPriceData: PriceData[] = [];
  selectedTimeframe: '1d' | '1w' | '1m' | 'ytd' | '1y' = '1m';
  chartType: 'area' | 'line' | 'candlestick' = 'area';
  
  // Define the major indices per region
  regionIndices: Record<string, string[]> = {
    global: [
      // Global selection of major indices from all regions
      'NIFTY 50', 'BSE SENSEX', 'Dow Jones Industrial Average', 'S&P 500', 'Nasdaq Composite', 
      'FTSE 100', 'DAX 30', 'CAC 40', 'Nikkei 225', 'Hang Seng Index', 'Shanghai Composite Index',
      'Tadawul All Share Index', 'Dubai Financial Market General Index', 'Bovespa', 'ASX 200',
      'Straits Times Index', 'Taiwan Weighted Index'
    ],
    
    india: [
      // Indian indices
      'BSE Sensex', 'NIFTY 50', 'NIFTY BANK', 'NIFTY MIDCAP 50', 'NIFTY SMALLCAP 50',
      'S&P BSE - 100', 'S&P BSE - 200', 'S&P BSE Midcap', 'Nifty Next 50', 
      'Nifty 500', 'Nifty VIX', 'GIFT Nifty', 'NIFTY IT', 'NIFTY Auto', 'NIFTY Pharma'
    ],
    
    us_americas: [
      // US indices
      'Dow Jones Industrial Average', 'S&P 500', 'Nasdaq Composite', 'Russell 2000',
      'Dow Jones Transportation', 'NYSE Composite', 'NYSE FANG+', 'Wilshire 5000',
      'Philadelphia Semiconductor',
      // Americas indices
      'Bovespa', // Brazil
      'TSX Composite Index', // Canada
      'Merval Index', // Argentina
      'IPC Mexico', // Mexico
      'S&P/TSX Venture Composite' // Canada
    ],
    
    europe: [
      // Europe indices as specified
      'FTSE 100', // United Kingdom
      'DAX 30', // Germany
      'CAC 40', // France
      'IBEX 35', // Spain
      'FTSE MIB', // Italy
      'Euro Stoxx 50', // Eurozone
      'AEX Index', // Netherlands
      'OMX Stockholm 30', // Sweden
      'Swiss Market Index' // Switzerland
    ],
    
    asia_pacific: [
      // Asia-Pacific indices as specified
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
      'KLCI', // Malaysia (Kuala Lumpur Composite Index)
      'PSEi', // Philippines
      'Colombo All Share Index' // Sri Lanka
    ],
    
    middle_east: [
      // Middle East indices as specified
      'Tadawul All Share Index', // Saudi Arabia
      'Dubai Financial Market General Index', // UAE (Dubai)
      'Abu Dhabi Securities Exchange Index', // UAE (Abu Dhabi)
      'Qatar Exchange Index', // Qatar
      'Bahrain All Share Index', // Bahrain
      'Muscat Securities Market Index', // Oman
      'Kuwait Stock Exchange Index' // Kuwait
    ],
    
    australia: [
      // Australia and New Zealand indices
      'ASX 200', // Australia
      'All Ordinaries Index', // Australia
      'S&P/ASX 50', // Australia
      'S&P/ASX 300', // Australia
      'NZX 50' // New Zealand
    ]
  };

  constructor(
    private stockService: StockService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit(): void {
    // Check if we have a route parameter for the index name
    this.route.paramMap.subscribe(params => {
      const indexName = params.get('name');
      if (indexName) {
        // If we have an index name, we'll load the indices and then select the right one
        this.loadIndices(indexName);
      } else {
        // If no index name is provided, just load all indices
        this.loadIndices();
      }
    });
  }

  loadIndices(indexNameToSelect?: string): void {
    this.isLoadingIndices = true;
    this.indices$ = this.stockService.getIndices().pipe(
      catchError(error => {
        console.error('Failed to load indices', error);
        this.indicesError = 'Failed to load market indices';
        this.isLoadingIndices = false;
        return of([]);
      })
    );

    this.indices$.subscribe({
      next: (indices) => {
        this.isLoadingIndices = false;
        
        if (indexNameToSelect) {
          // Find the index with the matching name
          const indexToSelect = indices.find(index => index.name === indexNameToSelect);
          if (indexToSelect) {
            // Determine which region this index belongs to
            for (const [region, indexNames] of Object.entries(this.regionIndices)) {
              if (indexNames.includes(indexToSelect.name)) {
                // Handle mapping of old region values to new ones
                let mappedRegion = region;
                if (region === 'us' || region === 'americas') {
                  mappedRegion = 'us_americas';
                } else if (region === 'asia') {
                  mappedRegion = 'asia_pacific';
                }
                this.selectedRegion = mappedRegion as 'global' | 'india' | 'us_americas' | 'europe' | 'asia_pacific' | 'middle_east' | 'australia';
                break;
              }
            }
            // Select the index
            this.selectIndex(indexToSelect);
          } else {
            // If the requested index is not found, fall back to the first available
            if (indices.length > 0) {
              this.selectIndex(indices[0]);
            }
          }
        } else if (indices.length > 0 && !this.selectedIndex) {
          // Auto-select first index if none is selected
          this.selectIndex(indices[0]);
        }
      },
      error: () => {
        this.isLoadingIndices = false;
        this.indicesError = 'Failed to load market indices';
      }
    });
  }

  selectIndex(index: IndexData): void {
    this.selectedIndex = index;
    this.loadConstituents(index.name);
    this.loadIndexHistoricalData(index.name);
  }
  
  loadIndexHistoricalData(indexName: string, forceRefresh: boolean = false): void {
    this.isLoadingChart = true;
    this.chartError = null;
    this.indexPriceData = [];
    
    // Map Angular timeframe format to API timeframe format
    let apiTimeframe: string;
    switch (this.selectedTimeframe) {
      case '1d': apiTimeframe = '1d'; break;
      case '1w': apiTimeframe = '1w'; break;
      case '1m': apiTimeframe = '1m'; break;
      case 'ytd': apiTimeframe = 'ytd'; break;
      case '1y': apiTimeframe = '1y'; break;
      default: apiTimeframe = '1m';
    }
    
    console.log(`Loading historical data for ${indexName} with timeframe ${apiTimeframe}`);
    
    try {
      this.stockService.getIndexHistory(indexName, apiTimeframe, forceRefresh).subscribe({
        next: (data) => {
          console.log(`Successfully loaded chart data for ${indexName}`, data);
          
          if (data && data.priceData && Array.isArray(data.priceData)) {
            this.indexPriceData = data.priceData;
          } else {
            console.warn(`Invalid price data format received for ${indexName}`, data);
            this.chartError = 'Invalid data format received from the server';
            // Fall back to sample data if needed
            this.generateSampleChartData(indexName, this.selectedTimeframe);
          }
          
          this.isLoadingChart = false;
        },
        error: (error) => {
          console.error(`Error loading chart data for ${indexName}`, error);
          this.chartError = `Failed to load chart data for ${indexName}`;
          this.isLoadingChart = false;
          
          // If we couldn't get real data, use the sample data generator as a fallback
          this.generateSampleChartData(indexName, this.selectedTimeframe);
        }
      });
    } catch (e) {
      console.error(`Exception caught while trying to load chart data for ${indexName}`, e);
      this.chartError = `An unexpected error occurred loading chart data for ${indexName}`;
      this.isLoadingChart = false;
      
      // Use sample data as a last resort
      this.generateSampleChartData(indexName, this.selectedTimeframe);
    }
  }
  
  changeTimeframe(timeframe: '1d' | '1w' | '1m' | 'ytd' | '1y'): void {
    this.selectedTimeframe = timeframe;
    if (this.selectedIndex) {
      this.loadIndexHistoricalData(this.selectedIndex.name);
    }
  }
  
  changeChartType(type: 'area' | 'line' | 'candlestick'): void {
    this.chartType = type;
  }
  
  // Generate sample chart data until we have an API endpoint
  private generateSampleChartData(indexName: string, timeframe: '1d' | '1w' | '1m' | 'ytd' | '1y'): void {
    const today = new Date();
    const data: PriceData[] = [];
    
    // Get current value from selected index
    const baseValue = this.selectedIndex?.value || 1000;
    
    // Determine number of data points based on timeframe
    let days = 30; // Default to 1 month
    switch (timeframe) {
      case '1d': days = 1; break;
      case '1w': days = 7; break;
      case '1m': days = 30; break;
      case 'ytd': {
        const yearStart = new Date(today.getFullYear(), 0, 1);
        days = Math.floor((today.getTime() - yearStart.getTime()) / (1000 * 60 * 60 * 24));
        break;
      }
      case '1y': days = 365; break;
    }
    
    // Generate data points
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      // Random variation factor
      const variationPercentage = 0.02; // 2% max variation
      const randomFactor = (Math.random() * 2 - 1) * variationPercentage;
      
      // Trending factor - add a slight upward or downward trend
      const trendFactor = (this.selectedIndex?.change || 0) > 0 ? 0.0001 : -0.0001;
      const dayFactor = (days - i) * trendFactor;
      
      // Calculate day's price with variation
      const dayValue = baseValue * (1 + randomFactor + dayFactor);
      
      // Create price data entry
      const priceData: PriceData = {
        date: date.toISOString().split('T')[0],
        open: dayValue * (1 - Math.random() * 0.005),
        high: dayValue * (1 + Math.random() * 0.01),
        low: dayValue * (1 - Math.random() * 0.01),
        close: dayValue,
        volume: Math.floor(Math.random() * 10000000) + 1000000
      };
      
      data.push(priceData);
    }
    
    this.indexPriceData = data;
  }

  refreshConstituents(): void {
    if (this.selectedIndex) {
      console.log(`Refreshing constituents for ${this.selectedIndex.name}`);
      this.loadConstituents(this.selectedIndex.name, true);
      // Also refresh chart data
      this.loadIndexHistoricalData(this.selectedIndex.name, true);
    }
  }

  loadConstituents(indexName: string, forceRefresh: boolean = false): void {
    this.isLoadingConstituents = true;
    this.constituentsError = null;
    this.indexConstituents = []; // Clear previous constituents
    
    console.log(`Attempting to load constituents for ${indexName}, forceRefresh: ${forceRefresh}`);
    
    // Add error handling around the service call
    try {
      this.stockService.getIndexConstituents(indexName, forceRefresh).subscribe({
        next: (constituents) => {
          console.log(`Successfully loaded ${constituents.length} constituents for ${indexName}`);
          this.indexConstituents = constituents;
          this.isLoadingConstituents = false;
        },
        error: (error) => {
          console.error(`Error loading constituents for ${indexName}`, error);
          this.constituentsError = `Failed to load constituents for ${indexName}`;
          this.isLoadingConstituents = false;
        }
      });
    } catch (e) {
      console.error(`Exception caught while trying to load constituents for ${indexName}`, e);
      this.constituentsError = `An unexpected error occurred loading constituents for ${indexName}`;
      this.isLoadingConstituents = false;
    }
  }

  changeRegion(region: 'global' | 'india' | 'us_americas' | 'europe' | 'asia_pacific' | 'middle_east' | 'australia'): void {
    this.selectedRegion = region;
    // Reset selected index
    this.selectedIndex = null;
    
    // In a real app, we might reload the indices based on region
    // Here we'll just use the already loaded indices
    this.indices$.subscribe(indices => {
      const regionIndices = indices.filter(index => this.regionIndices[region].includes(index.name));
      if (regionIndices.length > 0) {
        this.selectIndex(regionIndices[0]);
      }
    });
  }

  get filteredConstituents(): Stock[] {
    if (!this.searchTerm) return this.indexConstituents;
    
    const term = this.searchTerm.toLowerCase();
    return this.indexConstituents.filter(stock => 
      stock.symbol.toLowerCase().includes(term) || 
      (stock.company && stock.company.toLowerCase().includes(term))
    );
  }

  trackBySymbol(index: number, item: Stock): string {
    return item.symbol;
  }
}
