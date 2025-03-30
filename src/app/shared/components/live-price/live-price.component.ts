import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import { WebSocketService } from '../../../core/services/websocket.service';
import { CommonModule, DatePipe } from '@angular/common';

@Component({
  selector: 'app-live-price',
  templateUrl: './live-price.component.html',
  styleUrls: ['./live-price.component.css'],
  standalone: true,
  imports: [CommonModule, DatePipe]
})
export class LivePriceComponent implements OnInit, OnDestroy {
  @Input() symbol: string = '';
  
  price: number | null = null;
  change: number | null = null;
  changePercent: number | null = null;
  high: number | null = null;
  low: number | null = null;
  volume: number | null = null;
  timestamp: string | null = null;
  currency: string = 'USD';
  
  isConnected: boolean = false;
  isLoading: boolean = true;
  hasData: boolean = false;
  
  private priceSubscription?: Subscription;
  private connectionSubscription?: Subscription;
  
  constructor(private webSocketService: WebSocketService) { }
  
  ngOnInit(): void {
    // Monitor connection status
    this.connectionSubscription = this.webSocketService.connectionStatus$.subscribe(
      connected => {
        this.isConnected = connected;
        if (connected && this.symbol) {
          this.subscribeToSymbol();
        }
      }
    );
    
    // Connect to WebSocket server
    this.webSocketService.connect();
    
    // Subscribe to real-time updates if we have a symbol
    if (this.symbol) {
      this.subscribeToSymbol();
    }
  }
  
  ngOnDestroy(): void {
    // Unsubscribe from WebSocket updates
    if (this.symbol) {
      this.webSocketService.unsubscribeFromSymbol(this.symbol);
    }
    
    // Clean up subscriptions
    if (this.priceSubscription) {
      this.priceSubscription.unsubscribe();
    }
    
    if (this.connectionSubscription) {
      this.connectionSubscription.unsubscribe();
    }
  }
  
  private subscribeToSymbol(): void {
    // Subscribe to price updates for this symbol
    this.priceSubscription = this.webSocketService.getPriceUpdates(this.symbol).subscribe(
      data => {
        if (data) {
          this.price = data.price;
          this.change = data.change;
          this.changePercent = data.changePercent;
          this.high = data.high;
          this.low = data.low;
          this.volume = data.volume;
          this.timestamp = data.timestamp;
          this.currency = data.currency || 'USD';
          
          this.isLoading = false;
          this.hasData = true;
        }
      }
    );
    
    // Subscribe to updates through WebSocket
    this.webSocketService.subscribeToSymbol(this.symbol);
  }
  
  /**
   * Format the price with the appropriate currency symbol
   */
  get formattedPrice(): string {
    if (this.price === null) return '–';
    
    const currencySymbol = this.getCurrencySymbol();
    return `${currencySymbol}${this.price.toFixed(2)}`;
  }
  
  /**
   * Format the change with the appropriate currency symbol
   */
  get formattedChange(): string {
    if (this.change === null) return '–';
    
    const sign = this.change >= 0 ? '+' : '';
    const currencySymbol = this.getCurrencySymbol();
    return `${sign}${currencySymbol}${this.change.toFixed(2)} (${sign}${this.changePercent?.toFixed(2)}%)`;
  }
  
  /**
   * Get the appropriate CSS class for price changes
   */
  get changeClass(): string {
    if (this.change === null) return '';
    return this.change > 0 ? 'text-success' : this.change < 0 ? 'text-danger' : '';
  }
  
  /**
   * Get the appropriate icon for price changes
   */
  get changeIcon(): string {
    if (this.change === null) return '';
    return this.change > 0 ? 'trending_up' : this.change < 0 ? 'trending_down' : 'trending_flat';
  }
  
  /**
   * Get the appropriate currency symbol
   */
  getCurrencySymbol(): string {
    switch (this.currency) {
      case 'USD': return '$';
      case 'EUR': return '€';
      case 'GBP': return '£';
      case 'JPY': return '¥';
      case 'INR': return '₹';
      default: return '$';
    }
  }
}