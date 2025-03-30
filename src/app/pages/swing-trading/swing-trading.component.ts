import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { MainService } from '../../core/services/main.service';
import { ChartService } from '../../core/services/chart.service';
import { Subscription } from 'rxjs';

import { CommonModule } from '@angular/common';
import { MatTabsModule, MatTabChangeEvent } from '@angular/material/tabs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { RouterLink } from '@angular/router';
import { Chart } from 'chart.js';

@Component({
  selector: 'app-swing-trading',
  templateUrl: './swing-trading.component.html',
  styleUrls: ['./swing-trading.component.css'],
  standalone: true,
  imports: [
    CommonModule,
    MatTabsModule,
    MatProgressSpinnerModule,
    RouterLink
  ]
})
export class SwingTradingComponent implements OnInit, OnDestroy {
  
  swinglist = ["Short-Term", "Medium-Term", "Long-Term"];
  selectedSwingList = '';
  getSignalModel: any[] = [];
  isShowResult = false;
  isLoading = false;
  isError = false;
  errorMessage = '';
  loadingTime = 0;
  loadingTimer: any;
  chartLoading = false;
  estimatedTime = 30; // Default estimated loading time in seconds
  
  sendIndicatorDetail: any[] = [];
  rsiResult: any = {};
  macdResult: any = {};
  public chartOptions: any;
  receivedData: any;
  receivedSwingTrading = '';
  companySelect = 0;
  showNews: any;
  itemsPerPage = 5;
  totalPages = 1;
  paginatedData: any[] = [];
  currentPage = 1;

  private chart: Chart | null = null;
  
  // Track subscriptions for cleanup
  private subscriptions: Subscription[] = [];
  
  // Add a flag to identify if we're in a retry state
  isRetrying = false;
  retryCount = 0;
  maxRetries = 2;
  loadingMessage: string = '';
  
  constructor(
    private router: Router, 
    private mainService: MainService,
    private chartService: ChartService
  ) {
    // Chart options will be configured when creating the Chart.js instance
  }

  ngOnInit(): void {
    this.loadSwingTradingData();
  }
  
  ngOnDestroy(): void {
    // Clean up subscriptions to prevent memory leaks
    this.subscriptions.forEach(sub => sub.unsubscribe());
    
    // Make sure to clear any interval timers
    if (this.loadingTimer) {
      clearInterval(this.loadingTimer);
      this.loadingTimer = null;
    }
  }
  
  loadDefaultData(): void {
    this.isLoading = true;
    const defaultTickers = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS'];
    
    this.mainService.setData(defaultTickers);
    this.receivedData = defaultTickers;
    
    // Set default timeframe if not already set
    if (!this.receivedSwingTrading) {
      this.receivedSwingTrading = 'Short-Term';
      this.mainService.setSwingTrading('Short-Term');
    }
    
    // Load the data
    this.loadSwingTradingData();
  }

