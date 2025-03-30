import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Observable, Subject, of } from 'rxjs';
import { takeUntil, switchMap, catchError, tap } from 'rxjs/operators';
import { StockService } from '@core/services/stock.service';
import { 
  Stock, PriceData, FundamentalData, TradingTerm, 
  TradingTermDetail, PredictionData 
} from '@core/models/stock.model';

@Component({
  selector: 'app-company',
  templateUrl: './company.component.html',
  styleUrls: ['./company.component.scss']
})
export class CompanyComponent implements OnInit, OnDestroy {
  symbol: string = '';
  stockDetails: Stock | null = null;
  priceData: PriceData[] = [];
  fundamentalData: FundamentalData | null = null;
  availableTradingTerms: TradingTermDetail[] = [];
  selectedTradingTerm: TradingTerm = TradingTerm.INTRADAY;
  predictionData: PredictionData | null = null;
  
  isLoadingDetails = true;
  isLoadingPriceData = true;
  isLoadingFundamentals = true;
  isLoadingTechnicals = true;
  isLoadingPredictions = true;

  timeframes = [
    { value: '1d', label: '1 Day' },
    { value: '5d', label: '5 Days' },
    { value: '1mo', label: '1 Month' },
    { value: '3mo', label: '3 Months' },
    { value: '6mo', label: '6 Months' },
    { value: '1y', label: '1 Year' },
    { value: '5y', label: '5 Years' },
    { value: 'max', label: 'Max' }
  ];
  selectedTimeframe = '6mo';

  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private stockService: StockService
  ) { }

  ngOnInit(): void {
    this.route.params.pipe(
      takeUntil(this.destroy$),
      switchMap(params => {
        this.symbol = params['symbol'];
        if (!this.symbol) {
          this.router.navigate(['/']);
          return of(null);
        }
        
        this.isLoadingDetails = true;
        this.isLoadingPriceData = true;
        this.isLoadingFundamentals = true;
        this.isLoadingTechnicals = true;
        this.isLoadingPredictions = true;
        
        // Get available trading terms
        this.stockService.getAvailableTradingTerms(this.symbol)
          .pipe(takeUntil(this.destroy$))
          .subscribe(terms => {
            this.availableTradingTerms = terms;
          });
        
        // Get stock details
        return this.stockService.getStockDetails(this.symbol);
      }),
      tap(details => {
        if (details) {
          this.stockDetails = details;
          this.isLoadingDetails = false;
        }
      }),
      switchMap(() => {
        // Get price data
        return this.stockService.getStockPriceHistory(this.symbol, '1d', this.selectedTimeframe);
      }),
      tap(priceData => {
        this.priceData = priceData;
        this.isLoadingPriceData = false;
      }),
      switchMap(() => {
        // Get fundamental data
        return this.stockService.getFundamentalAnalysis(this.symbol);
      }),
      tap(fundamentalData => {
        this.fundamentalData = fundamentalData;
        this.isLoadingFundamentals = false;
      }),
      switchMap(() => {
        // Get predictions
        return this.stockService.getPricePrediction(this.symbol);
      }),
      catchError(error => {
        console.error('Error loading company data:', error);
        this.isLoadingDetails = false;
        this.isLoadingPriceData = false;
        this.isLoadingFundamentals = false;
        this.isLoadingTechnicals = false;
        this.isLoadingPredictions = false;
        return of(null);
      })
    ).subscribe(predictionData => {
      if (predictionData) {
        this.predictionData = predictionData;
      }
      this.isLoadingPredictions = false;
      this.isLoadingTechnicals = false;
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onTimeframeChange(timeframe: string): void {
    this.selectedTimeframe = timeframe;
    this.isLoadingPriceData = true;
    
    this.stockService.getStockPriceHistory(this.symbol, '1d', timeframe)
      .pipe(takeUntil(this.destroy$))
      .subscribe(priceData => {
        this.priceData = priceData;
        this.isLoadingPriceData = false;
      });
  }

  onTradingTermChange(tradingTerm: TradingTerm): void {
    this.selectedTradingTerm = tradingTerm;
  }
}
