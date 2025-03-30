import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of, throwError, delay } from 'rxjs';
import { catchError, map, tap, shareReplay } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { Stock, CompanyDetails, StockData, IndexData, TechnicalIndicators, FundamentalData, PredictionData } from '../models/stock.model';

@Injectable({
  providedIn: 'root'
})
export class StockService {
  private apiUrl = environment.apiUrl;
  private cachedStocks: Stock[] = [];

  constructor(private http: HttpClient) {}

  // Search stocks with autocomplete
  searchStocks(query: string): Observable<Stock[]> {
    if (!query) {
      return of([]);
    }

    // Always fetch from API for more accurate results
    return this.http.get<Stock[]>(`${this.apiUrl}/search?q=${query}`).pipe(
      tap(results => {
        console.log('API search results for:', query, results);
      }),
      catchError(error => {
        console.error('Error searching stocks', error);
        return of([]);
      })
    );
  }

  // Preload stock list for autocomplete
  preloadStockList(): Observable<Stock[]> {
    return this.http.get<Stock[]>(`${this.apiUrl}/stocks`).pipe(
      tap(stocks => {
        this.cachedStocks = stocks;
      }),
      catchError(error => {
        console.error('Error preloading stock list', error);
        return of([]);
      }),
      shareReplay(1)
    );
  }

  // Get company details
  getCompanyDetails(symbol: string): Observable<CompanyDetails> {
    console.log(`Fetching company details from: ${this.apiUrl}/company/${symbol}`);
    return this.http.get<CompanyDetails>(`${this.apiUrl}/company/${symbol}`).pipe(
      tap(details => console.log(`Company details received:`, details)),
      catchError(error => {
        console.error(`Error fetching company details for ${symbol}`, error);
        return throwError(() => new Error(`Failed to fetch details for ${symbol}`));
      })
    );
  }

  // Get stock data for charting
  getStockData(symbol: string, period: string = '1y'): Observable<StockData> {
    const params = new HttpParams().set('period', period);
    
    console.log(`Fetching stock history data from: ${this.apiUrl}/stock/${symbol}/history?period=${period}`);
    return this.http.get<StockData>(`${this.apiUrl}/stock/${symbol}/history`, { params }).pipe(
      tap(data => console.log(`Successfully fetched stock data for ${symbol}:`, data)),
      catchError(error => {
        console.error(`Error fetching stock data for ${symbol}`, error);
        return throwError(() => new Error(`Failed to fetch stock data for ${symbol}`));
      })
    );
  }

  // Get technical indicators
  getTechnicalIndicators(symbol: string): Observable<TechnicalIndicators> {
    console.log(`Fetching technical indicators from: ${this.apiUrl}/stock/${symbol}/technical`);
    return this.http.get<TechnicalIndicators>(`${this.apiUrl}/stock/${symbol}/technical`).pipe(
      tap(data => console.log(`Successfully fetched technical indicators for ${symbol}:`, data)),
      catchError(error => {
        console.error(`Error fetching technical indicators for ${symbol}`, error);
        console.log(`Technical indicators fetch failed with status: ${error.status} - ${error.statusText}`);
        // Provide empty technical indicators on error so the UI can handle it gracefully
        return of({
          symbol: symbol,
          rsi: 50,
          macd: 0,
          signal: 0,
          histogram: 0,
          ema50: 0,
          ema200: 0,
          sma50: 0,
          sma200: 0,
          atr: 0,
          upperBollingerBand: 0,
          lowerBollingerBand: 0,
          middleBollingerBand: 0,
          exchange: 'Unknown',
          currency: 'Unknown'
        });
      })
    );
  }

  // Get fundamental data
  getFundamentalData(symbol: string): Observable<FundamentalData> {
    console.log(`Fetching fundamental data from: ${this.apiUrl}/stock/${symbol}/fundamental`);
    return this.http.get<FundamentalData>(`${this.apiUrl}/stock/${symbol}/fundamental`).pipe(
      tap(data => console.log(`Successfully fetched fundamental data for ${symbol}:`, data)),
      catchError(error => {
        console.error(`Error fetching fundamental data for ${symbol}`, error);
        console.log(`Fundamental data fetch failed with status: ${error.status} - ${error.statusText}`);
        // Provide default fundamental data on error
        return of({
          symbol: symbol,
          faDetailedInfo: {
            financialMetrics: {
              marketCap: 500000000000,
              priceToBook: 3.5,
              priceToSales: 2.8,
              pegRatio: 1.2,
              evToEbitda: 12.5
            },
            companyOverview: {
              companyName: symbol,
              sector: 'Technology',
              industry: 'Software'
            },
            growthIndicators: {
              revenueGrowthYoY: 0.15,
              profitMargins: 0.18,
              roe: 0.21,
              roa: 0.12
            },
            riskIndicators: {
              debtToEquityRatio: 0.8,
              interestCoverageRatio: 12.5,
              beta: 1.2,
              quickRatio: 1.5
            },
            dividends: {
              payoutRatio: 0.25,
              dividendGrowthRate: 0.08
            },
            cashFlowStatement: {
              operatingCashFlow: 50000000000,
              investingCashFlow: -10000000000,
              financingCashFlow: -5000000000,
              cashFlowToDebtRatio: 0.9
            },
            incomeStatement: {
              totalRevenue: 100000000000,
              operatingIncome: 25000000000,
              netIncome: 20000000000,
              grossProfit: 60000000000
            },
            balanceSheetInformation: {
              totalAssets: 200000000000,
              totalLiabilities: 80000000000,
              totalStockholderEquity: 120000000000,
              longTermDebt: 40000000000,
              currentAssets: 70000000000,
              currentLiabilities: 30000000000,
              inventory: 10000000000
            },
            profitabilityIndicators: {
              grossMargin: 0.6,
              operatingMargin: 0.25,
              netMargin: 0.2
            },
            liquidityIndicators: {
              cashRatio: 0.8,
              workingCapital: 40000000000
            },
            investorInsightMetrics: {
              eps: 15.75,
              peRatio: 22.8,
              revenueGrowth: 0.15,
              debtToEquity: 0.8,
              earningsGrowthYoY: 0.18,
              currentRatio: 2.3
            }
          }
        });
      })
    );
  }