  loadSwingTradingData(): void {
    this.isLoading = true;
    this.isError = false;
    this.loadingTime = 0;
    this.chartLoading = true;
    
    // Start a timer to show loading progress
    if (this.loadingTimer) {
      clearInterval(this.loadingTimer);
    }
    
    this.loadingTimer = setInterval(() => {
      this.loadingTime++;
      
      // Calculate estimated time based on number of stocks
      if (this.receivedData && this.receivedData.length > 0) {
        // More accurate time estimation: 10 sec per ticker + 20 sec base
        this.estimatedTime = 20 + (this.receivedData.length * 10);  
        
        // Show meaningful messages during loading
        if (this.loadingTime > this.estimatedTime * 2) {
          this.loadingMessage = 'This is taking longer than expected. The server might be busy. Live data retrieval can take time.';
        } else if (this.loadingTime > this.estimatedTime) {
          this.loadingMessage = 'Almost done... Finalizing analysis with live market data';
        } else {
          this.loadingMessage = `Loading ${this.receivedSwingTrading} data using live market information...`;
        }
      }
    }, 1000);
    
    // Ensure timeframe is correctly set in the service
    if (this.selectedSwingList) {
      console.log(`Using selected timeframe: ${this.selectedSwingList}`);
      this.mainService.setSwingTrading(this.selectedSwingList);
    } else if (this.receivedSwingTrading) {
      console.log(`Using received timeframe: ${this.receivedSwingTrading}`);
      this.mainService.setSwingTrading(this.receivedSwingTrading);
    } else {
      // Default to Short-Term if nothing is set
      console.log(`No timeframe set, defaulting to Short-Term`);
      this.selectedSwingList = 'Short-Term';
      this.receivedSwingTrading = 'Short-Term';
      this.mainService.setSwingTrading('Short-Term');
    }
    
    console.log(`Loading swing trading data with timeframe: ${this.mainService.getSwingTrading()}`);
    
    // Check if we have data to process
    if (!this.receivedData || this.receivedData.length === 0) {
      console.warn('No ticker data available, loading default tickers');
      this.loadDefaultData();
      return;
    }
    
    // Set a reasonable timeout for API requests - longer for live data
    const timeoutTimer = setTimeout(() => {
      if (this.isLoading) {
        console.warn('Request is taking a long time with live data. Consider reducing the number of stocks');
        // Don't retry automatically, just show a warning to the user
        this.loadingMessage = 'Request is taking longer than expected with live data. Consider reducing the number of stocks or trying again later.';
      }
    }, 120000); // 2 minute warning for live data
    
    // Track the subscription for cleanup
    const subscription = this.mainService.getPredictedSwingTrading(this.receivedData).subscribe({
      next: (response) => {
        // Clear the loading timer
        if (this.loadingTimer) {
          clearInterval(this.loadingTimer);
          this.loadingTimer = null;
        }
        clearTimeout(timeoutTimer);
        
        this.isLoading = false;
        
        if (response && Array.isArray(response)) {
          this.getSignalModel = response;
          
          // Filter out items with errors
          const validData = this.getSignalModel.filter((item: any) => !item.result.error);
          
          if (validData.length === 0) {
            console.warn('All tickers returned errors - possibly a connection issue');
            this.isError = true;
            this.errorMessage = "Unable to retrieve live data for any of the selected stocks. Please check your network connection or try different stocks.";
            return;
          }
          
          // Sort valid data based on overall score
          validData.sort((a: any, b: any) => 
            (b.result.combined_overall_score || 0) - (a.result.combined_overall_score || 0)
          );
          
          this.getSignalModel = validData;
          this.totalPages = Math.ceil(this.getSignalModel.length / this.itemsPerPage);
          this.updatePagination();
          
          if (this.getSignalModel.length > 0) {
            this.showResult(0); // Show the first result by default
          } else {
            console.warn('No valid data received after filtering');
            this.isError = true;
            this.errorMessage = "No valid data available for the selected stocks. Try different stocks or refresh.";
          }
        } else {
          this.isError = true;
          this.errorMessage = 'Invalid response format received from server. The data source might be unavailable.';
        }
      },
      error: (error) => {
        // Clear the loading timer
        if (this.loadingTimer) {
          clearInterval(this.loadingTimer);
          this.loadingTimer = null;
        }
        clearTimeout(timeoutTimer);
        
        this.isLoading = false;
        this.isError = true;
        
        // Format a more user-friendly error message
        if (error.message && error.message.includes('504')) {
          this.errorMessage = "The server took too long to respond while retrieving live data. Try reducing the number of stocks or selecting a different timeframe.";
        } else if (error.message && error.message.includes('Network Error')) {
          this.errorMessage = "Network error occurred. Please check your internet connection and try again.";
        } else {
          this.errorMessage = error.message || "Failed to load swing trading data from live sources";
        }
        
        console.error('Error loading live swing trading data:', error);
      }
    });
    
    this.subscriptions.push(subscription);
  }

  updatePagination(): void {
    // Simply show all data 
    this.paginatedData = this.getSignalModel;
  }

  selectTimeframe(timeframe: string): void {
    console.log(`Selecting new timeframe: ${timeframe}`);
    
    // Reset any error state
    this.isError = false;
    
    // Normalize the timeframe to ensure consistent values
    this.selectedSwingList = timeframe;
    this.mainService.setSwingTrading(timeframe);
    this.receivedSwingTrading = timeframe;
    
    // Add a small delay to ensure the service has updated the timeframe
    setTimeout(() => {
      // Set loading state before fetching data
      this.isLoading = true;
      
      // Hide results while loading
      this.isShowResult = false;
      
      // Load data with the new timeframe
      this.loadSwingTradingData();
    }, 500);
  }

  /**
   * Navigate to company details in a new window
   * @param ticker Stock ticker symbol
   * @param newWindow Whether to open in a new window (always true for swing-trading)
   */
  navigateToCompany(ticker: string, newWindow: boolean = true): void {
    if (ticker) {
      // Always open in new window/tab per user requirement
      window.open(`/company/${ticker}`, '_blank');
    }
  }

