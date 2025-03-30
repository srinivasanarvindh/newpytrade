import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { StockService } from '../../core/services/stock.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { 
  CompanyDetails, 
  StockData, 
  TechnicalIndicators, 
  FundamentalData,
  PredictionData
} from '../../core/models/stock.model';
import { Observable, forkJoin, of, Subject, Subscription } from 'rxjs';
import { catchError, switchMap, tap, takeUntil } from 'rxjs/operators';
import { Title } from '@angular/platform-browser';
import { CommonModule, DecimalPipe, DatePipe } from '@angular/common';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { ChartComponent } from '../../shared/components/chart/chart.component';
import { TechnicalAnalysisComponent } from './components/technical-analysis/technical-analysis.component';
import { FundamentalAnalysisComponent } from './components/fundamental-analysis/fundamental-analysis.component';
import { PredictionComponent } from './components/prediction/prediction.component';
import { BreadcrumbComponent } from '../../shared/components/breadcrumb/breadcrumb.component';
import { LivePriceComponent } from '../../shared/components/live-price/live-price.component';
import { SharedModule } from '../../shared/shared.module';

@Component({
  selector: 'app-company-detail',
  templateUrl: './company-detail.component.html',
  styleUrls: ['./company-detail.component.scss'],
  standalone: true,
  styles: [`
    .error-box {
      margin: 20px 0;
      padding: 15px;
      border-radius: 4px;
      background-color: #ffefef;
      border: 1px solid #f8d7d7;
      color: #d32f2f;
    }
    .error-message {
      color: #d32f2f;
      font-weight: 500;
    }
    .tab-pane {
      display: block;
      width: 100%;
      margin-top: 20px;
    }
    .tab-content {
      display: block;
      width: 100%;
    }
  `],
  imports: [
    CommonModule,
    RouterModule,
    LoadingSpinnerComponent,
    ChartComponent,
    TechnicalAnalysisComponent,
    FundamentalAnalysisComponent,
    PredictionComponent,
    BreadcrumbComponent,
    DecimalPipe,
    DatePipe,
    LivePriceComponent,
    SharedModule
  ]
})
export class CompanyDetailComponent implements OnInit, OnDestroy {
  symbol!: string;
  companyDetails: CompanyDetails | null = null;
  stockData: StockData | null = null;
  technicalIndicators: TechnicalIndicators | null = null;
  fundamentalData: FundamentalData | null = null;
  predictionData: PredictionData | null = null;
  shortTermSignal: any = null;
  stockNews: any[] = [];
  
  isLoading = true;
  dataError: string | null = null;
  livePriceAvailable = false;
  
  private websocketSubscription?: Subscription;
  
