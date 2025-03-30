import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, of, throwError, timer } from 'rxjs';
import { catchError, map, mergeMap, retry, retryWhen, delay, take, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

// New imports for timeout handling
import { timeout, finalize } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class MainService {
  private data: any;
  public swingTrading: string = '';
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Helper method to handle HTTP errors
  private handleError(error: HttpErrorResponse, serviceName: string): Observable<never> {
    console.error(`Error in ${serviceName}:`, error);
    
    let errorMessage = '';
    
    if (error.status === 0) {
      errorMessage = `Network error: Unable to connect to the ${serviceName}. Please check your connection.`;
    } else if (error.status === 404) {
      errorMessage = `API endpoint not found: The ${serviceName} may be unavailable.`;
    } else if (error.status === 502) {
      errorMessage = `Bad Gateway: The ${serviceName} is temporarily unavailable or experiencing high load.`;
    } else if (error.status >= 500) {
      errorMessage = `Server error: The ${serviceName} is experiencing technical issues.`;
    } else {
      errorMessage = `Error in ${serviceName}: ${error.message || 'Unknown error occurred'}`;
    }
    
    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }

  // Helper method to implement retry logic
  private retryStrategy(maxRetries: number = 3, delayMs: number = 1000, serviceName: string): any {
    return retryWhen(errors => {
      return errors.pipe(
        tap(err => {
          console.log(`Retrying ${serviceName} request after error:`, err);
        }),
        mergeMap((error, i) => {
          const retryAttempt = i + 1;
          // For 5xx (except 503) and network errors, retry
          const shouldRetry = 
            (error.status === 0 || error.status === 502 || error.status === 504 || 
             (error.status >= 500 && error.status !== 503)) && 
            retryAttempt <= maxRetries;

          if (shouldRetry) {
            console.log(`Attempt ${retryAttempt} of ${maxRetries} for ${serviceName} - retrying in ${delayMs}ms`);
            return timer(delayMs * retryAttempt);
          }
          
          console.log(`Error in ${serviceName} - giving up after ${retryAttempt} attempts`);
          return throwError(() => error);
        })
      );
    });
  }

  // Get company names for different indices
  getCompaniesName(): Observable<any> {
    console.log('Fetching companies list from API');
    
    return this.http.get('/companies').pipe(
      this.retryStrategy(3, 1000, 'Company Data Service'),
      map((response: any) => {
        console.log('Successfully received companies data');
        
        // Process the response based on its format
        const processedResponse: any = {};
        
        // Check if the response matches the new format (with constituents and metadata)
        for (const indexName in response) {
          if (response.hasOwnProperty(indexName)) {
            if (response[indexName].constituents && Array.isArray(response[indexName].constituents)) {
              // New format
              console.log(`Using new response format for ${indexName}`);
              processedResponse[indexName] = response[indexName].constituents;
            } else if (Array.isArray(response[indexName])) {
              // Legacy format
              console.log(`Using legacy format for ${indexName}`);
              processedResponse[indexName] = response[indexName];
            } else {
              console.warn(`Unknown format for ${indexName}, skipping`);
              processedResponse[indexName] = [];
            }
          }
        }
        
        // Load companies count for each index
        for (const indexName in processedResponse) {
          if (processedResponse.hasOwnProperty(indexName)) {
            console.log(`Loaded ${processedResponse[indexName].length} companies for ${indexName}`);
          }
        }
        
        // Count total companies
        let totalCompanies = 0;
        for (const indexName in processedResponse) {
          if (processedResponse.hasOwnProperty(indexName)) {
            totalCompanies += processedResponse[indexName].length;
          }
        }
        
        console.log(`Total companies loaded: ${totalCompanies}`);
        return processedResponse;
      }),
      catchError(error => this.handleError(error, 'Company Data Service'))
    );
  }
  
  // Get market structure from indices endpoint
  getMarketStructure(): Observable<any> {
    console.log('Fetching market structure from indices API');
    
    return this.http.get('/api/indices').pipe(
      this.retryStrategy(3, 1000, 'Market Structure Service'),
      map((response: any) => {
        console.log('Successfully received market structure data');
        return response;
      }),
      catchError(error => this.handleError(error, 'Market Structure Service'))
    );
  }
  
  // Get constituents for a specific index
  getConstituents(indexName: string): Observable<any> {
    // Log original index name for debugging
    console.log(`Original index name: "${indexName}"`);
    
    // Create endpoint URL with proper encoding
    const encodedName = encodeURIComponent(indexName);
    const endpoint = `/api/index/${encodedName}/constituents`;
    
    console.log(`Fetching index constituents from: ${endpoint}`);
    
    return this.http.get(endpoint).pipe(
      this.retryStrategy(3, 1000, 'Index Constituents Service'),
      map((response: any) => {
        console.log(`Successfully fetched constituents for "${indexName}":`, response);
        
        // Handle both new and old response format
        if (response && response.constituents && Array.isArray(response.constituents)) {
          // New format with constituents and metadata
          console.log(`Using new response format with metadata for ${indexName}`);
          return response.constituents;
        } else if (Array.isArray(response)) {
          // Old format (directly array)
          console.log(`Using legacy array response format for ${indexName}`);
          if (response.length === 0) {
            console.warn(`Warning: Zero constituents returned for "${indexName}"`);
          }
          return response;
        } else {
          // Invalid response format
          console.error(`Invalid response format for ${indexName}:`, response);
          return [];
        }
      }),
      catchError(error => {
        console.error(`Error fetching constituents for "${indexName}"`, error);
        console.error(`Error details: ${error.status} - ${error.statusText || 'Unknown status'}`);
        
        // More detailed error logging
        if (error.error instanceof ErrorEvent) {
          console.error(`Client-side error: ${error.error.message}`);
        } else if (error.error) {
          console.error(`Server response error: ${JSON.stringify(error.error)}`);
        }
        
        return this.handleError(error, 'Index Constituents Service');
      })
    );
  }

  // Get predicted swing trading data
  getPredictedSwingTrading(tickers: string[]): Observable<any> {
    if (!tickers || tickers.length === 0) {
      console.error('No tickers provided for swing trading analysis');
      return throwError(() => new Error('No tickers provided for analysis'));
    }

    // Enhanced timeframe detection for more reliable results
    let timeframe = 'short'; // Default to short-term
    
    if (this.swingTrading) {
      const term = this.swingTrading.toLowerCase().trim();
      
      // Direct mapping based on display timeframe to backend parameter
      if (term.includes('medium')) {
        timeframe = 'medium';
        console.log('Setting timeframe to medium (Medium-Term)');
      } 
      else if (term.includes('short')) {
        timeframe = 'short';
        console.log('Setting timeframe to short (Short-Term)');
      } 
      else if (term.includes('long')) {
        timeframe = 'long';
        console.log('Setting timeframe to long (Long-Term)');
      } else {
        // Fall back to direct matching if needed
        if (term === 'medium') timeframe = 'medium';
        else if (term === 'short') timeframe = 'short';
        else if (term === 'long') timeframe = 'long';
        else {
          console.log(`Unrecognized timeframe "${this.swingTrading}", defaulting to short-term`);
        }
      }
    }
    
    console.log(`Final timeframe choice: ${timeframe} (from: ${this.swingTrading})`);
    
    // Verify that the timeframe is normalized before sending to backend
    if (timeframe === 'medium') {
      console.log('✅ Using MEDIUM timeframe in API request');
    } else if (timeframe === 'long') {
      console.log('✅ Using LONG timeframe in API request');
    } else {
      console.log('✅ Using SHORT timeframe in API request');
    }
    
    const payload = {
      ticker: tickers,
      timeframe: timeframe
    };

    console.log(`Fetching swing trading data for ${tickers.length} tickers with timeframe: ${timeframe}`);
    
    // Calculate an appropriate timeout based on number of tickers - longer for live data
    const baseTimeout = 60000; // 60 seconds base
    const timeoutPerTicker = 15000; // 15 seconds per ticker for live data
    const totalTimeout = baseTimeout + (tickers.length * timeoutPerTicker);
    
    // Log the timeout calculation
    console.log(`Setting API timeout to ${totalTimeout}ms for ${tickers.length} tickers using live data`);
    
    return this.http.post<any>(`${this.apiUrl}/trade/shorttermswingtrading`, payload).pipe(
      timeout(totalTimeout),
      tap(response => console.log(`Successfully received live swing trading data`)),
      retryWhen(this.retryStrategy(2, 5000, 'Live Swing Trading Service')), // Longer delay between retries
      catchError(error => {
        console.error('Error in live swing trading service:', error);
        
        // Check if it's a timeout error
        if (error.name === 'TimeoutError') {
          console.error(`Request timed out after ${totalTimeout}ms`);
          return throwError(() => new Error('Request timed out. The server is taking too long to retrieve live data.'));
        }
        
        // No fallback, return the error
        return this.handleError(error, 'Live Swing Trading Service');
      })
    );
  }

  // Get predicted data for one specific ticker
  getPredictedSwingTradingSingle(ticker: string): Observable<any> {
    if (!ticker) {
      console.error('No ticker provided for swing trading analysis');
      throw new Error('No ticker provided for analysis');
    }

    // Enhanced timeframe detection for more reliable results - single ticker version
    let timeframe = 'short'; // Default to short-term
    
    if (this.swingTrading) {
      const term = this.swingTrading.toLowerCase().trim();
      
      // Direct mapping based on display timeframe to backend parameter
      if (term.includes('medium')) {
        timeframe = 'medium';
        console.log('Setting timeframe to medium (Medium-Term) for single ticker');
      } 
      else if (term.includes('short')) {
        timeframe = 'short';
        console.log('Setting timeframe to short (Short-Term) for single ticker');
      } 
      else if (term.includes('long')) {
        timeframe = 'long';
        console.log('Setting timeframe to long (Long-Term) for single ticker');
      } else {
        // Fall back to direct matching if needed
        if (term === 'medium') timeframe = 'medium';
        else if (term === 'short') timeframe = 'short';
        else if (term === 'long') timeframe = 'long';
        else {
          console.log(`Unrecognized timeframe "${this.swingTrading}", defaulting to short-term`);
        }
      }
    }
    
    console.log(`Final timeframe choice for single ticker: ${timeframe} (from: ${this.swingTrading})`);
    
    // Verify that the timeframe is normalized before sending to backend
    if (timeframe === 'medium') {
      console.log('✅ Using MEDIUM timeframe in single ticker API request');
    } else if (timeframe === 'long') {
      console.log('✅ Using LONG timeframe in single ticker API request');
    } else {
      console.log('✅ Using SHORT timeframe in single ticker API request');
    }
    
    console.log(`Fetching swing trading data for ${ticker} with timeframe: ${timeframe}`);
    
    return this.http.get(`/swing-trading/${ticker}?timeframe=${timeframe}`)
      .pipe(
        timeout(45000), // 45-second timeout for single ticker requests
        retryWhen(this.retryStrategy(2, 2000, 'Swing Trading Service')),
        map(response => {
          console.log(`Successfully received data for ${ticker}`);
          return response;
        }),
        catchError(error => this.handleError(error, 'Swing Trading Service'))
      );
  }

  // Get short-term swing trading (alternative implementation)
  getShortTermSwingTrading(companies: string[]): Observable<any> {
    // For now, just use the regular swing trading endpoint
    return this.getPredictedSwingTrading(companies);
  }

  // Store data for sharing between components
  setData(data: any) {
    this.data = data;
  }

  // Get stored data
  getData() {
    return this.data;
  }

  // Store swing trading timeframe
  setSwingTrading(swingTrading: string) {
    this.swingTrading = swingTrading;
  }

  // Get stored swing trading timeframe
  getSwingTrading() {
    return this.swingTrading;
  }

  // Refresh API data cache
  refreshCache(): Observable<any> {
    console.log('Manually refreshing backend data cache');
    
    return this.http.post('/api/refresh_cache', {}).pipe(
      this.retryStrategy(2, 1000, 'Cache Refresh Service'),
      map((response: any) => {
        console.log('Cache refresh response:', response);
        return response;
      }),
      catchError(error => this.handleError(error, 'Cache Refresh Service'))
    );
  }
  
  // Get company news for a specific ticker
  getCompanyNews(ticker: string): Observable<any> {
    console.log(`Fetching news for ticker: ${ticker}`);
    
    if (!ticker) {
      console.error('No ticker provided for news retrieval');
      return throwError(() => new Error('No ticker provided for news retrieval'));
    }
    
    return this.http.get(`/api/company/${ticker}/news`).pipe(
      this.retryStrategy(3, 1000, 'Company News Service'),
      map((response: any) => {
        console.log(`Successfully received news data for ${ticker}`);
        return response;
      }),
      catchError(error => this.handleError(error, 'Company News Service'))
    );
  }

  // Get BSE stocks from dedicated endpoint
  getBSEStocks(): Observable<any[]> {
    console.log('Fetching BSE stocks from dedicated endpoint');
    
    // Use either a specialized endpoint or the BSE SENSEX constituents
    const url = `/api/index/BSE%20SENSEX/constituents`;
    
    return this.http.get<any[]>(url).pipe(
      this.retryStrategy(2, 1000, 'BSE Stocks Service'),
      map((response: any) => {
        console.log('Successfully received BSE stocks data');
        
        // Handle both response formats
        if (response && response.constituents && Array.isArray(response.constituents)) {
          console.log('Using new BSE response format with metadata');
          return response.constituents;
        } else if (Array.isArray(response)) {
          console.log('Using legacy BSE response format');
          return response;
        } else {
          console.warn('Unknown BSE response format, returning empty array');
          return [];
        }
      }),
      catchError(error => {
        console.error('Error loading BSE stocks:', error);
        return of([]); // Return empty array on failure
      })
    );
  }
  
  // Get NSE/NIFTY stocks from dedicated endpoint
  getNiftyStocks(): Observable<any[]> {
    console.log('Fetching NIFTY stocks from dedicated endpoint');
    
    // Use NIFTY 50 constituents endpoint
    const url = `/api/index/NIFTY%2050/constituents`;
    
    return this.http.get<any[]>(url).pipe(
      this.retryStrategy(2, 1000, 'NIFTY Stocks Service'),
      map((response: any) => {
        console.log('Successfully received NIFTY stocks data');
        
        // Handle both response formats
        if (response && response.constituents && Array.isArray(response.constituents)) {
          console.log('Using new NIFTY response format with metadata');
          return response.constituents;
        } else if (Array.isArray(response)) {
          console.log('Using legacy NIFTY response format');
          return response;
        } else {
          console.warn('Unknown NIFTY response format, returning empty array');
          return [];
        }
      }),
      catchError(error => {
        console.error('Error loading NIFTY stocks:', error);
        return of([]); // Return empty array on failure
      })
    );
  }

  getToolsData(): Observable<any> {
    return this.http.get('/tools');
  }

  getSwingTradeData(tickers: string[]): Observable<any> {
    return this.http.post('/swing-trade', { tickers });
  }
}