import { Component, Input, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Stock } from '../../core/models/stock.model';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-top-stocks-table',
  templateUrl: './top-stocks-table.component.html',
  styleUrls: ['./top-stocks-table.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    LoadingSpinnerComponent,
    DecimalPipe
  ]
})
export class TopStocksTableComponent implements OnInit {
  @Input() nseStocks: Stock[] = [];
  @Input() bseStocks: Stock[] = [];
  @Input() nasdaqStocks: Stock[] = [];
  @Input() nyseStocks: Stock[] = [];
  @Input() ftseStocks: Stock[] = [];
  @Input() daxStocks: Stock[] = [];
  @Input() nikkeiStocks: Stock[] = [];
  @Input() shcompStocks: Stock[] = [];
  
  @Input() isLoadingNse = true;
  @Input() isLoadingBse = true;
  @Input() isLoadingNasdaq = true;
  @Input() isLoadingNyse = true;
  @Input() isLoadingFtse = true;
  @Input() isLoadingDax = true;
  @Input() isLoadingNikkei = true;
  @Input() isLoadingShcomp = true;
  
  @Input() nseError: string | null = null;
  @Input() bseError: string | null = null;
  @Input() nasdaqError: string | null = null;
  @Input() nyseError: string | null = null;
  @Input() ftseError: string | null = null;
  @Input() daxError: string | null = null;
  @Input() nikkeiError: string | null = null;
  @Input() shcompError: string | null = null;
  
  @Output() reloadNseStocks = new EventEmitter<void>();
  @Output() reloadBseStocks = new EventEmitter<void>();
  @Output() reloadNasdaqStocks = new EventEmitter<void>();
  @Output() reloadNyseStocks = new EventEmitter<void>();
  @Output() reloadFtseStocks = new EventEmitter<void>();
  @Output() reloadDaxStocks = new EventEmitter<void>();
  @Output() reloadNikkeiStocks = new EventEmitter<void>();
  @Output() reloadShcompStocks = new EventEmitter<void>();
  
  selectedTab: 'nse' | 'bse' | 'nasdaq' | 'nyse' | 'ftse' | 'dax' | 'nikkei' | 'shcomp' = 'nse';
  
  // Array of available tabs for navigation - public for template access
  tabs: ('nse' | 'bse' | 'nasdaq' | 'nyse' | 'ftse' | 'dax' | 'nikkei' | 'shcomp')[] = [
    'nse', 'bse', 'nasdaq', 'nyse', 'ftse', 'dax', 'nikkei', 'shcomp'
  ];
  
  // Market region mapping for better organization
  marketRegions: {[key: string]: string} = {
    'nse': 'India',
    'bse': 'India',
    'nasdaq': 'US',
    'nyse': 'US',
    'ftse': 'UK',
    'dax': 'Germany',
    'nikkei': 'Japan',
    'shcomp': 'China'
  };
  
  constructor() {}
  
  ngOnInit(): void {
    // Default to first non-loading tab
    if (this.isLoadingNse || this.nseError) {
      for (const tab of this.tabs) {
        const isLoading = this.getLoadingState(tab);
        const hasError = this.getErrorState(tab);
        if (!isLoading && !hasError) {
          this.selectedTab = tab;
          break;
        }
      }
    }
    
    // Sort stocks by symbol when data is loaded
    this.sortStocksBySymbol();
  }
  
  /**
   * Get loading state for a given tab
   */
  private getLoadingState(tab: string): boolean {
    switch(tab) {
      case 'nse': return this.isLoadingNse;
      case 'bse': return this.isLoadingBse;
      case 'nasdaq': return this.isLoadingNasdaq;
      case 'nyse': return this.isLoadingNyse;
      case 'ftse': return this.isLoadingFtse;
      case 'dax': return this.isLoadingDax;
      case 'nikkei': return this.isLoadingNikkei;
      case 'shcomp': return this.isLoadingShcomp;
      default: return true;
    }
  }
  
  /**
   * Get error state for a given tab
   */
  private getErrorState(tab: string): boolean {
    switch(tab) {
      case 'nse': return !!this.nseError;
      case 'bse': return !!this.bseError;
      case 'nasdaq': return !!this.nasdaqError;
      case 'nyse': return !!this.nyseError;
      case 'ftse': return !!this.ftseError;
      case 'dax': return !!this.daxError;
      case 'nikkei': return !!this.nikkeiError;
      case 'shcomp': return !!this.shcompError;
      default: return false;
    }
  }
  
