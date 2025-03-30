import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class MainService {
  private apiUrl = 'http://localhost:5010'; // Default to local dev server
  private data: any = null;
  private swingTrading: string = '';

  constructor(private http: HttpClient) { }

  setData(data: any): void {
    this.data = data;
  }

  getData(): any {
    return this.data;
  }

  setSwingTrading(data: string): void {
    this.swingTrading = data;
  }

  getSwingTrading(): string {
    return this.swingTrading;
  }

  getCompanies(country: string, market: string, division: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/companies`)
      .pipe(
        map((response: any) => {
          // Filter based on parameters if needed
          return response;
        }),
        catchError(error => {
          console.error('Error fetching companies:', error);
          return of([]);
        })
      );
  }

  getPredictedSwingTrading(tickers: any[]): Observable<any> {
    const tickersArray = tickers.map(item => item.symbol);
    const payload = {
      tickers: tickersArray,
      timeframe: this.swingTrading.toLowerCase().includes('short') ? 'short' : 
                this.swingTrading.toLowerCase().includes('medium') ? 'medium' : 'long'
    };

    return this.http.post(`${this.apiUrl}/api/swing-trading`, payload)
      .pipe(
        map((response: any) => {
          return response.map((item: any, index: number) => {
            return {
              symbol: tickers[index].symbol,
              company: tickers[index].company,
              result: item
            };
          });
        }),
        catchError(error => {
          console.error('Error fetching swing trading prediction:', error);
          return of([]);
        })
      );
  }

  getPredictedSwingTradingSingle(ticker: string): Observable<any> {
    const timeframe = this.swingTrading.toLowerCase().includes('short') ? 'short' : 
                     this.swingTrading.toLowerCase().includes('medium') ? 'medium' : 'long';
    
    return this.http.get(`${this.apiUrl}/api/swing-trading/${ticker}?timeframe=${timeframe}`)
      .pipe(
        catchError(error => {
          console.error(`Error fetching swing trading prediction for ${ticker}:`, error);
          return of({ error: 'Failed to fetch data' });
        })
      );
  }
}