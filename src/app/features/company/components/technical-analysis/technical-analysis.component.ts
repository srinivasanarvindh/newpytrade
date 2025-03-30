import { Component, Input, OnChanges, OnDestroy, OnInit, SimpleChanges } from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { PriceData, TradingSignal, TradingTerm } from '@core/models/stock.model';
import { StockService } from '@core/services/stock.service';

interface TechnicalIndicator {
  name: string;
  value: number | string;
  interpretation: string;
  status: 'bullish' | 'bearish' | 'neutral';
  description: string;
}

@Component({
  selector: 'app-technical-analysis',
  templateUrl: './technical-analysis.component.html',
  styleUrls: ['./technical-analysis.component.scss']
})
export class TechnicalAnalysisComponent implements OnInit, OnChanges, OnDestroy {
  @Input() symbol: string = '';
  @Input() priceData: PriceData[] = [];
  @Input() isLoading: boolean = true;
  @Input() tradingTerm: TradingTerm = TradingTerm.INTRADAY;

  technicalIndicators: TechnicalIndicator[] = [];
  tradingSignal: TradingSignal | null = null;
  
  // RSI Data
  rsiData: any[] = [];
  isLoadingRSI: boolean = true;
  
  // MACD Data
  macdData: any[] = [];
  isLoadingMACD: boolean = true;

  // Overall signal
  overallSignal: 'Buy' | 'Sell' | 'Neutral' = 'Neutral';
  signalStrength: number = 0;
  signalConfidence: 'Low' | 'Medium' | 'High' = 'Medium';

  private destroy$ = new Subject<void>();

  constructor(private stockService: StockService) { }