  /**
   * Sort stock data by symbol (alphabetically)
   */
  private sortStocksBySymbol(): void {
    // We're making a copy to avoid mutating the original input
    this.nseStocks = [...this.nseStocks].sort((a, b) => a.symbol.localeCompare(b.symbol));
    this.bseStocks = [...this.bseStocks].sort((a, b) => a.symbol.localeCompare(b.symbol));
    this.nasdaqStocks = [...this.nasdaqStocks].sort((a, b) => a.symbol.localeCompare(b.symbol));
    this.nyseStocks = [...this.nyseStocks].sort((a, b) => a.symbol.localeCompare(b.symbol));
    this.ftseStocks = [...this.ftseStocks].sort((a, b) => a.symbol.localeCompare(b.symbol));
    this.daxStocks = [...this.daxStocks].sort((a, b) => a.symbol.localeCompare(b.symbol));
    this.nikkeiStocks = [...this.nikkeiStocks].sort((a, b) => a.symbol.localeCompare(b.symbol));
    this.shcompStocks = [...this.shcompStocks].sort((a, b) => a.symbol.localeCompare(b.symbol));
  }
  
  /**
   * Get stocks data for current tab
   */
  getStocksForCurrentTab(): Stock[] {
    switch(this.selectedTab) {
      case 'nse': return this.nseStocks;
      case 'bse': return this.bseStocks;
      case 'nasdaq': return this.nasdaqStocks;
      case 'nyse': return this.nyseStocks;
      case 'ftse': return this.ftseStocks;
      case 'dax': return this.daxStocks;
      case 'nikkei': return this.nikkeiStocks;
      case 'shcomp': return this.shcompStocks;
      default: return [];
    }
  }
  
  /**
   * Get error for current tab
   */
  getErrorForCurrentTab(): string | null {
    switch(this.selectedTab) {
      case 'nse': return this.nseError;
      case 'bse': return this.bseError;
      case 'nasdaq': return this.nasdaqError;
      case 'nyse': return this.nyseError;
      case 'ftse': return this.ftseError;
      case 'dax': return this.daxError;
      case 'nikkei': return this.nikkeiError;
      case 'shcomp': return this.shcompError;
      default: return null;
    }
  }
  
  /**
   * Get loading state for current tab
   */
  isCurrentTabLoading(): boolean {
    return this.getLoadingState(this.selectedTab);
  }
  
  /**
   * Emit reload event for current tab
   */
  reloadCurrentTab(): void {
    switch(this.selectedTab) {
      case 'nse': this.reloadNseStocks.emit(); break;
      case 'bse': this.reloadBseStocks.emit(); break;
      case 'nasdaq': this.reloadNasdaqStocks.emit(); break;
      case 'nyse': this.reloadNyseStocks.emit(); break;
      case 'ftse': this.reloadFtseStocks.emit(); break;
      case 'dax': this.reloadDaxStocks.emit(); break;
      case 'nikkei': this.reloadNikkeiStocks.emit(); break;
      case 'shcomp': this.reloadShcompStocks.emit(); break;
    }
  }
  
  /**
   * Select a tab to display
   */
  selectTab(tab: 'nse' | 'bse' | 'nasdaq' | 'nyse' | 'ftse' | 'dax' | 'nikkei' | 'shcomp'): void {
    this.selectedTab = tab;
  }
  
  /**
   * Navigate between tabs using prev/next buttons
   */
  navigateTabs(direction: 'prev' | 'next'): void {
    const currentIndex = this.tabs.indexOf(this.selectedTab);
    let newIndex = currentIndex;
    
    if (direction === 'prev' && currentIndex > 0) {
      newIndex = currentIndex - 1;
    } else if (direction === 'next' && currentIndex < this.tabs.length - 1) {
      newIndex = currentIndex + 1;
    }
    
    if (newIndex !== currentIndex) {
      this.selectedTab = this.tabs[newIndex];
    }
  }
  
  /**
   * Check if we can navigate to the previous tab
   */
  canNavigatePrev(): boolean {
    return this.tabs.indexOf(this.selectedTab) > 0;
  }
  
  /**
   * Check if we can navigate to the next tab
   */
  canNavigateNext(): boolean {
    return this.tabs.indexOf(this.selectedTab) < this.tabs.length - 1;
  }
  
  /**
   * Get full market name with region
   */
  getMarketDisplayName(market: string): string {
    const marketNames: {[key: string]: string} = {
      'nse': 'NSE',
      'bse': 'BSE',
      'nasdaq': 'NASDAQ',
      'nyse': 'NYSE',
      'ftse': 'FTSE 100',
      'dax': 'DAX 40',
      'nikkei': 'Nikkei 225',
      'shcomp': 'Shanghai Comp'
    };
    
    return `${marketNames[market]} (${this.marketRegions[market]})`;
  }
  
  isChangePositive(stock: Stock): boolean {
    return (stock.change ?? 0) >= 0;
  }
  
  getChangeClass(stock: Stock): string {
    return this.isChangePositive(stock) ? 'positive' : 'negative';
  }
  
  getChangeIcon(stock: Stock): string {
    return this.isChangePositive(stock) ? 'fa-caret-up' : 'fa-caret-down';
  }
  
  getCurrencySymbol(tab: string): string {
    switch(tab) {
      case 'nse':
      case 'bse':
        return '₹';
      case 'ftse':
        return '£';
      case 'dax':
        return '€';
      case 'nikkei':
        return '¥';
      case 'shcomp':
        return '¥';
      default:
        return '$';
    }
  }
}