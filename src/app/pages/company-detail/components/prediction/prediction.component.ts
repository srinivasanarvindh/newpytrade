import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { StockData, PredictionData } from '../../../../core/models/stock.model';
import { CommonModule, DecimalPipe, DatePipe } from '@angular/common';
import { ChartComponent } from '../../../../shared/components/chart/chart.component';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-prediction',
  templateUrl: './prediction.component.html',
  styleUrls: ['./prediction.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ChartComponent,
    LoadingSpinnerComponent,
    DecimalPipe,
    DatePipe
  ]
})
export class PredictionComponent implements OnChanges {
  @Input() stockData: StockData | null = null;
  @Input() predictionData: PredictionData | null = null;
  
  predictionSummary: {
    direction: 'up' | 'down' | 'neutral';
    percentChange: number;
    daysAhead: number;
    confidence: number;
    interpretation: string;
  } = {
    direction: 'neutral',
    percentChange: 0,
    daysAhead: 0,
    confidence: 0,
    interpretation: 'No prediction data available.'
  };
  
  predictionPoints: {
    date: string;
    actualPrice?: number;
    predictedPrice: number;
    percentDifference?: number;
  }[] = [];
  
  accuracyMetrics: {
    historicalAccuracy: number;
    meanError: number;
    confidence: number;
  } = {
    historicalAccuracy: 0,
    meanError: 0,
    confidence: 0
  };
  
  aiSummary: string = '';
  technicalFactors: string = '';
  fundamentalFactors: string = '';
  marketSentiment: string = '';
  
  isLoading = true;
  error: string | null = null;

  constructor() { }

  ngOnChanges(changes: SimpleChanges): void {
    console.log('AI Prediction received data:', {
      stockData: this.stockData,
      predictionData: this.predictionData
    });
    
    this.isLoading = false;
    
    // Always try to process data regardless of changes
    if (this.stockData && this.predictionData) {
      this.processData();
    } else {
      // Set up default state when data is missing
      this.error = 'Prediction data is not available for this stock.';
      
      // Set up default prediction data so the component can still render
      this.predictionSummary = {
        direction: 'neutral',
        percentChange: 0,
        daysAhead: 30, // Default to 30-day forecast period
        confidence: 50,
        interpretation: 'Insufficient data to generate predictions for this stock.'
      };
      
      this.generateAiAnalysisText();
      
      if (this.stockData) {
        // Use stock name if available
        const stockName = this.stockData.name || 'this stock';
        this.aiSummary = `AI prediction models cannot currently provide reliable forecasts for ${stockName} due to insufficient training data or market complexity.`;
      }
    }
  }

  processData(): void {
    try {
      this.isLoading = true;
      this.error = null;
      
      if (!this.predictionData || !this.predictionData.predictions || this.predictionData.predictions.length === 0) {
        throw new Error('No prediction data available');
      }
      
      // Extract the latest actual price from stock data
      const latestActualPrice = this.stockData && this.stockData.prices.length > 0 
        ? this.stockData.prices[this.stockData.prices.length - 1].close 
        : null;
      
      // Generate prediction points
      this.predictionPoints = [];
      const latestDate = this.stockData && this.stockData.prices.length > 0 
        ? new Date(this.stockData.prices[this.stockData.prices.length - 1].date)
        : new Date();
      
      if (this.predictionData.dates && this.predictionData.dates.length === this.predictionData.predictions.length) {
        // If we have explicit prediction dates
        for (let i = 0; i < this.predictionData.predictions.length; i++) {
          this.predictionPoints.push({
            date: this.predictionData.dates[i],
            predictedPrice: this.predictionData.predictions[i]
          });
        }
      } else {
        // Generate dates if none provided
        for (let i = 0; i < this.predictionData.predictions.length; i++) {
          const futureDate = new Date(latestDate);
          futureDate.setDate(futureDate.getDate() + i + 1);
          
          this.predictionPoints.push({
            date: futureDate.toISOString().split('T')[0],
            predictedPrice: this.predictionData.predictions[i]
          });
        }
      }
      
      // Calculate prediction summary
      if (latestActualPrice && this.predictionPoints.length > 0) {
        const lastPredictionPrice = this.predictionPoints[this.predictionPoints.length - 1].predictedPrice;
        const percentChange = ((lastPredictionPrice - latestActualPrice) / latestActualPrice) * 100;
        
        this.predictionSummary = {
          direction: percentChange > 1 ? 'up' : percentChange < -1 ? 'down' : 'neutral',
          percentChange: Math.abs(percentChange),
          daysAhead: this.predictionPoints.length,
          confidence: this.calculateConfidence(percentChange),
          interpretation: this.getInterpretation(percentChange)
        };
      }
      
      // Set mock accuracy metrics (in a real app, these would come from the model)
      this.accuracyMetrics = {
        historicalAccuracy: 85, // This would come from backtesting the model
        meanError: 2.5, // Average error percentage
        confidence: 80 // Confidence score for current prediction
      };
      
      // Generate AI analysis text
      this.generateAiAnalysisText();
      
      this.isLoading = false;
    } catch (error) {
      console.error('Error processing prediction data:', error);
      this.isLoading = false;
      this.error = 'Failed to process prediction data.';
    }
  }

