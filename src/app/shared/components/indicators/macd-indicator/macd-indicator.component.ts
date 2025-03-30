import { Component, Input, OnInit, ViewChild, ElementRef, AfterViewInit, OnChanges, SimpleChanges } from '@angular/core';
import { Chart, registerables } from 'chart.js';
import 'chartjs-adapter-moment';
import { MACDData } from '@core/models/stock.model';
import { ChartService } from '@core/services/chart.service';

// Register Chart.js components
Chart.register(...registerables);

@Component({
  selector: 'app-macd-indicator',
  templateUrl: './macd-indicator.component.html',
  styleUrls: ['./macd-indicator.component.scss']
})
export class MacdIndicatorComponent implements OnInit, AfterViewInit, OnChanges {
  @Input() macdData: MACDData[] = [];
  @Input() height: string = '200px';
  @Input() isLoading: boolean = false;

  @ViewChild('macdCanvas') macdCanvas!: ElementRef<HTMLCanvasElement>;
  
  chart: Chart | null = null;
  currentMACD: number = 0;
  currentSignal: number = 0;
  currentHistogram: number = 0;
  macdStatus: 'bullish' | 'bearish' | 'neutral' = 'neutral';

  constructor(private chartService: ChartService) {}

  ngOnInit(): void {
    this.updateCurrentMACD();
  }

  ngAfterViewInit(): void {
    this.initChart();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['macdData'] && this.macdCanvas) {
      this.updateCurrentMACD();
      if (this.chart) {
        this.chart.destroy();
      }
      this.initChart();
    }
  }

  private updateCurrentMACD(): void {
    if (this.macdData && this.macdData.length > 0) {
      const lastMACD = this.macdData[this.macdData.length - 1];
      this.currentMACD = Math.round(lastMACD.macd * 1000) / 1000;
      this.currentSignal = Math.round(lastMACD.signal * 1000) / 1000;
      this.currentHistogram = Math.round(lastMACD.histogram * 1000) / 1000;
      
      // Determine MACD status based on histogram (MACD - Signal)
      if (lastMACD.histogram > 0 && lastMACD.histogram > this.macdData[this.macdData.length - 2]?.histogram) {
        this.macdStatus = 'bullish';
      } else if (lastMACD.histogram < 0 && lastMACD.histogram < this.macdData[this.macdData.length - 2]?.histogram) {
        this.macdStatus = 'bearish';
      } else {
        this.macdStatus = 'neutral';
      }
    }
  }

  private initChart(): void {
    if (!this.macdCanvas || !this.macdData || this.macdData.length === 0) {
      return;
    }

    const ctx = this.macdCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    const formattedData = this.chartService.formatMACDData(this.macdData);
    const chartConfig = this.chartService.generateMACDChartConfig(formattedData);
    
    this.chart = new Chart(ctx, chartConfig);
  }
}
