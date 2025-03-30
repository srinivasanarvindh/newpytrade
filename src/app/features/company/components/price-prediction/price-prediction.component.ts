import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { PriceData, PredictionData } from '@core/models/stock.model';

@Component({
  selector: 'app-price-prediction',
  templateUrl: './price-prediction.component.html',
  styleUrls: ['./price-prediction.component.scss']
})
export class PricePredictionComponent implements OnChanges {
  @Input() predictionData: PredictionData | null = null;
  @Input() priceData: PriceData[] = [];
  @Input() isLoading: boolean = true;

  // Prediction stats
  latestPrice: number = 0;
  predictedPrices: number[] = [];
  predictionDates: string[] = [];
  
  maxPredictedPrice: number = 0;
  minPredictedPrice: number = 0;
  avgPredictedPrice: number = 0;
  
  shortTermTrend: 'bullish' | 'bearish' | 'neutral' = 'neutral';
  predictionConfidence: 'high' | 'moderate' | 'low' = 'moderate';
  potentialReturn: number = 0;
  
  // Display chart with predictions
  showPredictionChart: boolean = true;

  constructor() { }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['predictionData'] || changes['priceData']) && !this.isLoading) {
      this.processPredictionData();
    }
  }

  private processPredictionData(): void {
    // Get latest price from price data
    if (this.priceData && this.priceData.length > 0) {
      this.latestPrice = this.priceData[this.priceData.length - 1].close;
    }
    
    // Process prediction data
    if (this.predictionData) {
      this.predictedPrices = this.predictionData.predictions || [];
      this.predictionDates = this.predictionData.dates || [];
      
      if (this.predictedPrices.length > 0) {
        // Calculate prediction stats
        this.maxPredictedPrice = Math.max(...this.predictedPrices);
        this.minPredictedPrice = Math.min(...this.predictedPrices);
        this.avgPredictedPrice = this.predictedPrices.reduce((sum, price) => sum + price, 0) / this.predictedPrices.length;
        
        // Determine short-term trend
        const lastPredictedPrice = this.predictedPrices[this.predictedPrices.length - 1];
        const percentChange = ((lastPredictedPrice - this.latestPrice) / this.latestPrice) * 100;
        
        if (percentChange > 3) {
          this.shortTermTrend = 'bullish';
        } else if (percentChange < -3) {
          this.shortTermTrend = 'bearish';
        } else {
          this.shortTermTrend = 'neutral';
        }
        
        // Calculate potential return
        this.potentialReturn = percentChange;
        
        // Determine prediction confidence based on volatility
        const volatility = (this.maxPredictedPrice - this.minPredictedPrice) / this.avgPredictedPrice;
        
        if (volatility < 0.05) {
          this.predictionConfidence = 'high';
        } else if (volatility < 0.1) {
          this.predictionConfidence = 'moderate';
        } else {
          this.predictionConfidence = 'low';
        }
      }
    }
  }
}