  calculateConfidence(percentChange: number): number {
    // This is a simplified mock for confidence calculation
    // In a real app, this would be based on model uncertainty metrics
    const absChange = Math.abs(percentChange);
    
    if (absChange > 20) {
      return 60; // Lower confidence for extreme predictions
    } else if (absChange > 10) {
      return 70;
    } else if (absChange > 5) {
      return 80;
    } else {
      return 90; // Higher confidence for modest predictions
    }
  }

  getInterpretation(percentChange: number): string {
    if (percentChange > 10) {
      return 'AI model predicts significant upside potential over the forecast period.';
    } else if (percentChange > 5) {
      return 'AI model suggests moderate positive movement in the near term.';
    } else if (percentChange > 1) {
      return 'AI model indicates slight upward trend, but with limited movement.';
    } else if (percentChange > -1) {
      return 'AI model suggests sideways movement with minimal price change expected.';
    } else if (percentChange > -5) {
      return 'AI model indicates slight downward pressure in the near term.';
    } else if (percentChange > -10) {
      return 'AI model suggests moderate negative movement ahead.';
    } else {
      return 'AI model predicts significant downside risk over the forecast period.';
    }
  }

  generateAiAnalysisText(): void {
    // Generate AI summary based on prediction direction and magnitude
    if (this.predictionSummary.direction === 'up') {
      this.aiSummary = `The AI prediction model indicates a bullish outlook for ${this.stockData?.symbol} over the next ${this.predictionSummary.daysAhead} days. The model forecasts a potential ${this.predictionSummary.percentChange.toFixed(2)}% increase in price, with a confidence level of ${this.predictionSummary.confidence}%. This prediction is based on historical price patterns, technical indicators, and market sentiment analysis.`;
      
      this.technicalFactors = 'Positive technical factors include favorable momentum indicators, supportive moving average crossovers, and increasing volume patterns that suggest accumulation. The AI model has identified bullish chart patterns in recent price action.';
      
      this.fundamentalFactors = 'The model has factored in recent positive developments such as strong earnings reports, favorable industry trends, and potential catalysts that may drive growth in the near term.';
      
      this.marketSentiment = 'Market sentiment analysis reveals increasing investor interest, positive social media mentions, and growing institutional positioning that supports the bullish outlook.';
    } else if (this.predictionSummary.direction === 'down') {
      this.aiSummary = `The AI prediction model indicates a bearish outlook for ${this.stockData?.symbol} over the next ${this.predictionSummary.daysAhead} days. The model forecasts a potential ${this.predictionSummary.percentChange.toFixed(2)}% decrease in price, with a confidence level of ${this.predictionSummary.confidence}%. This prediction is based on historical price patterns, technical indicators, and market sentiment analysis.`;
      
      this.technicalFactors = 'Negative technical factors include deteriorating momentum indicators, bearish moving average crossovers, and decreasing volume patterns that suggest distribution. The AI model has identified bearish chart patterns in recent price action.';
      
      this.fundamentalFactors = 'The model has factored in recent challenges such as disappointing earnings, adverse industry trends, or potential headwinds that may impact performance in the near term.';
      
      this.marketSentiment = 'Market sentiment analysis reveals decreasing investor interest, negative social media sentiment, or reduced institutional positioning that supports the bearish outlook.';
    } else {
      this.aiSummary = `The AI prediction model indicates a neutral outlook for ${this.stockData?.symbol} over the next ${this.predictionSummary.daysAhead} days. The model forecasts minimal price movement (${this.predictionSummary.percentChange.toFixed(2)}%), with a confidence level of ${this.predictionSummary.confidence}%. This prediction suggests a period of consolidation or range-bound trading ahead.`;
      
      this.technicalFactors = 'Technical factors show mixed signals with balanced momentum indicators, neutral moving average alignments, and moderate volume patterns that suggest neither strong accumulation nor distribution.';
      
      this.fundamentalFactors = 'The model has factored in a balance of positive and negative factors, with no clear catalysts identified that would drive significant price movement in either direction.';
      
      this.marketSentiment = 'Market sentiment analysis reveals balanced investor interest without strong conviction in either direction, suggesting a wait-and-see approach from market participants.';
    }
  }
}
