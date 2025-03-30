import { Component, OnInit } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Observable, of, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, tap, catchError } from 'rxjs/operators';
import { StockService } from '../../../core/services/stock.service';
import { Stock } from '../../../core/models/stock.model';
import { CommonModule } from '@angular/common';
import { LoadingSpinnerComponent } from '../loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-stock-search',
  templateUrl: './stock-search.component.html',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    LoadingSpinnerComponent
  ],
  styleUrls: ['./stock-search.component.scss']
})
export class StockSearchComponent implements OnInit {
  searchControl = new FormControl();
  filteredStocks$!: Observable<Stock[]>;
  isLoading = false;
  searchTerms = new Subject<string>();
  showResults = false;

  constructor(
    private stockService: StockService,
    private router: Router
  ) { }

  ngOnInit(): void {
    // Preload stock list for autocomplete
    this.stockService.preloadStockList().subscribe();

    // Configure the search with debounce
    this.filteredStocks$ = this.searchControl.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      tap(() => {
        this.isLoading = true;
        this.showResults = true;
      }),
      switchMap((term: any) => {
        // Handle both string or object inputs
        const searchTerm = typeof term === 'string' ? term : (term && term.symbol ? term.symbol : '');
        
        if (!searchTerm || searchTerm.length < 2) {
          this.isLoading = false;
          return of([]);
        }
        
        console.log('Searching for:', searchTerm);
        return this.stockService.searchStocks(searchTerm).pipe(
          catchError((error) => {
            console.error('Search error:', error);
            return of([]);
          })
        );
      }),
      tap((results) => {
        console.log('Search results:', results);
        this.isLoading = false;
      })
    );
  }

  selectStock(stock: Stock): void {
    if (!stock || !stock.symbol) return;
    
    // Navigate to /company/:symbol format
    console.log('Navigating to stock:', stock.symbol);
    this.router.navigate(['/company', stock.symbol]);
    this.searchControl.setValue('');
    this.showResults = false;
  }

  displayStockName(stock: Stock): string {
    return stock ? `${stock.symbol} - ${stock.company}` : '';
  }

  hideResults(): void {
    // Delay hiding to allow click events to register
    setTimeout(() => {
      this.showResults = false;
    }, 200);
  }

  onSearchSubmit(): void {
    const searchTerm = this.searchControl.value;
    if (typeof searchTerm === 'string' && searchTerm.trim()) {
      // If it's just a string (user typed and pressed enter), try to navigate directly to that stock symbol
      // This is common in financial sites where users know the symbol
      const upperCaseSymbol = searchTerm.trim().toUpperCase();
      console.log('Direct navigation attempt to symbol:', upperCaseSymbol);
      this.router.navigate(['/company', upperCaseSymbol]);
      this.searchControl.setValue('');
      this.showResults = false;
    } else if (typeof searchTerm === 'object' && searchTerm.symbol) {
      // If it's an object (user selected from dropdown), navigate to that stock
      this.selectStock(searchTerm);
    }
  }
}