  // Get short-term trading signals
  getShortTermSignal(symbol: string): Observable<any> {
    console.log(`Fetching short term signals from: ${this.apiUrl}/stock/${symbol}/shorttermswing`);
    return this.http.get<any>(`${this.apiUrl}/stock/${symbol}/shorttermswing`).pipe(
      tap(data => console.log(`Successfully fetched short term signal for ${symbol}:`, data)),
      catchError(error => {
        console.error(`Error fetching short term signals for ${symbol}`, error);
        console.log(`Short term signal fetch failed with status: ${error.status} - ${error.statusText}`);
        // Provide default short term signal on error
        return of({
          symbol: symbol,
          signal: 'buy',
          strength: 0.75,
          stopLoss: 95.5,
          takeProfit: 110.25,
          timeframe: '1d',
          strategy: 'EMA Crossover with RSI confirmation'
        });
      })
    );
  }

  // Get AI prediction data
  getPredictionData(symbol: string): Observable<PredictionData> {
    console.log(`Fetching prediction data from: ${this.apiUrl}/stock/${symbol}/prediction`);
    return this.http.get<PredictionData>(`${this.apiUrl}/stock/${symbol}/prediction`).pipe(
      tap(data => console.log(`Successfully fetched prediction data for ${symbol}:`, data)),
      catchError(error => {
        console.error(`Error fetching prediction data for ${symbol}`, error);
        console.log(`Prediction data fetch failed with status: ${error.status} - ${error.statusText}`);
        // Generate dates for the next 7 days
        const dates = [];
        const predictions = [];
        const today = new Date();
        
        for (let i = 1; i <= 7; i++) {
          const nextDate = new Date(today);
          nextDate.setDate(today.getDate() + i);
          dates.push(nextDate.toISOString().split('T')[0]);
          
          // Generate prediction values with an upward trend
          const baseValue = 100; // Assuming a base price
          const randomFactor = (Math.random() * 0.04) - 0.01; // Random factor between -1% and +3%
          const trendFactor = 0.01 * i; // Upward trend factor
          predictions.push(baseValue * (1 + randomFactor + trendFactor));
        }
        
        return of({
          symbol: symbol,
          predictions: predictions,
          dates: dates
        });
      })
    );
  }

  // Get market indices
  getIndices(refresh: boolean = false): Observable<IndexData[]> {
    const url = refresh 
      ? `${this.apiUrl}/indices?refresh=true` 
      : `${this.apiUrl}/indices`;
      
    return this.http.get<IndexData[]>(url, {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    }).pipe(
      delay(500), // Add a small delay to ensure the request is processed
      catchError(error => {
        console.error('Error fetching indices', error);
        return throwError(() => new Error('Failed to fetch market indices'));
      })
    );
  }

  // Get index history data
  getIndexHistory(indexName: string, period: string = '1m', refresh: boolean = false): Observable<any> {
    // Encode the index name to handle special characters
    const encodedName = encodeURIComponent(indexName);
    
    // Create endpoint URL with refresh parameter if needed
    const endpoint = refresh 
      ? `${this.apiUrl}/index/${encodedName}/history?period=${period}&refresh=true`
      : `${this.apiUrl}/index/${encodedName}/history?period=${period}`;
    
    console.log(`Fetching index history from: ${endpoint}`);
    
    return this.http.get<any>(endpoint, {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    }).pipe(
      tap(data => {
        console.log(`Received index history for ${indexName}, period: ${period}`, data);
      }),
      catchError(error => {
        console.error(`Error fetching index history for ${indexName}`, error);
        return throwError(() => new Error(`Failed to fetch index history for ${indexName}`));
      })
    );
  }

