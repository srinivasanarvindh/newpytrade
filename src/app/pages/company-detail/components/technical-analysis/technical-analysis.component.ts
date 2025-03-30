import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { StockData, TechnicalIndicators } from '../../../../core/models/stock.model';
import { CommonModule, DecimalPipe, TitleCasePipe } from '@angular/common';
import { ChartComponent } from '../../../../shared/components/chart/chart.component';

@Component({
  selector: 'app-technical-analysis',
  templateUrl: './technical-analysis.component.html',
  styleUrls: ['./technical-analysis.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ChartComponent,
    DecimalPipe,
    TitleCasePipe
  ]
})
export class TechnicalAnalysisComponent implements OnChanges {
  @Input() stockData: StockData | null = null;
  @Input() technicalIndicators: TechnicalIndicators | null = null;
  @Input() tradingView: 'intraday' | 'swing' | 'scalping' | 'positional' | 'longterm' | 'options' | 'ai' = 'intraday';
  
  signalAnalysis = {
    trend: 'neutral',
    strength: 0,
    summary: ''
  };
  
  indicatorSignals: {
    indicator: string;
    value: number | null;
    signal: 'buy' | 'sell' | 'neutral';
    description: string;
  }[] = [];
  
  supportResistanceLevels: {
    type: 'support' | 'resistance';
    level: number;
    strength: 'weak' | 'medium' | 'strong';
  }[] = [];
  
  chartType: 'line' | 'candlestick' = 'candlestick';
  chartTimeframe: string = '1d';
  
  // Thresholds for indicator signals
  thresholds = {
    rsi: {
      oversold: 30,
      overbought: 70
    },
    macd: {
      positive: 0
    }
  };

  constructor() { }

  ngOnChanges(changes: SimpleChanges): void {
    console.log('Technical Analysis received data:', {
      stockData: this.stockData ? 'Available' : 'Not available',
      technicalIndicators: this.technicalIndicators ? 'Available' : 'Not available',
      tradingView: this.tradingView
    });
    
    if (this.technicalIndicators) {
      console.log('Technical Indicators Details:', JSON.stringify(this.technicalIndicators));
    } else {
      console.warn('No technical indicators available, will use fallback values');
    }
    
    // Create default objects if needed to prevent errors
    if (!this.stockData) {
      console.warn('No stock data available');
    }
    
    try {
      // Initialize with safe defaults even if data is missing
      this.analyzeIndicators();
      this.calculateSupportResistanceLevels();
      this.updateChartPreferences();
    } catch (error) {
      console.error('Error in technical analysis calculations:', error);
      // Set fallback values to ensure component renders
      this.signalAnalysis = {
        trend: 'neutral',
        strength: 50,
        summary: 'Unable to analyze technical indicators due to an error.'
      };
      
      this.supportResistanceLevels = [];
      
      this.indicatorSignals = [{
        indicator: 'Error',
        value: null,
        signal: 'neutral',
        description: 'An error occurred while analyzing technical data.'
      }];
    }
    
    console.log('Technical Analysis calculated:', {
      indicatorSignals: this.indicatorSignals.length > 0 ? 'Generated' : 'None',
      supportResistanceLevels: this.supportResistanceLevels.length > 0 ? 'Generated' : 'None',
      signalAnalysis: this.signalAnalysis
    });
    
    // Ensure we have some default signal analysis if nothing else available
    if (!this.indicatorSignals.length) {
      this.indicatorSignals = [{
        indicator: 'Market Status',
        value: null,
        signal: 'neutral',
        description: 'Insufficient technical data available. Consider fundamental metrics or other information sources.'
      }];
    }
  }

  analyzeIndicators(): void {
    // Reset signals
    this.indicatorSignals = [];
    
    if (!this.technicalIndicators) {
      console.warn('No technical indicators available. Setting default neutral signal.');
      this.signalAnalysis = {
        trend: 'neutral',
        strength: 50,
        summary: 'Insufficient technical data available. Consider using fundamental analysis or other metrics.'
      };
      return;
    }
    
    console.log('Processing technical indicators:', this.technicalIndicators);
    
    try {
      // RSI
      const rsiSignal = this.getRsiSignal(this.technicalIndicators.rsi);
      this.indicatorSignals.push({
        indicator: 'RSI',
        value: this.technicalIndicators.rsi,
        signal: rsiSignal.signal,
        description: rsiSignal.description
      });
      
      // MACD
      const macdSignal = this.getMacdSignal(
        this.technicalIndicators.macd, 
        this.technicalIndicators.signal, 
        this.technicalIndicators.histogram
      );
      this.indicatorSignals.push({
        indicator: 'MACD',
        value: this.technicalIndicators.histogram,
        signal: macdSignal.signal,
        description: macdSignal.description
      });
      
      // Moving Averages
      const maSignal = this.getMovingAverageSignal(
        this.technicalIndicators.ema50, 
        this.technicalIndicators.ema200, 
        this.technicalIndicators.sma50, 
        this.technicalIndicators.sma200
      );
      this.indicatorSignals.push({
        indicator: 'Moving Averages',
        value: null,
        signal: maSignal.signal,
        description: maSignal.description
      });
      
      // Bollinger Bands
      if (this.stockData && this.stockData.prices.length > 0) {
        const latestPrice = this.stockData.prices[this.stockData.prices.length - 1].close;
        const bbSignal = this.getBollingerBandsSignal(
          latestPrice,
          this.technicalIndicators.upperBollingerBand,
          this.technicalIndicators.lowerBollingerBand
        );
        this.indicatorSignals.push({
          indicator: 'Bollinger Bands',
          value: null,
          signal: bbSignal.signal,
          description: bbSignal.description
        });
      }
      
      // Calculate overall trend based on all signals
      this.calculateOverallSignal();
      
    } catch (error) {
      console.error('Error processing technical indicators:', error);
      // Set fallback neutral values if processing fails
      this.signalAnalysis = {
        trend: 'neutral',
        strength: 50,
        summary: 'Error processing technical indicators. Please try refreshing the page or selecting a different trading view.'
      };
      
      // Add a generic indicator for error state
      this.indicatorSignals = [{
        indicator: 'System Status',
        value: null,
        signal: 'neutral',
        description: 'Technical indicators could not be processed. Data may be incomplete or unavailable.'
      }];
    }
  }