  ngOnInit(): void {
    this.loadTechnicalData();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['symbol'] || changes['tradingTerm']) && !changes['isLoading']) {
      this.loadTechnicalData();
    }
    
    if (changes['priceData'] && this.priceData && this.priceData.length > 0) {
      this.calculateIndicators();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadTechnicalData(): void {
    if (!this.symbol || this.isLoading) {
      return;
    }

    this.isLoadingRSI = true;
    this.isLoadingMACD = true;
    
    // Get technical indicators from API
    this.stockService.getTechnicalIndicators(this.symbol, ['rsi', 'macd'])
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          if (data && data.rsi) {
            this.rsiData = data.rsi.map((item: any) => ({
              date: new Date(item.date),
              value: item.value
            }));
            this.isLoadingRSI = false;
          }
          
          if (data && data.macd) {
            this.macdData = data.macd.map((item: any) => ({
              date: new Date(item.date),
              macd: item.macd,
              signal: item.signal,
              histogram: item.histogram
            }));
            this.isLoadingMACD = false;
          }
          
          this.calculateIndicators();
        },
        error: (error) => {
          console.error('Error loading technical indicators:', error);
          this.isLoadingRSI = false;
          this.isLoadingMACD = false;
          
          // Generate mock data based on price data for the demo
          if (this.priceData && this.priceData.length > 0) {
            this.generateDemoIndicatorData();
          }
        }
      });
      
    // Get trading signal
    this.stockService.getTradingSignal(this.symbol, this.tradingTerm)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (signal) => {
          this.tradingSignal = signal;
          this.updateOverallSignal();
        },
        error: (error) => {
          console.error('Error loading trading signal:', error);
          // Set default signal
          this.tradingSignal = {
            signal: 'Neutral',
            score: 50,
            indicators: {
              'momentum': 'Neutral',
              'trend': 'Neutral',
              'volatility': 'Neutral'
            }
          };
          this.updateOverallSignal();
        }
      });
  }

  private calculateIndicators(): void {
    if (!this.priceData || this.priceData.length === 0) {
      return;
    }
    
    const lastPrice = this.priceData[this.priceData.length - 1];
    const lastRSI = this.rsiData.length > 0 ? this.rsiData[this.rsiData.length - 1].value : null;
    const lastMACD = this.macdData.length > 0 ? this.macdData[this.macdData.length - 1] : null;
    
    this.technicalIndicators = [];
    
    // RSI
    if (lastRSI !== null) {
      let rsiStatus: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      let rsiInterpretation = 'Neutral';
      
      if (lastRSI < 30) {
        rsiStatus = 'bullish';
        rsiInterpretation = 'Oversold';
      } else if (lastRSI > 70) {
        rsiStatus = 'bearish';
        rsiInterpretation = 'Overbought';
      }
      
      this.technicalIndicators.push({
        name: 'RSI (14)',
        value: lastRSI.toFixed(2),
        interpretation: rsiInterpretation,
        status: rsiStatus,
        description: 'Relative Strength Index measures the speed and magnitude of price movements.'
      });
    }
    
    // MACD
    if (lastMACD !== null) {
      let macdStatus: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      let macdInterpretation = 'Neutral';
      
      if (lastMACD.macd > lastMACD.signal) {
        macdStatus = 'bullish';
        macdInterpretation = 'Bullish Crossover';
      } else if (lastMACD.macd < lastMACD.signal) {
        macdStatus = 'bearish';
        macdInterpretation = 'Bearish Crossover';
      }
      
      this.technicalIndicators.push({
        name: 'MACD',
        value: lastMACD.macd.toFixed(2),
        interpretation: macdInterpretation,
        status: macdStatus,
        description: 'Moving Average Convergence Divergence shows the relationship between two moving averages.'
      });
    }
    
    // Calculate Simple Moving Averages
    const sma20 = this.calculateSMA(20);
    const sma50 = this.calculateSMA(50);
    const sma200 = this.calculateSMA(200);
    
    // SMA 20
    if (sma20 !== null) {
      const currentPrice = lastPrice.close;
      let smaStatus: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      let smaInterpretation = 'Neutral';
      
      if (currentPrice > sma20) {
        smaStatus = 'bullish';
        smaInterpretation = 'Price Above SMA';
      } else if (currentPrice < sma20) {
        smaStatus = 'bearish';
        smaInterpretation = 'Price Below SMA';
      }
      
      this.technicalIndicators.push({
        name: 'SMA (20)',
        value: sma20.toFixed(2),
        interpretation: smaInterpretation,
        status: smaStatus,
        description: '20-day Simple Moving Average helps identify the trend direction.'
      });
    }
    
    // SMA 50
    if (sma50 !== null) {
      const currentPrice = lastPrice.close;
      let smaStatus: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      let smaInterpretation = 'Neutral';
      
      if (currentPrice > sma50) {
        smaStatus = 'bullish';
        smaInterpretation = 'Price Above SMA';
      } else if (currentPrice < sma50) {
        smaStatus = 'bearish';
        smaInterpretation = 'Price Below SMA';
      }
      
      this.technicalIndicators.push({
        name: 'SMA (50)',
        value: sma50.toFixed(2),
        interpretation: smaInterpretation,
        status: smaStatus,
        description: '50-day Simple Moving Average helps identify medium-term trend direction.'
      });
    }
    
    // SMA 200
    if (sma200 !== null) {
      const currentPrice = lastPrice.close;
      let smaStatus: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      let smaInterpretation = 'Neutral';
      
      if (currentPrice > sma200) {
        smaStatus = 'bullish';
        smaInterpretation = 'Price Above SMA';
      } else if (currentPrice < sma200) {
        smaStatus = 'bearish';
        smaInterpretation = 'Price Below SMA';
      }
      
      this.technicalIndicators.push({
        name: 'SMA (200)',
        value: sma200.toFixed(2),
        interpretation: smaInterpretation,
        status: smaStatus,
        description: '200-day Simple Moving Average helps identify long-term trend direction.'
      });
    }
    
    // Calculate ATR (Average True Range)
    const atr = this.calculateATR(14);
    if (atr !== null) {
      this.technicalIndicators.push({
        name: 'ATR (14)',
        value: atr.toFixed(2),
        interpretation: 'Volatility Indicator',
        status: 'neutral',
        description: 'Average True Range measures market volatility.'
      });
    }
    
    this.updateOverallSignal();
  }
  
  private calculateSMA(period: number): number | null {
    if (!this.priceData || this.priceData.length < period) {
      return null;
    }
    
    const prices = this.priceData.slice(-period).map(item => item.close);
    const sum = prices.reduce((acc, price) => acc + price, 0);
    return sum / period;
  }
  
  private calculateATR(period: number): number | null {
    if (!this.priceData || this.priceData.length < period + 1) {
      return null;
    }
    
    const trueRanges = [];
    
    for (let i = 1; i < this.priceData.length; i++) {
      const high = this.priceData[i].high;
      const low = this.priceData[i].low;
      const prevClose = this.priceData[i - 1].close;
      
      const tr1 = high - low;
      const tr2 = Math.abs(high - prevClose);
      const tr3 = Math.abs(low - prevClose);
      
      trueRanges.push(Math.max(tr1, tr2, tr3));
    }
    
    const lastTRs = trueRanges.slice(-period);
    const sum = lastTRs.reduce((acc, tr) => acc + tr, 0);
    return sum / period;
  }
  
  private updateOverallSignal(): void {
    if (!this.tradingSignal) {
      this.overallSignal = 'Neutral';
      this.signalStrength = 50;
      this.signalConfidence = 'Low';
      return;
    }
    
    // Calculate overall signal based on trading signal and technical indicators
    let bullishCount = 0;
    let bearishCount = 0;
    let totalCount = 0;
    
    // Count technical indicators sentiment
    this.technicalIndicators.forEach(indicator => {
      if (indicator.status === 'bullish') bullishCount++;
      if (indicator.status === 'bearish') bearishCount++;
      totalCount++;
    });
    
    // Add trading signal weight (higher weight than individual indicators)
    if (this.tradingSignal.signal === 'Buy') bullishCount += 2;
    if (this.tradingSignal.signal === 'Sell') bearishCount += 2;
    totalCount += 2;
    
    // Calculate signal strength (0-100)
    this.signalStrength = Math.round((bullishCount / (totalCount || 1)) * 100);
    
    // Determine overall signal
    if (this.signalStrength > 65) {
      this.overallSignal = 'Buy';
    } else if (this.signalStrength < 35) {
      this.overallSignal = 'Sell';
    } else {
      this.overallSignal = 'Neutral';
    }
    
    // Determine confidence level
    const confidenceScore = Math.abs(this.signalStrength - 50) * 2;
    if (confidenceScore > 70) {
      this.signalConfidence = 'High';
    } else if (confidenceScore > 40) {
      this.signalConfidence = 'Medium';
    } else {
      this.signalConfidence = 'Low';
    }
  }
  
  private generateDemoIndicatorData(): void {
    if (!this.priceData || this.priceData.length === 0) {
      return;
    }
    
    // Generate demo RSI data
    this.rsiData = this.priceData.map((item, index) => {
      // Simple RSI simulation based on price movement
      const baseRSI = 50;
      const priceChange = index > 0 ? item.close - this.priceData[index - 1].close : 0;
      const rsiChange = priceChange * 5; // Scale factor
      const rsiValue = Math.max(0, Math.min(100, baseRSI + rsiChange));
      
      return {
        date: item.date,
        value: rsiValue
      };
    });
    this.isLoadingRSI = false;
    
    // Generate demo MACD data
    const ema12 = this.calculateEMA(12);
    const ema26 = this.calculateEMA(26);
    
    this.macdData = this.priceData.map((item, index) => {
      const macdValue = ema12[index] - ema26[index];
      const signalValue = this.calculateSignalLine(9, index, ema12, ema26);
      
      return {
        date: item.date,
        macd: macdValue,
        signal: signalValue,
        histogram: macdValue - signalValue
      };
    });
    this.isLoadingMACD = false;
    
    this.calculateIndicators();
  }
  
  private calculateEMA(period: number): number[] {
    if (!this.priceData || this.priceData.length === 0) {
      return [];
    }
    
    const prices = this.priceData.map(item => item.close);
    const k = 2 / (period + 1);
    const ema = [prices[0]];
    
    for (let i = 1; i < prices.length; i++) {
      ema.push(prices[i] * k + ema[i - 1] * (1 - k));
    }
    
    return ema;
  }
  
  private calculateSignalLine(period: number, index: number, ema12: number[], ema26: number[]): number {
    if (index < period) {
      return ema12[index] - ema26[index];
    }
    
    const macdValues = [];
    for (let i = index - period + 1; i <= index; i++) {
      macdValues.push(ema12[i] - ema26[i]);
    }
    
    const sum = macdValues.reduce((acc, value) => acc + value, 0);
    return sum / period;
  }
}
