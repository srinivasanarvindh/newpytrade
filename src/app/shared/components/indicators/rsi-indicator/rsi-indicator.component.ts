import { Component, Input, OnInit, ViewChild, ElementRef, AfterViewInit, OnChanges, SimpleChanges } from '@angular/core';
import { Chart, registerables } from 'chart.js';
import 'chartjs-adapter-moment';
import { RSIData } from '@core/models/stock.model';
import { ChartService } from '@core/services/chart.service';

// Register Chart.js components
Chart.register(...registerables);

@Component({
  selector: 'app-rsi-indicator',
  templateUrl: './rsi-indicator.component.html',
  styleUrls: ['./rsi-indicator.component.scss']
})
export class RsiIndicatorComponent implements OnInit, AfterViewInit, OnChanges {
  @Input() rsiData: RSIData[] = [];
  @Input() height: string = '200px';
  @Input() isLoading: boolean = false;

  @ViewChild('rsiCanvas') rsiCanvas!: ElementRef<HTMLCanvasElement>;
  
  chart: Chart | null = null;
  currentRSI: number = 0;
  rsiStatus: 'overbought' | 'oversold' | 'neutral' = 'neutral';

  constructor(private chartService: ChartService) {}

  ngOnInit(): void {
    this.updateCurrentRSI();
  }

  ngAfterViewInit(): void {
    this.initChart();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['rsiData'] && this.rsiCanvas) {
      this.updateCurrentRSI();
      if (this.chart) {
        this.chart.destroy();
      }
      this.initChart();
    }
  }

  private updateCurrentRSI(): void {
    if (this.rsiData && this.rsiData.length > 0) {
      this.currentRSI = Math.round(this.rsiData[this.rsiData.length - 1].value * 10) / 10;
      
      if (this.currentRSI >= 70) {
        this.rsiStatus = 'overbought';
      } else if (this.currentRSI <= 30) {
        this.rsiStatus = 'oversold';
      } else {
        this.rsiStatus = 'neutral';
      }
    }
  }

  private initChart(): void {
    if (!this.rsiCanvas || !this.rsiData || this.rsiData.length === 0) {
      return;
    }

    const ctx = this.rsiCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    const formattedData = this.chartService.formatRSIData(this.rsiData);
    const chartConfig = this.chartService.generateRSIChartConfig(formattedData);
    
    this.chart = new Chart(ctx, chartConfig);
  }
}