  getRsiSignal(rsi: number): { signal: 'buy' | 'sell' | 'neutral', description: string } {
    if (rsi < this.thresholds.rsi.oversold) {
      return {
        signal: 'buy',
        description: `RSI is oversold at ${rsi.toFixed(2)}, indicating a potential buying opportunity.`
      };
    } else if (rsi > this.thresholds.rsi.overbought) {
      return {
        signal: 'sell',
        description: `RSI is overbought at ${rsi.toFixed(2)}, indicating a potential selling opportunity.`
      };
    } else {
      return {
        signal: 'neutral',
        description: `RSI is at ${rsi.toFixed(2)}, indicating neutral market conditions.`
      };
    }
  }

  getMacdSignal(macd: number, signal: number, histogram: number): { signal: 'buy' | 'sell' | 'neutral', description: string } {
    if (macd > signal && histogram > 0) {
      return {
        signal: 'buy',
        description: 'MACD is above signal line and histogram is positive, indicating bullish momentum.'
      };
    } else if (macd < signal && histogram < 0) {
      return {
        signal: 'sell',
        description: 'MACD is below signal line and histogram is negative, indicating bearish momentum.'
      };
    } else {
      return {
        signal: 'neutral',
        description: 'MACD shows mixed signals, indicating consolidation or trend change.'
      };
    }
  }

  getMovingAverageSignal(ema50: number, ema200: number, sma50: number, sma200: number): { signal: 'buy' | 'sell' | 'neutral', description: string } {
    let bullishSignals = 0;
    let bearishSignals = 0;
    
    // EMA Golden/Death Cross
    if (ema50 > ema200) {
      bullishSignals++;
    } else if (ema50 < ema200) {
      bearishSignals++;
    }
    
    // SMA Golden/Death Cross
    if (sma50 > sma200) {
      bullishSignals++;
    } else if (sma50 < sma200) {
      bearishSignals++;
    }
    
    if (bullishSignals > bearishSignals) {
      return {
        signal: 'buy',
        description: 'Moving averages show bullish trend with shorter-term averages above longer-term averages.'
      };
    } else if (bearishSignals > bullishSignals) {
      return {
        signal: 'sell',
        description: 'Moving averages show bearish trend with shorter-term averages below longer-term averages.'
      };
    } else {
      return {
        signal: 'neutral',
        description: 'Moving averages show mixed signals or potential trend reversal.'
      };
    }
  }

  getBollingerBandsSignal(price: number, upper: number, lower: number): { signal: 'buy' | 'sell' | 'neutral', description: string } {
    if (price >= upper) {
      return {
        signal: 'sell',
        description: 'Price is at/above upper Bollinger Band, indicating potential overbought conditions.'
      };
    } else if (price <= lower) {
      return {
        signal: 'buy',
        description: 'Price is at/below lower Bollinger Band, indicating potential oversold conditions.'
      };
    } else {
      // Check if price is near bands (within 5%)
      const width = upper - lower;
      const distanceToUpper = upper - price;
      const distanceToLower = price - lower;
      
      if (distanceToUpper < width * 0.05) {
        return {
          signal: 'neutral',
          description: 'Price is approaching upper Bollinger Band, monitor for potential reversal.'
        };
      } else if (distanceToLower < width * 0.05) {
        return {
          signal: 'neutral',
          description: 'Price is approaching lower Bollinger Band, monitor for potential reversal.'
        };
      } else {
        return {
          signal: 'neutral',
          description: 'Price is within Bollinger Bands, indicating neutral market conditions.'
        };
      }
    }
  }