  openPopup(data: any): void {
    console.log('Indicator data:', data);
    
    // Create a more detailed popup with the fundamental analysis data
    let message = '';
    
    // Always show basic data regardless of fa_detailed_info availability
    message += '=== FUNDAMENTAL ANALYSIS REPORT ===\n\n';
    
    // Add basic metrics that are already visible in the table
    message += `Earnings Growth: ${data.earnings_growth || 'N/A'}%\n`;
    message += `Debt to Equity: ${data.debt_to_equity || 'N/A'}\n`;
    message += `P/E Ratio: ${data.pe_ratio || 'N/A'}\n\n`;
    
    // Add overall score if available
    message += `Overall FA Score: ${data.overall_fa_score || 'N/A'}\n\n`;
    
    // Check if additional data is available
    if (data && data.fa_detailed_info) {
      // Add detailed data if available
      message += '--- DETAILED METRICS ---\n\n';
      
      if (data.fa_detailed_info.investorInsightMetrics) {
        // Format investor insights
        message += 'Investor Insights:\n';
        for (const [key, value] of Object.entries(data.fa_detailed_info.investorInsightMetrics)) {
          message += `${key}: ${value}\n`;
        }
        message += '\n';
      }
      
      if (data.fa_detailed_info.profitabilityIndicators) {
        // Format profitability
        message += 'Profitability:\n';
        for (const [key, value] of Object.entries(data.fa_detailed_info.profitabilityIndicators)) {
          message += `${key}: ${value}\n`;
        }
        message += '\n';
      }
    }
    
    // Add message about detailed information
    message += 'For more comprehensive analysis, please visit the company detail page.';
    
    // Show the popup
    alert(message);
  }

  showResult(index: number): void {
    this.isShowResult = true;
    this.chartLoading = true;
    
    const realIndex = index;
    this.companySelect = realIndex;
    
    if (!this.getSignalModel[realIndex]) {
      console.error('Invalid index or no data available');
      this.chartLoading = false;
      return;
    }
    
    // Get the ticker symbol for the selected company
    const ticker = this.getSignalModel[realIndex].result.ticker;
    
    // Fetch news for this ticker from the company endpoint
    if (ticker && ticker !== 'all') {
      // Set loading state for news
      this.showNews = [];
      
      // Fetch news from company endpoint
      this.mainService.getCompanyNews(ticker).subscribe({
        next: (newsData) => {
          console.log(`News data fetched for ${ticker}:`, newsData);
          if (Array.isArray(newsData)) {
            this.showNews = newsData;
          } else {
            console.warn(`Invalid news data format for ${ticker}`);
            this.showNews = [];
          }
        },
        error: (err) => {
          console.error(`Error fetching news for ${ticker}:`, err);
          // Fallback to any news already in the model
          if (this.getSignalModel[realIndex].result.news && 
              Array.isArray(this.getSignalModel[realIndex].result.news)) {
            this.showNews = this.getSignalModel[realIndex].result.news;
          } else {
            this.showNews = [];
          }
        }
      });
    } else {
      // If no valid ticker, use any news already in the model
      if (this.getSignalModel[realIndex].result.news && 
          Array.isArray(this.getSignalModel[realIndex].result.news)) {
        this.showNews = this.getSignalModel[realIndex].result.news;
      } else {
        this.showNews = [];
      }
    }
    
    // Wait for the next Angular change detection cycle and create chart
    // after the MatTab is properly activated
    setTimeout(() => {
      this.createPredictionChart();
    }, 500);
  }
  
  /**
   * Creates the prediction chart with proper error handling and retries
   */
  private createPredictionChart(): void {
    console.log('Creating prediction chart');
    try {
      const companyData = this.getSignalModel[this.companySelect];
      if (!companyData || !companyData.result) {
        console.error('No company data available');
        this.chartLoading = false;
        return;
      }
      
      console.log(`Setting up chart for ticker: ${companyData.result.ticker}`);
      
      // Set appropriate chart color based on signal
      let chartColor = '#1e88e5'; // Default blue
      if (companyData.result.combined_overall_signal === 'Buy') {
        chartColor = '#4caf50'; // Green for buy
      } else if (companyData.result.combined_overall_signal === 'Sell' || 
                companyData.result.combined_overall_signal === 'DBuy') {
        chartColor = '#f44336'; // Red for sell/don't buy
      } else if (companyData.result.combined_overall_signal === 'Neutral') {
        chartColor = '#ff9800'; // Orange for neutral
      }
      
      // Destroy previous chart instance if it exists
      if (this.chart) {
        console.log('Destroying existing chart instance');
        this.chart.destroy();
        this.chart = null;
      }
      
      // Prepare data for Chart.js
      let dates: string[] = [];
      let prices: number[] = [];
      
      // Check if prediction data exists
      if (companyData.result.prediction_dates && 
          Array.isArray(companyData.result.prediction_dates) &&
          companyData.result.prediction_prices && 
          Array.isArray(companyData.result.prediction_prices) &&
          companyData.result.prediction_prices.length > 0) {
        
        console.log(`Using prediction data from API: ${companyData.result.prediction_dates.length} dates`);
        dates = companyData.result.prediction_dates;
        
        // Safely map the prediction prices to numbers
        prices = companyData.result.prediction_prices.map((value: any) => {
          return Number(parseFloat(value || 0).toFixed(2));
        });
      } else {
        console.warn("No prediction data available, using defaults");
        
        // Generate default dates and prices
        const today = new Date();
        const currentPrice = companyData.result.current_price || 100;
        
        for (let i = 0; i < 5; i++) {
          const futureDate = new Date(today);
          futureDate.setDate(today.getDate() + i + 1);
          dates.push(futureDate.toISOString().split('T')[0]);
          
          // Generate a slightly increasing or decreasing price based on signal
          const direction = companyData.result.combined_overall_signal === 'Buy' ? 1 : 
                          (companyData.result.combined_overall_signal === 'Sell' ? -1 : 0.5);
          prices.push(Number((currentPrice * (1 + (i * 0.01 * direction))).toFixed(2)));
        }
      }
      
      // Wait for DOM to be ready
      setTimeout(() => {
        // Fixed canvas ID that matches our HTML template
        const canvasId = 'prediction-chart-0';
        
        // Try to create the chart with multiple attempts
        this.attemptChartCreation(canvasId, dates, prices, companyData, chartColor);
      }, 100);
      
    } catch (error) {
      console.error('Error in chart setup:', error);
      this.chartLoading = false;
    }
  } 
  
