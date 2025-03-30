import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Router } from '@angular/router';
import { Observable, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, catchError } from 'rxjs/operators';
import { StockService } from '@core/services/stock.service';
import { Stock } from '@core/models/stock.model';

// Interface for autocomplete suggestions
interface StockOption {
  symbol: string;
  company?: string;
}

@Component({
  selector: 'app-search-bar',
  templateUrl: './search-bar.component.html',
  styleUrls: ['./search-bar.component.scss']
})
export class SearchBarComponent implements OnInit {
  searchControl = new FormControl('');
  filteredOptions!: Observable<StockOption[]>;
  isLoading = false;

  constructor(
    private stockService: StockService,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.filteredOptions = this.searchControl.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(value => {
        if (value && typeof value === 'string' && value.length > 1) {
          this.isLoading = true;
          return this.stockService.searchStocks(value).pipe(
            catchError(() => {
              this.isLoading = false;
              return of([]);
            })
          );
        }
        return of([]);
      }),
      catchError(() => {
        this.isLoading = false;
        return of([]);
      })
    );

    // Reset loading state after results are loaded
    this.filteredOptions.subscribe(() => {
      this.isLoading = false;
    });
  }

  displayFn(stock: Stock | StockOption | null): string {
    return stock && 'symbol' in stock ? `${stock.symbol} - ${stock.company || ''}` : '';
  }

  onOptionSelected(stock: Stock | StockOption): void {
    if (stock && 'symbol' in stock) {
      // Open in new window/tab per user requirement
      window.open(`/company/${stock.symbol}`, '_blank');
      this.searchControl.setValue('');
    }
  }

  onSubmit(): void {
    const value = this.searchControl.value;
    if (typeof value === 'string' && value.trim()) {
      // Extract the ticker symbol if the user typed in "SYMBOL - Company Name" format
      const match = value.match(/^([A-Za-z0-9.-]+)/);
      if (match && match[1]) {
        // Open in new window/tab per user requirement
        window.open(`/company/${match[1]}`, '_blank');
        this.searchControl.setValue('');
      }
    } else if (value && typeof value === 'object') {
      // Type guard to check if it's a StockOption with a symbol property
      if ('symbol' in value && typeof value.symbol === 'string') {
        // Open in new window/tab per user requirement
        window.open(`/company/${value.symbol}`, '_blank');
        this.searchControl.setValue('');
      }
    }
  }
}