  calculateOverallSignal(): void {
    const buySignals = this.indicatorSignals.filter(s => s.signal === 'buy').length;
    const sellSignals = this.indicatorSignals.filter(s => s.signal === 'sell').length;
    
    if (buySignals > sellSignals) {
      this.signalAnalysis.trend = 'bullish';
      this.signalAnalysis.strength = Math.min(100, Math.round((buySignals / this.indicatorSignals.length) * 100));
      this.signalAnalysis.summary = `${buySignals} out of ${this.indicatorSignals.length} indicators show bullish signals. Consider buying or holding positions.`;
    } else if (sellSignals > buySignals) {
      this.signalAnalysis.trend = 'bearish';
      this.signalAnalysis.strength = Math.min(100, Math.round((sellSignals / this.indicatorSignals.length) * 100));
      this.signalAnalysis.summary = `${sellSignals} out of ${this.indicatorSignals.length} indicators show bearish signals. Consider selling or reducing positions.`;
    } else {
      this.signalAnalysis.trend = 'neutral';
      this.signalAnalysis.strength = 50;
      this.signalAnalysis.summary = 'Technical indicators show mixed signals. Market appears to be consolidating.';
    }
  }

  calculateSupportResistanceLevels(): void {
    if (!this.stockData || this.stockData.prices.length < 10) return;
    
    this.supportResistanceLevels = [];
    const prices = this.stockData.prices.map(p => p.close);
    const latestPrice = prices[prices.length - 1];
    
    // Find recent highs and lows
    let localHighs: number[] = [];
    let localLows: number[] = [];
    
    // Simple algorithm to find local tops and bottoms
    for (let i = 5; i < prices.length - 5; i++) {
      const window = prices.slice(i - 5, i + 6);
      const curPrice = prices[i];
      
      if (curPrice === Math.max(...window)) {
        localHighs.push(curPrice);
      }
      
      if (curPrice === Math.min(...window)) {
        localLows.push(curPrice);
      }
    }
    
    // Find support levels below current price
    localLows.sort((a, b) => b - a);
    const supports = localLows.filter(price => price < latestPrice).slice(0, 3);
    
    // Find resistance levels above current price
    localHighs.sort((a, b) => a - b);
    const resistances = localHighs.filter(price => price > latestPrice).slice(0, 3);
    
    // Add supports
    supports.forEach(level => {
      const priceDiff = Math.abs(latestPrice - level) / latestPrice;
      let strength: 'weak' | 'medium' | 'strong' = 'medium';
      
      if (priceDiff < 0.02) {
        strength = 'strong';
      } else if (priceDiff > 0.05) {
        strength = 'weak';
      }
      
      this.supportResistanceLevels.push({
        type: 'support',
        level: level,
        strength: strength
      });
    });
    
    // Add resistances
    resistances.forEach(level => {
      const priceDiff = Math.abs(latestPrice - level) / latestPrice;
      let strength: 'weak' | 'medium' | 'strong' = 'medium';
      
      if (priceDiff < 0.02) {
        strength = 'strong';
      } else if (priceDiff > 0.05) {
        strength = 'weak';
      }
      
      this.supportResistanceLevels.push({
        type: 'resistance',
        level: level,
        strength: strength
      });
    });
  }

  updateChartPreferences(): void {
    // Set chart preferences based on trading view
    switch(this.tradingView) {
      case 'intraday':
        this.chartType = 'candlestick';
        this.chartTimeframe = '1d';
        break;
      case 'swing':
        this.chartType = 'candlestick';
        this.chartTimeframe = '1w';
        break;
      case 'scalping':
        this.chartType = 'candlestick';
        this.chartTimeframe = '1d';
        break;
      case 'positional':
        this.chartType = 'candlestick';
        this.chartTimeframe = '1m';
        break;
      case 'longterm':
        this.chartType = 'line';
        this.chartTimeframe = '1y';
        break;
      case 'options':
        this.chartType = 'candlestick';
        this.chartTimeframe = '1m';
        break;
      case 'ai':
        this.chartType = 'line';
        this.chartTimeframe = '3m';
        break;
      default:
        this.chartType = 'candlestick';
        this.chartTimeframe = '1d';
    }
  }

  getTradingViewDescription(): string {
    switch(this.tradingView) {
      case 'intraday':
        return 'Intraday trading focuses on short-term price movements within a single trading day. Traders aim to capitalize on small price fluctuations over hours or minutes.';
      case 'swing':
        return 'Swing trading aims to capture short to medium-term gains over a period of days to weeks. Traders look for "swings" in price momentum.';
      case 'scalping':
        return 'Scalping is an ultra-short-term trading strategy aiming to make multiple small profits on minor price changes throughout the day.';
      case 'positional':
        return 'Positional trading involves holding positions for weeks to months to benefit from expected price movements based on fundamental and technical analysis.';
      case 'longterm':
        return 'Long-term investment focuses on holding assets for months to years, based primarily on fundamental analysis and long-term growth potential.';
      case 'options':
        return 'Options trading uses derivatives that give the right to buy or sell the underlying asset at a specified price within a specific time period.';
      case 'ai':
        return 'AI trading leverages machine learning algorithms to predict price movements and execute trades based on pattern recognition and predictive modeling.';
      default:
        return '';
    }
  }
}