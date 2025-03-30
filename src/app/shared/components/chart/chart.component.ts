import { Component, Input, OnInit, OnChanges, SimpleChanges, ElementRef, ViewChild, AfterViewInit, Output, EventEmitter } from '@angular/core';
import { StockData, StockPrice } from '../../../core/models/stock.model';
import Chart from 'chart.js/auto';
import { CommonModule } from '@angular/common';
import { LoadingSpinnerComponent } from '../loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-chart',
  templateUrl: './chart.component.html',
  styleUrls: ['./chart.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    LoadingSpinnerComponent
  ],
  styles: [`
    .chart-fallback {
      display: flex;
      height: 300px;
      align-items: center;
      justify-content: center;
      background-color: #f9f9f9;
      border-radius: 4px;
      margin: 10px 0;
    }
    .fallback-message {
      text-align: center;
      padding: 20px;
      color: #666;
    }
    .fallback-icon {
      font-size: 32px;
      margin-bottom: 10px;
    }
    .fallback-subtitle {
      font-size: 14px;
      margin-top: 8px;
      color: #888;
    }
  `]
})
export class ChartComponent implements OnInit, OnChanges, AfterViewInit {
  @Input() stockData: StockData | null = null;
  @Input() chartType: 'line' | 'candlestick' | 'ohlc' | 'bar' = 'line';
  @Input() timeframe: string = '1m';
  @Input() showVolume: boolean = true;
  @Input() showIndicators: boolean = false;
  @Input() indicators: any[] = [];
  @Input() predictions: number[] | null = null;
  @Input() predictionDates: string[] | null = null;
  
  @Output() timeframeChange = new EventEmitter<string>();
  @Output() chartTypeChange = new EventEmitter<'line' | 'candlestick' | 'ohlc' | 'bar'>();
  
  @ViewChild('chartCanvas') chartCanvas!: ElementRef<HTMLCanvasElement>;
  
  chart: Chart | null = null;
  isLoading = true;
  error: string | null = null;
  