  /**
   * Attempts to create a chart with multiple retries
   */
  private attemptChartCreation(
    canvasId: string, 
    dates: string[], 
    prices: number[], 
    companyData: any, 
    chartColor: string
  ): void {
    let attempts = 0;
    const maxAttempts = 5;
    const retryIntervalMs = 400;
    
    const tryCreateChart = () => {
      attempts++;  
      console.log(`Attempting to create chart, attempt ${attempts}/${maxAttempts}`);
      
      const canvasElement = document.getElementById(canvasId);
      
      if (!canvasElement) {
        console.warn(`Canvas element not found with ID: ${canvasId}, attempt ${attempts}/${maxAttempts}`);
        
        if (attempts < maxAttempts) {
          setTimeout(tryCreateChart, retryIntervalMs);
        } else {
          console.error(`Failed to find canvas element after ${maxAttempts} attempts`);
          this.chartLoading = false;
        }
        return;
      }
      
      // Canvas found, try creating chart
      console.log(`Found canvas element with ID: ${canvasId} on attempt ${attempts}`);
      
      try {
        // Destroy previous chart instance if it exists
        if (this.chart) {
          this.chart.destroy();
          this.chart = null;
        }
        
        // Force the canvas to be visible and sized
        canvasElement.style.width = '100%';
        canvasElement.style.height = '350px';
        canvasElement.style.display = 'block';
        
        // Create new chart
        this.chart = this.chartService.createPredictionChart(
          canvasId,
          dates,
          prices,
          companyData.result.ticker || 'Stock', 
          companyData.result.current_price || 0,
          chartColor
        );
        
        console.log(`Successfully created chart for ${companyData.result.ticker}`);
        this.chartLoading = false;
      } catch (err) {
        console.error(`Error creating chart: ${err}`);
        
        if (attempts < maxAttempts) {
          console.warn(`Retrying chart creation, attempt ${attempts + 1}/${maxAttempts}`);
          setTimeout(tryCreateChart, retryIntervalMs);
        } else {
          console.error(`Failed to create chart after ${maxAttempts} attempts`);
          this.chartLoading = false;
        }
      }
    };
    
    // Start the retry process
    tryCreateChart();
  }

  getScoreClass(score: number): string {
    if (score >= 70) return 'score-high';
    if (score >= 40) return 'score-medium';
    return 'score-low';
  }

  getSentimentClass(sentiment: string): string {
    if (sentiment === 'Buy' || sentiment === 'good') return 'green';
    if (sentiment === 'DBuy' || sentiment === 'bad') return 'red';
    return 'yellow';
  }

  goBack(): void {
    console.log('Navigating back to tools page');
    this.router.navigate(['/tools']);
  }
  
  /**
   * Handle tab change events - specifically for chart rendering
   */
  onTabChange(event: MatTabChangeEvent): void {
    console.log(`Tab changed to: ${event.index}`);
    
    // If we switched to the chart tab (index 1)
    if (event.index === 1) {
      console.log('Switched to chart tab, initializing chart');
      this.chartLoading = true;
      
      // Delay to ensure the DOM is ready after the tab animation completes
      setTimeout(() => {
        this.createPredictionChart();
      }, 300);
    }
  }
}