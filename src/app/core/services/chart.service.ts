import { Injectable } from '@angular/core';
import { Chart, ChartConfiguration, registerables } from 'chart.js';
import 'chartjs-adapter-moment';

@Injectable({
  providedIn: 'root'
})
export class ChartService {
  constructor() {
    // Register all Chart.js components
    Chart.register(...registerables);
  }

  /**
   * Creates a line chart with prediction data
   * @param canvasId - The ID of the canvas element
   * @param dates - Array of date strings
   * @param prices - Array of price values
   * @param label - Name of the stock
   * @param currentPrice - Current stock price
   * @param chartColor - Color for the chart
   * @returns The created Chart instance
   */
  createPredictionChart(
    canvasId: string,
    dates: string[],
    prices: number[],
    label: string,
    currentPrice: number,
    chartColor: string = '#1e88e5'
  ): Chart {
    console.log(`Chart service creating chart with ID: ${canvasId}`);
    
    // Remove any existing charts with the same ID
    try {
      const existingChart = Chart.getChart(canvasId);
      if (existingChart) {
        console.log(`Destroying existing chart with ID: ${canvasId}`);
        existingChart.destroy();
      }
    } catch (err) {
      console.warn(`Error checking for existing chart: ${err}`);
      // Continue even if error - this could be because no chart exists yet
    }
    
    // Get the canvas element
    const canvas = document.getElementById(canvasId) as HTMLCanvasElement;
    if (!canvas) {
      console.error(`Canvas element with ID ${canvasId} not found`);
      throw new Error(`Canvas element with ID ${canvasId} not found`);
    }
    
    console.log(`Found canvas element with ID: ${canvasId}`);
    
    // Ensure canvas is visible and properly sized
    canvas.style.display = 'block';
    canvas.style.width = '100%';
    canvas.style.height = '350px';
    
    // Force a redraw of the canvas
    canvas.getContext('2d')?.clearRect(0, 0, canvas.width, canvas.height);
    
    // Get rendering context
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      console.error('Could not get canvas context');
      throw new Error('Could not get canvas context');
    }

    // Format the dates consistently
    const formattedDates = dates.map(date => {
      // Ensure the date is properly formatted
      try {
        return new Date(date).toISOString().split('T')[0];
      } catch (e) {
        console.warn(`Invalid date: ${date}, using as-is`);
        return date;
      }
    });

    // We'll add a current price indicator in a different way
    // instead of using annotations which requires a plugin

    // Create chart configuration
    const config: ChartConfiguration = {
      type: 'line',
      data: {
        labels: formattedDates,
        datasets: [{
          label: label,
          data: prices,
          backgroundColor: chartColor,
          borderColor: chartColor,
          borderWidth: 2,
          tension: 0.2,
          pointRadius: 5,
          pointHoverRadius: 7,
          fill: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            titleColor: '#333',
            bodyColor: '#333',
            borderColor: '#ddd',
            borderWidth: 1,
            padding: 10,
            displayColors: false
          },
          title: {
            display: true,
            text: `${label} Price Prediction`,
            font: {
              size: 16
            }
          },
          legend: {
            display: true,
            position: 'top'
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Date',
              font: {
                size: 14
              }
            },
            ticks: {
              maxRotation: 45,
              minRotation: 45
            }
          },
          y: {
            title: {
              display: true,
              text: 'Price',
              font: {
                size: 14
              }
            },
            beginAtZero: false
          }
        }
      }
    };

    // Create and return chart
    return new Chart(ctx, config);
  }
}