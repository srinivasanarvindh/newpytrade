import { Component, OnInit, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { CommonModule, DecimalPipe, CurrencyPipe } from '@angular/common';
import { Stock } from '../../core/models/stock.model';
import { StockService } from '../../core/services/stock.service';
import { SharedModule } from '../../shared/shared.module';

@Component({
  selector: 'app-screener',
  templateUrl: './screener.component.html',
  styleUrls: ['./screener.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    RouterModule,
    SharedModule
  ],
  providers: [
    DecimalPipe,
    CurrencyPipe
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class ScreenerComponent implements OnInit {
  filterForm: FormGroup;
  results: Stock[] = [];
  filteredResults: Stock[] = [];
  isLoading = false;
  error: string | null = null;
  totalResults = 0;
  currentPage = 1;
  pageSize = 20;
  Math = Math; // Add Math global object reference for the template
  
  // Predefined filters from query params
  presetFilter: string | null = null;

  // Filter options
  marketRegions = [
    { id: 'US', name: 'United States' },
    { id: 'India', name: 'India' },
    { id: 'Europe', name: 'Europe' },
    { id: 'Asia', name: 'Asia' }
  ];

  marketIndices = [
    { id: 'NIFTY 50', name: 'NIFTY 50', region: 'India' },
    { id: 'BSE SENSEX', name: 'BSE SENSEX', region: 'India' },
    { id: 'S&P 500', name: 'S&P 500', region: 'US' },
    { id: 'NASDAQ 100', name: 'NASDAQ 100', region: 'US' },
    { id: 'Dow Jones', name: 'Dow Jones', region: 'US' },
    { id: 'FTSE 100', name: 'FTSE 100', region: 'Europe' },
    { id: 'DAX', name: 'DAX', region: 'Europe' },
    { id: 'Nikkei 225', name: 'Nikkei 225', region: 'Asia' },
    { id: 'Hang Seng', name: 'Hang Seng', region: 'Asia' }
  ];

  sectors = [
    'Technology',
    'Healthcare',
    'Financial Services',
    'Consumer Cyclical',
    'Energy',
    'Consumer Defensive',
    'Industrials',
    'Communication Services',
    'Basic Materials',
    'Real Estate',
    'Utilities'
  ];

  industries: { [sector: string]: string[] } = {
    'Technology': ['Software', 'Semiconductors', 'Hardware', 'IT Services'],
    'Healthcare': ['Biotechnology', 'Pharmaceuticals', 'Medical Devices', 'Healthcare Services'],
    'Financial Services': ['Banks', 'Insurance', 'Asset Management', 'FinTech'],
    'Consumer Cyclical': ['Retail', 'Automotive', 'Entertainment', 'Hospitality'],
    'Energy': ['Oil & Gas', 'Renewable Energy', 'Utilities', 'Mining']
  };

  sortOptions = [
    { field: 'market_cap', name: 'Market Cap', direction: 'desc' },
    { field: 'price', name: 'Price', direction: 'desc' },
    { field: 'change', name: 'Daily Change %', direction: 'desc' },
    { field: 'technical.rsi', name: 'RSI', direction: 'desc' },
    { field: 'fundamental.pe_ratio', name: 'P/E Ratio', direction: 'asc' },
    { field: 'fundamental.dividend_yield', name: 'Dividend Yield', direction: 'desc' },
    { field: 'performance.price_change_1m', name: '1 Month Performance', direction: 'desc' },
    { field: 'prediction.predicted_change', name: 'Predicted Change', direction: 'desc' }
  ];

  constructor(
    private formBuilder: FormBuilder,
    private stockService: StockService,
    private route: ActivatedRoute
  ) {
    this.filterForm = this.formBuilder.group({
      markets: [[]],
      indices: [[]],
      sectors: [[]],
      industries: [[]],
      technical: this.formBuilder.group({
        rsi: this.formBuilder.group({
          min: [null],
          max: [null]
        }),
        macd: this.formBuilder.group({
          crossover: [null]
        }),
        ema: this.formBuilder.group({
          crossover: [null]
        })
      }),
      fundamental: this.formBuilder.group({
        pe_ratio: this.formBuilder.group({
          min: [null],
          max: [null]
        }),
        market_cap: this.formBuilder.group({
          min: [null],
          max: [null]
        }),
        dividend_yield: this.formBuilder.group({
          min: [null],
          max: [null]
        })
      }),
      performance: this.formBuilder.group({
        price_change_1d: this.formBuilder.group({
          min: [null],
          max: [null]
        }),
        price_change_1w: this.formBuilder.group({
          min: [null],
          max: [null]
        }),
        price_change_1m: this.formBuilder.group({
          min: [null],
          max: [null]
        }),
        volume_change_1d: this.formBuilder.group({
          min: [null],
          max: [null]
        })
      }),
      prediction: this.formBuilder.group({
        predicted_change: this.formBuilder.group({
          min: [null],
          max: [null]
        })
      }),
      sort: ['market_cap'],
      sortDirection: ['desc']
    });
  }

  ngOnInit(): void {
    // Get any preset filters from URL query params
    this.route.queryParams.subscribe(params => {
      const filter = params['filter'];
      if (filter) {
        this.presetFilter = filter;
        this.applyPresetFilter(filter);
      } else {
        // If no preset filter, load with default criteria
        this.search();
      }
    });
  }

  applyPresetFilter(filter: string): void {
    // Reset form to default values
    this.filterForm.reset({
      markets: [],
      indices: [],
      sectors: [],
      industries: [],
      sort: 'market_cap',
      sortDirection: 'desc'
    });

    // Apply preset filter based on query param
    switch (filter) {
      case 'gainers':
        this.filterForm.patchValue({
          performance: {
            price_change_1d: {
              min: 1
            }
          },
          sort: 'performance.price_change_1d',
          sortDirection: 'desc'
        });
        break;
      case 'losers':
        this.filterForm.patchValue({
          performance: {
            price_change_1d: {
              max: -1
            }
          },
          sort: 'performance.price_change_1d',
          sortDirection: 'asc'
        });
        break;
      case 'volume':
        this.filterForm.patchValue({
          performance: {
            volume_change_1d: {
              min: 1.5
            }
          },
          sort: 'volume',
          sortDirection: 'desc'
        });
        break;
      case 'rsi-oversold':
        this.filterForm.patchValue({
          technical: {
            rsi: {
              min: 0,
              max: 30
            }
          },
          sort: 'technical.rsi',
          sortDirection: 'asc'
        });
        break;
      case 'rsi-overbought':
        this.filterForm.patchValue({
          technical: {
            rsi: {
              min: 70,
              max: 100
            }
          },
          sort: 'technical.rsi',
          sortDirection: 'desc'
        });
        break;
      case 'dividend':
        this.filterForm.patchValue({
          fundamental: {
            dividend_yield: {
              min: 3
            }
          },
          sort: 'fundamental.dividend_yield',
          sortDirection: 'desc'
        });
        break;
      case 'value':
        this.filterForm.patchValue({
          fundamental: {
            pe_ratio: {
              min: 0,
              max: 15
            }
          },
          sort: 'fundamental.pe_ratio',
          sortDirection: 'asc'
        });
        break;
      case 'growth':
        this.filterForm.patchValue({
          performance: {
            price_change_1m: {
              min: 10
            }
          },
          sort: 'performance.price_change_1m',
          sortDirection: 'desc'
        });
        break;
      case 'ai-prediction':
        this.filterForm.patchValue({
          prediction: {
            predicted_change: {
              min: 5
            }
          },
          sort: 'prediction.predicted_change',
          sortDirection: 'desc'
        });
        break;
    }

    // Execute search with the applied filters
    this.search();
  }

  search(): void {
    this.isLoading = true;
    this.error = null;

    // Prepare filters for API request
    const filters: any = {
      technical: {},
      fundamental: {},
      performance: {},
      prediction: {}
    };

    // Technical indicators
    const rsi = this.filterForm.value.technical?.rsi;
    if (rsi && (rsi.min !== null || rsi.max !== null)) {
      filters.technical.rsi = {};
      if (rsi.min !== null) filters.technical.rsi.min = rsi.min;
      if (rsi.max !== null) filters.technical.rsi.max = rsi.max;
    }

    const macd = this.filterForm.value.technical?.macd;
    if (macd && macd.crossover) {
      filters.technical.macd = { crossover: macd.crossover };
    }

    const ema = this.filterForm.value.technical?.ema;
    if (ema && ema.crossover) {
      filters.technical.ema = { crossover: ema.crossover };
    }

    // Fundamental metrics
    const peRatio = this.filterForm.value.fundamental?.pe_ratio;
    if (peRatio && (peRatio.min !== null || peRatio.max !== null)) {
      filters.fundamental.pe_ratio = {};
      if (peRatio.min !== null) filters.fundamental.pe_ratio.min = peRatio.min;
      if (peRatio.max !== null) filters.fundamental.pe_ratio.max = peRatio.max;
    }

    const marketCap = this.filterForm.value.fundamental?.market_cap;
    if (marketCap && (marketCap.min !== null || marketCap.max !== null)) {
      filters.fundamental.market_cap = {};
      if (marketCap.min !== null) filters.fundamental.market_cap.min = marketCap.min;
      if (marketCap.max !== null) filters.fundamental.market_cap.max = marketCap.max;
    }

    const dividendYield = this.filterForm.value.fundamental?.dividend_yield;
    if (dividendYield && (dividendYield.min !== null || dividendYield.max !== null)) {
      filters.fundamental.dividend_yield = {};
      if (dividendYield.min !== null) filters.fundamental.dividend_yield.min = dividendYield.min;
      if (dividendYield.max !== null) filters.fundamental.dividend_yield.max = dividendYield.max;
    }

    // Sector and industry filters
    if (this.filterForm.value.sectors && this.filterForm.value.sectors.length > 0) {
      filters.fundamental.sector = this.filterForm.value.sectors;
    }

    if (this.filterForm.value.industries && this.filterForm.value.industries.length > 0) {
      filters.fundamental.industry = this.filterForm.value.industries;
    }

    // Performance metrics
    const priceChange1d = this.filterForm.value.performance?.price_change_1d;
    if (priceChange1d && (priceChange1d.min !== null || priceChange1d.max !== null)) {
      filters.performance.price_change_1d = {};
      if (priceChange1d.min !== null) filters.performance.price_change_1d.min = priceChange1d.min;
      if (priceChange1d.max !== null) filters.performance.price_change_1d.max = priceChange1d.max;
    }

    const priceChange1w = this.filterForm.value.performance?.price_change_1w;
    if (priceChange1w && (priceChange1w.min !== null || priceChange1w.max !== null)) {
      filters.performance.price_change_1w = {};
      if (priceChange1w.min !== null) filters.performance.price_change_1w.min = priceChange1w.min;
      if (priceChange1w.max !== null) filters.performance.price_change_1w.max = priceChange1w.max;
    }

    const priceChange1m = this.filterForm.value.performance?.price_change_1m;
    if (priceChange1m && (priceChange1m.min !== null || priceChange1m.max !== null)) {
      filters.performance.price_change_1m = {};
      if (priceChange1m.min !== null) filters.performance.price_change_1m.min = priceChange1m.min;
      if (priceChange1m.max !== null) filters.performance.price_change_1m.max = priceChange1m.max;
    }

    const volumeChange1d = this.filterForm.value.performance?.volume_change_1d;
    if (volumeChange1d && (volumeChange1d.min !== null || volumeChange1d.max !== null)) {
      filters.performance.volume_change_1d = {};
      if (volumeChange1d.min !== null) filters.performance.volume_change_1d.min = volumeChange1d.min;
      if (volumeChange1d.max !== null) filters.performance.volume_change_1d.max = volumeChange1d.max;
    }

    // Prediction metrics
    const predictedChange = this.filterForm.value.prediction?.predicted_change;
    if (predictedChange && (predictedChange.min !== null || predictedChange.max !== null)) {
      filters.prediction.predicted_change = {};
      if (predictedChange.min !== null) filters.prediction.predicted_change.min = predictedChange.min;
      if (predictedChange.max !== null) filters.prediction.predicted_change.max = predictedChange.max;
    }

    // Market and index filters
    const markets = this.filterForm.value.markets || [];
    const indices = this.filterForm.value.indices || [];

    // Sorting options
    const sort = {
      field: this.filterForm.value.sort || 'market_cap',
      direction: this.filterForm.value.sortDirection || 'desc'
    };

    // API request parameters
    const requestParams = {
      filters: filters,
      sort: sort,
      page: this.currentPage,
      limit: this.pageSize,
      markets: markets,
      indices: indices
    };

    // Call screener API
    this.stockService.screenStocks(requestParams).subscribe({
      next: (response) => {
        this.results = response.stocks;
        this.filteredResults = response.stocks;
        this.totalResults = response.total;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error in stock screener:', err);
        this.error = 'Error loading screener results. Please try again.';
        this.isLoading = false;
      }
    });
  }

  resetFilters(): void {
    this.filterForm.reset({
      markets: [],
      indices: [],
      sectors: [],
      industries: [],
      sort: 'market_cap',
      sortDirection: 'desc'
    });
    this.presetFilter = null;
    this.search();
  }

  changePage(page: number): void {
    this.currentPage = page;
    this.search();
  }

  onSortChange(event: any): void {
    // Selected value will be in format 'field|direction'
    const value = event.target.value;
    if (value) {
      const [field, direction] = value.split('|');
      this.filterForm.patchValue({
        sort: field,
        sortDirection: direction
      });
      this.search();
    }
  }

  onMarketChange(event: any): void {
    const selectedMarkets = this.filterForm.value.markets || [];
    
    // Filter indices to show only those from selected markets
    if (selectedMarkets.length > 0) {
      this.marketIndices.filter(index => 
        selectedMarkets.includes(index.region)
      );
    }
  }

  onSectorChange(event: any): void {
    const selectedSectors = this.filterForm.value.sectors || [];
    
    // Clear industries when no sectors are selected
    if (selectedSectors.length === 0) {
      this.filterForm.patchValue({
        industries: []
      });
    }
  }

  getAvailableIndustries(): string[] {
    const selectedSectors = this.filterForm.value.sectors || [];
    if (selectedSectors.length === 0) {
      return [];
    }
    
    let availableIndustries: string[] = [];
    selectedSectors.forEach((sector: string) => {
      if (this.industries[sector]) {
        availableIndustries = availableIndustries.concat(this.industries[sector]);
      }
    });
    
    return availableIndustries;
  }

  // Helper methods for template
  hasEmaData(stock: Stock): boolean {
    return stock.technical?.ema50 !== undefined && stock.technical?.ema200 !== undefined;
  }

  getEmaTrend(stock: Stock): string {
    if (!this.hasEmaData(stock)) return 'N/A';
    
    const ema50 = stock.technical?.ema50;
    const ema200 = stock.technical?.ema200;
    
    if (ema50 !== undefined && ema200 !== undefined) {
      return ema50 > ema200 ? 'Bullish' : 'Bearish';
    }
    
    return 'N/A';
  }

  getPredictionIconClass(stock: Stock): any {
    if (stock.prediction?.predicted_change === undefined) {
      return {};
    }
    
    return {
      'fa-arrow-trend-up': stock.prediction.predicted_change > 0,
      'fa-arrow-trend-down': stock.prediction.predicted_change <= 0
    };
  }
  
  getRsiClass(stock: Stock): any {
    if (stock.technical?.rsi === undefined) {
      return {};
    }
    
    const rsi = stock.technical.rsi;
    
    return {
      'oversold': rsi < 30,
      'overbought': rsi > 70,
      'neutral': rsi >= 30 && rsi <= 70
    };
  }
}