  activeTab: 'overview' | 'technical' | 'fundamental' | 'prediction' = 'overview';
  selectedTimeframe: string = '1m';
  selectedChartType: 'line' | 'candlestick' | 'ohlc' | 'bar' = 'line';
  selectedTradingView: 'intraday' | 'swing' | 'scalping' | 'positional' | 'longterm' | 'options' | 'ai' = 'intraday';
  
  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private stockService: StockService,
    private webSocketService: WebSocketService,
    private titleService: Title
  ) { }

  ngOnInit(): void {
    // Subscribe to WebSocket connection status
    this.websocketSubscription = this.webSocketService.connectionStatus$.subscribe(
      connected => {
        console.log(`WebSocket connection status: ${connected ? 'Connected' : 'Disconnected'}`);
        this.livePriceAvailable = connected;
      }
    );
    
    this.route.paramMap.pipe(
      switchMap(params => {
        // Get symbol from either the :symbol param or from the route path
        this.symbol = params.get('symbol') || this.route.snapshot.url[0].path;
        
        if (!this.symbol) {
          this.dataError = 'Invalid stock symbol';
          this.isLoading = false;
          return of(null);
        }
        
        // Set a loading title
        this.titleService.setTitle(`Loading ${this.symbol} | PyTrade`);
        
        // Load all data in parallel
        return forkJoin({
          companyDetails: this.stockService.getCompanyDetails(this.symbol).pipe(
            catchError(err => {
              console.error('Error fetching company details', err);
              return of(null);
            })
          ),
          stockData: this.stockService.getStockData(this.symbol, this.selectedTimeframe).pipe(
            catchError(err => {
              console.error('Error fetching stock data', err);
              return of(null);
            })
          ),
          technicalIndicators: this.stockService.getTechnicalIndicators(this.symbol).pipe(
            catchError(err => {
              console.error('Error fetching technical indicators', err);
              return of(null);
            })
          ),
          fundamentalData: this.stockService.getFundamentalData(this.symbol).pipe(
            catchError(err => {
              console.error('Error fetching fundamental data', err);
              return of(null);
            })
          ),
          predictionData: this.stockService.getPredictionData(this.symbol).pipe(
            catchError(err => {
              console.error('Error fetching prediction data', err);
              return of(null);
            })
          ),
          shortTermSignal: this.stockService.getShortTermSignal(this.symbol).pipe(
            catchError(err => {
              console.error('Error fetching short term signal', err);
              return of(null);
            })
          ),
          stockNews: this.stockService.getStockNews(this.symbol).pipe(
            catchError(err => {
              console.error('Error fetching stock news', err);
              return of([]);
            })
          )
        });
      }),
      takeUntil(this.destroy$),
      tap(result => {
        if (!result) {
          this.dataError = 'Failed to load data';
          return;
        }
        
        console.log('Company data received:', result);
        
        // Process company details
        this.companyDetails = result.companyDetails;
        if (this.companyDetails) {
          console.log(`Company details for ${this.symbol}:`, this.companyDetails);
        } else {
          console.warn(`No company details received for ${this.symbol}`);
        }
        
        // Process stock data
        this.stockData = result.stockData;
        if (this.stockData) {
          console.log(`Stock data for ${this.symbol}:`, {
            symbol: this.stockData.symbol,
            exchange: this.stockData.exchange,
            currency: this.stockData.currency,
            totalPrices: this.stockData.prices?.length || 0
          });
        } else {
          console.warn(`No stock data received for ${this.symbol}`);
        }
        
        // Process other data
        this.technicalIndicators = result.technicalIndicators;
        console.log(`Technical indicators for ${this.symbol}:`, this.technicalIndicators);
        
        this.fundamentalData = result.fundamentalData;
        console.log(`Fundamental data for ${this.symbol}:`, this.fundamentalData);
        
        this.predictionData = result.predictionData;
        console.log(`Prediction data for ${this.symbol}:`, this.predictionData);
        
        this.shortTermSignal = result.shortTermSignal;
        console.log(`Short term signal for ${this.symbol}:`, this.shortTermSignal);
        
        // Process news data
        this.stockNews = result.stockNews || [];
        console.log(`News for ${this.symbol}:`, this.stockNews);
        
        // Update page title with appropriate exchange & currency info
        if (this.companyDetails?.name) {
          let titleSuffix = `(${this.symbol})`;
          
          // Add exchange info if available
          if (this.companyDetails.exchange) {
            titleSuffix += ` ${this.companyDetails.exchange}`;
          }
          
          // Add currency info if available and different from USD
          if (this.companyDetails.currency && this.companyDetails.currency !== 'USD') {
            titleSuffix += ` ${this.companyDetails.currency}`;
          }
          
          this.titleService.setTitle(`${this.companyDetails.name} ${titleSuffix} | PyTrade`);
        } else {
          this.titleService.setTitle(`${this.symbol} | PyTrade`);
        }
      })
    ).subscribe({
      next: () => {
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error in company detail component', error);
        this.dataError = 'An error occurred while loading data';
        this.isLoading = false;
      }
    });
  }

  // Navigation method for templates
  navigateToHome(): void {
    this.router.navigate(['/']);
  }

  changeTab(tab: 'overview' | 'technical' | 'fundamental' | 'prediction'): void {
    console.log(`Tab changing from ${this.activeTab} to ${tab}`);
    this.activeTab = tab;
    console.log(`Tab changed, current state:`, {
      tab: this.activeTab,
      technicalIndicators: this.technicalIndicators ? 'Available' : 'Not available',
      fundamentalData: this.fundamentalData ? 'Available' : 'Not available',
      predictionData: this.predictionData ? 'Available' : 'Not available'
    });
  }

  changeTimeframe(timeframe: string): void {
    this.selectedTimeframe = timeframe;
    this.isLoading = true;
    
    this.stockService.getStockData(this.symbol, timeframe)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
      next: (data) => {
        this.stockData = data;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error fetching stock data for timeframe', error);
        this.dataError = 'Failed to load stock data for the selected timeframe';
        this.isLoading = false;
      }
    });
  }
  
  changeChartType(chartType: 'line' | 'candlestick' | 'ohlc' | 'bar'): void {
    console.log(`Changing chart type from ${this.selectedChartType} to ${chartType}`);
    this.selectedChartType = chartType;
  }

  changeTradingView(view: 'intraday' | 'swing' | 'scalping' | 'positional' | 'longterm' | 'options' | 'ai'): void {
    this.selectedTradingView = view;
    this.isLoading = true;
    
    // Change timeframe based on the selected trading view
    let timeframe = '1d';
    
    switch(view) {
      case 'intraday':
        timeframe = '1d';
        break;
      case 'swing':
        timeframe = '1w';
        break;
      case 'scalping':
        timeframe = '1d';
        break;
      case 'positional':
        timeframe = '1m';
        break;
      case 'longterm':
        timeframe = '1y';
        break;
      case 'options':
        timeframe = '1m';
        break;
      case 'ai':
        timeframe = '3m';
        break;
    }
    
    // Update timeframe and refresh data
    this.selectedTimeframe = timeframe;
    
    // Load stock data with new timeframe
    this.stockService.getStockData(this.symbol, timeframe)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.stockData = data;
          
          // Refresh technical indicators
          this.stockService.getTechnicalIndicators(this.symbol)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
              next: (indicators) => {
                this.technicalIndicators = indicators;
                this.isLoading = false;
                
                // Switch to technical analysis tab when changing trading view
                this.activeTab = 'technical';
              },
              error: (error) => {
                console.error('Error fetching technical indicators for trading view', error);
                this.isLoading = false;
                this.activeTab = 'technical';
              }
            });
        },
        error: (error) => {
          console.error('Error fetching stock data for trading view', error);
          this.dataError = 'Failed to load stock data for the selected trading view';
          this.isLoading = false;
          this.activeTab = 'technical';
        }
      });
  }
  
  ngOnDestroy(): void {
    // Clean up WebSocket subscription
    if (this.websocketSubscription) {
      this.websocketSubscription.unsubscribe();
    }
    
    this.destroy$.next();
    this.destroy$.complete();
  }
}