  // Chart configuration - simplified for better compatibility
  chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    scales: {
      x: {
        grid: {
          display: false
        }
      },
      y: {
        position: 'right' as const,
        grid: {
          color: '#f0f0f0'
        }
      },
      y1: {
        position: 'left' as const,
        display: false,
        grid: {
          display: false
        }
      }
    },
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
      tooltip: {
        enabled: true
      }
    },
  };
  
  constructor() {}
  
  ngOnInit(): void {}
  
  // Add method to handle timeframe changes
  onTimeframeChange(newTimeframe: string): void {
    console.log(`Changing timeframe from ${this.timeframe} to ${newTimeframe}`);
    this.timeframe = newTimeframe;
    this.timeframeChange.emit(newTimeframe);
  }
  
  // Add method to handle chart type changes
  onChartTypeChange(newChartType: 'line' | 'candlestick' | 'ohlc' | 'bar'): void {
    console.log(`Changing chart type from ${this.chartType} to ${newChartType}`);
    this.chartType = newChartType;
    this.chartTypeChange.emit(newChartType);
  }
  
  ngAfterViewInit(): void {
    this.renderChart();
  }
  
  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['stockData'] || changes['chartType'] || changes['timeframe'] || 
         changes['showVolume'] || changes['predictions']) && this.chartCanvas) {
      this.renderChart();
    }
  }
  
  renderChart(): void {
    if (!this.stockData || !this.stockData.prices || !this.chartCanvas) {
      this.isLoading = false;
      this.error = 'No data available for chart rendering';
      return;
    }
    
    this.isLoading = true;
    this.error = null;
    
    // Destroy previous chart if it exists
    if (this.chart) {
      this.chart.destroy();
    }
    
    try {
      console.log('Rendering chart for data:', this.stockData);
      
      const ctx = this.chartCanvas.nativeElement.getContext('2d');
      if (!ctx) {
        throw new Error('Failed to get canvas context');
      }
      
      // Make sure prices is an array
      const prices = Array.isArray(this.stockData.prices) ? this.stockData.prices : [];
      
      if (prices.length === 0) {
        this.isLoading = false;
        this.error = 'No price data available for this stock';
        return;
      }
      
      // Safely parse dates, handling different date formats
      const labels = prices.map(price => {
        try {
          if (!price || !price.date) {
            return 'Unknown';
          }
          
          // Handle both ISO date strings and other formats
          const date = new Date(price.date);
          // Check if date is valid before using it
          if (!isNaN(date.getTime())) {
            return date.toLocaleDateString();
          }
          // If date is not valid, just return the original string
          return String(price.date);
        } catch (e) {
          console.warn('Error parsing date:', price.date, e);
          return String(price.date || 'Unknown');
        }
      });
      
      // Ensure numeric values for price and volume data
      const closeData = prices.map(price => {
        try {
          if (!price || price.close === undefined || price.close === null) {
            return 0;
          }
          return typeof price.close === 'number' ? price.close : parseFloat(String(price.close)) || 0;
        } catch (e) {
          console.warn('Error parsing close price:', price, e);
          return 0;
        }
      });
      
      const volumeData = prices.map(price => {
        try {
          if (!price || price.volume === undefined || price.volume === null) {
            return 0;
          }
          return typeof price.volume === 'number' ? price.volume : parseFloat(String(price.volume)) || 0;
        } catch (e) {
          console.warn('Error parsing volume:', price, e);
          return 0;
        }
      });
      
      // Create datasets based on chart type
      const datasets = [];
      
      if (this.chartType === 'line') {
        datasets.push({
          label: 'Price',
          data: closeData,
          borderColor: '#1e88e5',
          backgroundColor: 'rgba(30, 136, 229, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.1,
          yAxisID: 'y'
        });
      } else if (this.chartType === 'candlestick' || this.chartType === 'ohlc') {
        // Get OHLC data
        const openData = prices.map(price => {
          try {
            if (!price || price.open === undefined || price.open === null) {
              return 0;
            }
            return typeof price.open === 'number' ? price.open : parseFloat(String(price.open)) || 0;
          } catch (e) {
            console.warn('Error parsing open price:', price, e);
            return 0;
          }
        });
        
        const highData = prices.map(price => {
          try {
            if (!price || price.high === undefined || price.high === null) {
              return 0;
            }
            return typeof price.high === 'number' ? price.high : parseFloat(String(price.high)) || 0;
          } catch (e) {
            console.warn('Error parsing high price:', price, e);
            return 0;
          }
        });
        
        const lowData = prices.map(price => {
          try {
            if (!price || price.low === undefined || price.low === null) {
              return 0;
            }
            return typeof price.low === 'number' ? price.low : parseFloat(String(price.low)) || 0;
          } catch (e) {
            console.warn('Error parsing low price:', price, e);
            return 0;
          }
        });
        
        if (this.chartType === 'candlestick') {
          // Candlestick chart - rendered as colored lines for each OHLC component
          datasets.push({
            label: 'Open',
            data: openData,
            borderColor: '#1e88e5',
            backgroundColor: 'transparent',
            borderWidth: 1,
            yAxisID: 'y'
          });
          
          datasets.push({
            label: 'High',
            data: highData,
            borderColor: '#4caf50',
            backgroundColor: 'transparent',
            borderWidth: 1,
            yAxisID: 'y'
          });
          
          datasets.push({
            label: 'Low',
            data: lowData,
            borderColor: '#d32f2f',
            backgroundColor: 'transparent',
            borderWidth: 1,
            yAxisID: 'y'
          });
          
          datasets.push({
            label: 'Close',
            data: closeData,
            borderColor: '#ff9800',
            backgroundColor: 'transparent',
            borderWidth: 1,
            yAxisID: 'y'
          });
        } else if (this.chartType === 'ohlc') {
          // Traditional OHLC chart - rendered with a single dataset containing OHLC data
          const combinedData = prices.map((price, index) => {
            return {
              o: openData[index],
              h: highData[index],
              l: lowData[index],
              c: closeData[index]
            };
          });
          
          // OHLC chart implementation
          datasets.push({
            label: 'OHLC',
            data: combinedData,
            borderColor: '#333',
            backgroundColor: (price: any) => {
              // Green for bullish (close > open), red for bearish (close < open)
              const idx = prices.indexOf(price);
              return closeData[idx] >= openData[idx] ? 'rgba(75, 192, 192, 0.6)' : 'rgba(255, 99, 132, 0.6)';
            },
            borderWidth: 1,
            yAxisID: 'y',
            // Special options for OHLC rendering
            type: 'bar',
            barPercentage: 0.3
          });
        }
      }
      
      // Add volume data if needed
      if (this.showVolume && volumeData.some(v => v > 0)) {
        // Create a separate bar chart for volume with explicit typing
        const volumeDataset = {
          label: 'Volume',
          data: volumeData,
          backgroundColor: 'rgba(128, 128, 128, 0.3)',
          borderColor: 'rgba(128, 128, 128, 0.5)',
          borderWidth: 1,
          yAxisID: 'y1'
        };
        
        // Push as explicitly typed for Chart.js
        datasets.push(volumeDataset);
        
        // Show y1 axis for volume
        this.chartOptions.scales.y1.display = true;
      } else {
        this.chartOptions.scales.y1.display = false;
      }
      
      // Add predictions if available
      if (this.predictions && this.predictions.length > 0 && this.predictionDates && this.predictionDates.length > 0) {
        try {
          // Ensure prediction data is numeric
          const predictionData = this.predictions.map(price => {
            try {
              return typeof price === 'number' ? price : parseFloat(String(price)) || 0;
            } catch (e) {
              console.warn('Error parsing prediction:', price, e);
              return 0;
            }
          });
          
          // Create prediction dataset
          datasets.push({
            label: 'Prediction',
            data: predictionData,
            borderColor: '#e91e63',
            backgroundColor: 'rgba(233, 30, 99, 0.1)',
            borderWidth: 2,
            borderDash: [5, 5],
            fill: false,
            tension: 0.1,
            yAxisID: 'y',
            pointRadius: 3,
            pointBackgroundColor: '#e91e63'
          });
          
          // Add predicted dates to labels with safe parsing
          const uniqueLabels = new Set(labels);
          this.predictionDates.forEach(date => {
            try {
              if (!date) return;
              
              const dateStr = String(date);
              const parsedDate = new Date(dateStr);
              if (!isNaN(parsedDate.getTime())) {
                uniqueLabels.add(parsedDate.toLocaleDateString());
              } else {
                uniqueLabels.add(dateStr);
              }
            } catch (e) {
              console.warn('Error parsing prediction date:', date, e);
            }
          });
          
          // Convert uniqueLabels back to array
          const updatedLabels = Array.from(uniqueLabels);
          if (updatedLabels.length > 0) {
            labels.length = 0;
            labels.push(...updatedLabels);
          }
        } catch (e) {
          console.error('Error adding prediction data:', e);
        }
      }
      
      // Create the chart
      try {
        console.log('Chart datasets:', datasets);
        console.log('Chart labels:', labels);
        
        // Verify data integrity before creating chart
        const validDatasets = datasets.filter(d => Array.isArray(d.data) && d.data.length > 0);
        if (validDatasets.length === 0) {
          console.warn('No valid datasets available for chart');
          throw new Error('No valid datasets available for chart');
        }
        
        this.chart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: datasets as any[]
          },
          options: this.chartOptions
        });
      } catch (chartErr) {
        console.error('Chart initialization error:', chartErr);
        
        // Simply log the error code without trying to access error properties
        console.error('ERROR', { code: -100 });
        // Don't set error message so it doesn't block the tabs from loading
        // Just hide the chart canvas
        this.chart = null;
      }
      
      this.isLoading = false;
    } catch (err) {
      console.error('Error rendering chart:', err);
      this.isLoading = false;
      // Set a more specific error message but don't block tabs from loading
      this.error = 'Chart data visualization is currently unavailable.';
    }
  }
}