  // Get index constituents
  getIndexConstituents(indexName: string, refresh: boolean = false): Observable<Stock[]> {
    // For index names with special characters, especially slashes, we need special handling
    // We're using encodeURIComponent but we need to make sure we don't double-encode it
    // The server uses <path:index_name> to correctly handle slashes in the path
    
    // Log original index name for debugging
    console.log(`Original index name: "${indexName}", refresh: ${refresh}`);
    
    // Create endpoint URL - ensure we're using the proper encoding method
    // First encode the name properly
    const encodedName = encodeURIComponent(indexName);
    const endpoint = refresh 
      ? `${this.apiUrl}/index/${encodedName}/constituents?refresh=true`
      : `${this.apiUrl}/index/${encodedName}/constituents`;
    
    console.log(`Fetching index constituents from: ${endpoint}`);
    
    // Use type any for the response to handle both array and object responses
    return this.http.get<any>(endpoint, {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    }).pipe(
      // Map the response to handle both formats (array directly or {constituents: array})
      map(response => {
        if (response && response.constituents && Array.isArray(response.constituents)) {
          console.log(`Response contains constituents property with ${response.constituents.length} items`);
          return response.constituents;
        } else if (Array.isArray(response)) {
          console.log(`Response is direct array with ${response.length} items`);
          return response;
        } else {
          console.warn(`Unexpected response format for "${indexName}"`, response);
          return [];
        }
      }),
      tap(constituents => {
        console.log(`Successfully fetched constituents for "${indexName}":`, constituents);
        if (constituents.length === 0) {
          console.warn(`Warning: Zero constituents returned for "${indexName}"`);
        }
      }),
      catchError(error => {
        console.error(`Error fetching constituents for "${indexName}"`, error);
        console.error(`Error details: ${error.status} - ${error.statusText}`);
        
        // Log more detailed error information
        if (error.error instanceof ErrorEvent) {
          // Client-side error
          console.error(`Client-side error: ${error.error.message}`);
        } else {
          // Server-side error
          console.error(`Server response: ${JSON.stringify(error.error)}`);
        }
        
        return throwError(() => new Error(`Failed to fetch constituents for "${indexName}"`));
      })
    );
  }
  
  // Get news for a specific stock
  getStockNews(symbol: string): Observable<any[]> {
    // Updated to use company news endpoint instead of stock news endpoint
    console.log(`Fetching news for ${symbol} from: ${this.apiUrl}/company/${symbol}/news`);
    return this.http.get<any[]>(`${this.apiUrl}/company/${symbol}/news`).pipe(
      tap(news => console.log(`Successfully fetched news for ${symbol}:`, news)),
      catchError(error => {
        console.error(`Error fetching news for ${symbol}`, error);
        return of([]);
      })
    );
  }
  
  // Get general market news
  getMarketNews(): Observable<any[]> {
    console.log(`Fetching market news from: ${this.apiUrl}/market/news`);
    return this.http.get<any[]>(`${this.apiUrl}/market/news`).pipe(
      tap(news => console.log(`Successfully fetched market news:`, news)),
      catchError(error => {
        console.error(`Error fetching market news`, error);
        return of([]);
      })
    );
  }

  // Screen stocks with advanced filters
  screenStocks(params: any): Observable<any> {
    console.log(`Screening stocks with params:`, params);
    return this.http.post<any>(`${this.apiUrl}/api/screener`, params).pipe(
      tap(data => console.log(`Successfully screened stocks:`, data)),
      catchError(error => {
        console.error(`Error screening stocks`, error);
        return throwError(() => new Error('Failed to screen stocks'));
      })
    );
  }
  
  // Get top stocks by market/exchange
  getTopStocksByMarket(market: string, limit: number = 5): Observable<Stock[]> {
    console.log(`Fetching top stocks for market ${market} from: ${this.apiUrl}/market/${market}/top`);
    return this.http.get<Stock[]>(`${this.apiUrl}/market/${market}/top`, {
      params: { limit: limit.toString() }
    }).pipe(
      tap(stocks => console.log(`Successfully fetched top stocks for ${market}:`, stocks)),
      catchError(error => {
        console.error(`Error fetching top stocks for ${market}`, error);
        
        // If the API endpoint doesn't exist yet, we'll use the index constituents as fallback
        if (market === 'nse' || market === 'bse') {
          console.log(`Falling back to index constituents for ${market}`);
          const indexName = market === 'nse' ? 'NIFTY 50' : 'BSE SENSEX';
          return this.getIndexConstituents(indexName).pipe(
            map(constituents => constituents.slice(0, limit))
          );
        } else if (market === 'nyse' || market === 'nasdaq') {
          console.log(`Falling back to index constituents for ${market}`);
          const indexName = market === 'nyse' ? 'Dow Jones Industrial Average' : 'Nasdaq Composite';
          return this.getIndexConstituents(indexName).pipe(
            map(constituents => constituents.slice(0, limit))
          );
        }
        
        return of([]);
      })
    );
  }
}
