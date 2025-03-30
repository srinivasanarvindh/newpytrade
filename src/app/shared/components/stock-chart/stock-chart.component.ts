import { Component, Input, OnInit, ViewChild, ElementRef, AfterViewInit, OnChanges, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Chart, registerables, TimeScale } from 'chart.js';
import * as moment from 'moment';
// Import the moment adapter directly 
import 'chartjs-adapter-moment';
import { PriceData } from '../../../core/models/stock.model';
import { ChartService } from '../../../core/services/chart.service';

// Register all Chart.js components including TimeScale
Chart.register(...registerables, TimeScale);

@Component({
  selector: 'app-stock-chart',
  templateUrl: './stock-chart.component.html',
  styleUrls: ['./stock-chart.component.scss'],
  standalone: true,
  imports: [CommonModule]
})
export class StockChartComponent implements OnInit, AfterViewInit, OnChanges {
  @Input() priceData: PriceData[] = [];
  @Input() chartType: 'candlestick' | 'area' | 'line' = 'area';
  @Input() title: string = 'Stock Price';
  @Input() height: string = '400px';
  @Input() isLoading: boolean = false;
  @Input() showVolume: boolean = true;
  @Input() showLegend: boolean = true;
  @Input() enableZoom: boolean = true;
  @Input() predictions?: number[];
  @Input() predictionDates?: string[];

  @ViewChild('chartCanvas') chartCanvas!: ElementRef<HTMLCanvasElement>;
  
  chart: Chart | null = null;
  volumeChart: Chart | null = null;
  
  // Use inject for dependency injection in standalone components
  private chartService = inject(ChartService);

  ngOnInit(): void {}

  ngAfterViewInit(): void {
    this.initChart();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['priceData'] || changes['chartType'] || changes['predictions']) && this.chartCanvas) {
      if (this.chart) {
        this.chart.destroy();
      }
      this.initChart();
    }
  }

  private initChart(): void {
    if (!this.chartCanvas || !this.priceData || this.priceData.length === 0) {
      return;
    }

    const ctx = this.chartCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    // Ensure the canvas has an ID
    if (!this.chartCanvas.nativeElement.id) {
      this.chartCanvas.nativeElement.id = 'stockChart-' + Math.random().toString(36).substring(2, 9);
    }

    const chartId = this.chartCanvas.nativeElement.id;
    console.log(`Using chart ID: ${chartId}`);

    // Extract dates and prices from priceData
    const dates = this.priceData.map(d => d.date);
    const prices = this.priceData.map(d => d.close);
    
    // Create appropriate chart based on type
    if (this.chartType === 'candlestick') {
      // For now, we'll create a line chart since candlestick requires a different plugin
      this.chart = this.chartService.createPredictionChart(
        chartId,
        dates,
        prices,
        this.title,
        prices[prices.length - 1],
        '#1e88e5'
      );
    } else if (this.chartType === 'area') {
      // If predictions are available, include them in the chart
      if (this.predictions && this.predictions.length > 0 && this.predictionDates) {
        // Create a combined chart with both historical and prediction data
        const allDates = [...dates, ...this.predictionDates];
        const allPrices = [...prices, ...this.predictions];
        
        this.chart = this.chartService.createPredictionChart(
          chartId,
          allDates,
          allPrices,
          this.title,
          prices[prices.length - 1],
          '#1e88e5'
        );
      } else {
        // Create a standard area chart
        this.chart = this.chartService.createPredictionChart(
          chartId,
          dates,
          prices,
          this.title,
          prices[prices.length - 1],
          '#1e88e5'
        );
      }
    } else {
      // Default to line chart - using the same method but we can adjust styles if needed
      this.chart = this.chartService.createPredictionChart(
        chartId,
        dates,
        prices,
        this.title,
        prices[prices.length - 1],
        '#1e88e5'
      );
    }

    // Add volume chart if needed
    if (this.showVolume && this.priceData[0]?.volume) {
      this.initVolumeChart();
    }
  }

  private initVolumeChart(): void {
    // Implementation for volume chart if needed
  }
}
