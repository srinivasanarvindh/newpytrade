import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, of } from 'rxjs';
import { StockService } from '@core/services/stock.service';
import { Stock } from '@core/models/stock.model';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  trendingStocks$: Observable<Stock[]> = of([]);
  isLoading = true;

  // Featured images from Unsplash
  dashboardImages = [
    'https://images.unsplash.com/photo-1554260570-e9689a3418b8',
    'https://images.unsplash.com/photo-1488459716781-31db52582fe9',
    'https://images.unsplash.com/photo-1508589066756-c5dfb2cb7587',
    'https://images.unsplash.com/photo-1501523460185-2aa5d2a0f981'
  ];

  chartImages = [
    'https://images.unsplash.com/photo-1444653614773-995cb1ef9efa',
    'https://images.unsplash.com/photo-1563986768711-b3bde3dc821e',
    'https://images.unsplash.com/photo-1579532582937-16c108930bf6',
    'https://images.unsplash.com/photo-1556155092-490a1ba16284'
  ];

  platformImages = [
    'https://images.unsplash.com/photo-1644361566696-3d442b5b482a',
    'https://images.unsplash.com/photo-1690226613377-aa7c2facb58d',
    'https://images.unsplash.com/photo-1644363832001-0876e81f37a9',
    'https://images.unsplash.com/photo-1640661089711-708d6043d0c7'
  ];

  // Top selling stocks categories
  topSellingCategories = [
    { id: 'us', name: 'US Stocks' },
    { id: 'india', name: 'Indian Stocks' },
    { id: 'technology', name: 'Technology' },
    { id: 'automotive', name: 'Automotive' },
    { id: 'healthcare', name: 'Healthcare' }
  ];
  
  selectedCategory = 'us';

  // Top selling stocks by category
  topSellingStocks: { [key: string]: Stock[] } = {
    'us': [
      { symbol: 'AAPL', company: 'Apple Inc.', lastPrice: 173.57, changePercent: 1.45, sector: 'Technology' },
      { symbol: 'MSFT', company: 'Microsoft Corporation', lastPrice: 338.11, changePercent: 0.87, sector: 'Technology' },
      { symbol: 'GOOGL', company: 'Alphabet Inc.', lastPrice: 132.60, changePercent: 1.23, sector: 'Technology' },
      { symbol: 'AMZN', company: 'Amazon.com, Inc.', lastPrice: 134.68, changePercent: -0.34, sector: 'Consumer' },
      { symbol: 'TSLA', company: 'Tesla, Inc.', lastPrice: 238.83, changePercent: 2.57, sector: 'Automotive' },
      { symbol: 'META', company: 'Meta Platforms, Inc.', lastPrice: 312.81, changePercent: 0.91, sector: 'Technology' }
    ],
    'india': [
      { symbol: 'RELIANCE', company: 'Reliance Industries Ltd.', lastPrice: 2389.75, changePercent: 1.23, sector: 'Energy' },
      { symbol: 'HDFCBANK', company: 'HDFC Bank Ltd.', lastPrice: 1583.20, changePercent: 0.45, sector: 'Banking' },
      { symbol: 'INFY', company: 'Infosys Ltd.', lastPrice: 1478.50, changePercent: 2.11, sector: 'Technology' },
      { symbol: 'TCS', company: 'Tata Consultancy Services Ltd.', lastPrice: 3450.65, changePercent: -0.23, sector: 'Technology' },
      { symbol: 'ICICIBANK', company: 'ICICI Bank Ltd.', lastPrice: 963.80, changePercent: 0.78, sector: 'Banking' },
      { symbol: 'KOTAKBANK', company: 'Kotak Mahindra Bank Ltd.', lastPrice: 1756.40, changePercent: -0.32, sector: 'Banking' }
    ],
    'technology': [
      { symbol: 'AAPL', company: 'Apple Inc.', lastPrice: 173.57, changePercent: 1.45, sector: 'Technology' },
      { symbol: 'MSFT', company: 'Microsoft Corporation', lastPrice: 338.11, changePercent: 0.87, sector: 'Technology' },
      { symbol: 'GOOGL', company: 'Alphabet Inc.', lastPrice: 132.60, changePercent: 1.23, sector: 'Technology' },
      { symbol: 'NVDA', company: 'NVIDIA Corporation', lastPrice: 429.97, changePercent: 3.58, sector: 'Technology' },
      { symbol: 'ADBE', company: 'Adobe Inc.', lastPrice: 564.70, changePercent: 0.91, sector: 'Technology' },
      { symbol: 'CRM', company: 'Salesforce, Inc.', lastPrice: 228.06, changePercent: 1.75, sector: 'Technology' }
    ],
    'automotive': [
      { symbol: 'TSLA', company: 'Tesla, Inc.', lastPrice: 238.83, changePercent: 2.57, sector: 'Automotive' },
      { symbol: 'F', company: 'Ford Motor Company', lastPrice: 11.94, changePercent: -0.34, sector: 'Automotive' },
      { symbol: 'GM', company: 'General Motors Company', lastPrice: 33.82, changePercent: 0.12, sector: 'Automotive' },
      { symbol: 'TM', company: 'Toyota Motor Corporation', lastPrice: 188.13, changePercent: 0.78, sector: 'Automotive' },
      { symbol: 'RIVN', company: 'Rivian Automotive, Inc.', lastPrice: 16.75, changePercent: -1.43, sector: 'Automotive' },
      { symbol: 'LCID', company: 'Lucid Group, Inc.', lastPrice: 5.04, changePercent: -2.13, sector: 'Automotive' }
    ],
    'healthcare': [
      { symbol: 'JNJ', company: 'Johnson & Johnson', lastPrice: 165.67, changePercent: 0.48, sector: 'Healthcare' },
      { symbol: 'PFE', company: 'Pfizer Inc.', lastPrice: 29.41, changePercent: -0.71, sector: 'Healthcare' },
      { symbol: 'UNH', company: 'UnitedHealth Group Incorporated', lastPrice: 490.87, changePercent: 1.24, sector: 'Healthcare' },
      { symbol: 'MRK', company: 'Merck & Co., Inc.', lastPrice: 109.57, changePercent: 0.91, sector: 'Healthcare' },
      { symbol: 'ABT', company: 'Abbott Laboratories', lastPrice: 106.32, changePercent: 0.52, sector: 'Healthcare' },
      { symbol: 'LLY', company: 'Eli Lilly and Company', lastPrice: 583.16, changePercent: 2.38, sector: 'Healthcare' }
    ]
  };

  // Market indices for the demo
  marketIndices: Stock[] = [
    { symbol: 'NIFTY 50', company: 'National Stock Exchange of India', lastPrice: 19889.70, changePercent: 0.53, sector: 'Index' },
    { symbol: 'BSE 30', company: 'Bombay Stock Exchange Sensex', lastPrice: 66060.90, changePercent: 0.42, sector: 'Index' },
    { symbol: 'S&P 500', company: 'Standard & Poor\'s 500', lastPrice: 4515.77, changePercent: 0.81, sector: 'Index' },
    { symbol: 'NASDAQ', company: 'NASDAQ Composite', lastPrice: 14031.81, changePercent: 1.28, sector: 'Index' }
  ];

  // Trading strategies
  tradingStrategies = [
    {
      name: 'Intraday',
      description: 'Short-term trading within a single day',
      icon: 'schedule'
    },
    {
      name: 'Swing Trading',
      description: 'Medium-term trading over several days or weeks',
      icon: 'trending_up'
    },
    {
      name: 'Scalping',
      description: 'Ultra-short-term trading for small profits',
      icon: 'bolt'
    },
    {
      name: 'Positional Trading',
      description: 'Medium to long-term position holding',
      icon: 'domain'
    },
    {
      name: 'Long-Term Investment',
      description: 'Long-term investment strategy',
      icon: 'calendar_today'
    },
    {
      name: 'Options & Futures',
      description: 'Derivatives trading',
      icon: 'swap_horiz'
    },
    {
      name: 'AI Trading',
      description: 'AI-powered trading signals and predictions',
      icon: 'psychology'
    }
  ];

  constructor(
    private stockService: StockService,
    private router: Router
  ) { }

  ngOnInit(): void {
    // Simulate loading trending stocks
    setTimeout(() => {
      this.trendingStocks$ = of(this.topSellingStocks[this.selectedCategory]);
      this.isLoading = false;
    }, 1000);
  }
  
  selectCategory(categoryId: string): void {
    this.selectedCategory = categoryId;
    this.trendingStocks$ = of(this.topSellingStocks[categoryId]);
  }

  navigateToStock(symbol: string): void {
    // Open in new window/tab per user requirement
    window.open(`/company/${symbol}`, '_blank');
  }

  getRandomImage(imageArray: string[]): string {
    const randomIndex = Math.floor(Math.random() * imageArray.length);
    return imageArray[randomIndex];
  }
}
