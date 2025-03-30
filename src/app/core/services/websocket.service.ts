import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface WebSocketMessage {
  type: string;
  symbol?: string;
  data?: any;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000; // 3 seconds
  private reconnectTimeoutId: any;
  private pingIntervalId: any;

  private connectionStatus = new BehaviorSubject<boolean>(false);
  public connectionStatus$ = this.connectionStatus.asObservable();

  private messageSubject = new Subject<WebSocketMessage>();
  public messages$ = this.messageSubject.asObservable();

  private priceUpdates: { [symbol: string]: BehaviorSubject<any> } = {};

  constructor() { }

  /**
   * Connect to the WebSocket server
   */
  public connect(): void {
    if (this.socket && this.isConnected()) {
      return; // Already connected
    }

    // Clear any existing reconnect timeout
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;
      
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = this.onOpen.bind(this);
      this.socket.onmessage = this.onMessage.bind(this);
      this.socket.onclose = this.onClose.bind(this);
      this.socket.onerror = this.onError.bind(this);
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from the WebSocket server
   */
  public disconnect(): void {
    this.clearTimers();

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    this.connectionStatus.next(false);
  }

  /**
   * Subscribe to price updates for a symbol
   */
  public subscribeToSymbol(symbol: string): void {
    if (!symbol) return;
    
    // Create a new subject for this symbol if it doesn't exist
    if (!this.priceUpdates[symbol]) {
      this.priceUpdates[symbol] = new BehaviorSubject<any>(null);
    }

    // Send subscription message to server if connected
    if (this.isConnected()) {
      this.sendMessage({
        action: 'subscribe',
        symbol: symbol
      });
    }
  }

  /**
   * Unsubscribe from price updates for a symbol
   */
  public unsubscribeFromSymbol(symbol: string): void {
    if (!symbol) return;

    // Send unsubscribe message to server if connected
    if (this.isConnected()) {
      this.sendMessage({
        action: 'unsubscribe',
        symbol: symbol
      });
    }
  }

  /**
   * Get price updates for a specific symbol
   */
  public getPriceUpdates(symbol: string): Observable<any> {
    if (!this.priceUpdates[symbol]) {
      this.priceUpdates[symbol] = new BehaviorSubject<any>(null);
    }
    return this.priceUpdates[symbol].asObservable();
  }

  /**
   * Send a message to the WebSocket server
   */
  private sendMessage(message: any): void {
    if (this.isConnected()) {
      this.socket!.send(JSON.stringify(message));
    }
  }

  /**
   * Check if WebSocket is connected
   */
  private isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }

  /**
   * Handle WebSocket open event
   */
  private onOpen(event: Event): void {
    console.log('WebSocket connected');
    this.connectionStatus.next(true);
    this.reconnectAttempts = 0;

    // Subscribe to all symbols
    Object.keys(this.priceUpdates).forEach(symbol => {
      this.subscribeToSymbol(symbol);
    });

    // Start ping interval
    this.startPingInterval();
  }

  /**
   * Handle WebSocket message event
   */
  private onMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data) as WebSocketMessage;
      
      // Handle different message types
      switch (message.type) {
        case 'price_update':
          if (message.symbol && message.data) {
            // Update price data for the symbol
            if (this.priceUpdates[message.symbol]) {
              this.priceUpdates[message.symbol].next(message.data);
            }
          }
          break;
        
        case 'pong':
          // Ping response received
          break;
        
        default:
          // Forward all messages to general message stream
          this.messageSubject.next(message);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket close event
   */
  private onClose(event: CloseEvent): void {
    console.log('WebSocket disconnected, code:', event.code, 'reason:', event.reason);
    this.socket = null;
    this.connectionStatus.next(false);
    this.clearTimers();

    // Schedule reconnect
    this.scheduleReconnect();
  }

  /**
   * Handle WebSocket error event
   */
  private onError(event: Event): void {
    console.error('WebSocket error:', event);
    // The onClose handler will be called after this
  }

  /**
   * Schedule a reconnection attempt
   */
  private scheduleReconnect(): void {
    // Only reconnect if we haven't exceeded the max attempts
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      
      const delay = this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1);
      console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
      
      this.reconnectTimeoutId = setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect();
      }, delay);
    } else {
      console.error(`Failed to reconnect after ${this.maxReconnectAttempts} attempts`);
    }
  }

  /**
   * Start a ping interval to keep the connection alive
   */
  private startPingInterval(): void {
    // Clear any existing interval
    if (this.pingIntervalId) {
      clearInterval(this.pingIntervalId);
    }

    // Send a ping message every 30 seconds
    this.pingIntervalId = setInterval(() => {
      if (this.isConnected()) {
        this.sendMessage({ action: 'ping' });
      } else {
        // If we're not connected, clear the interval
        clearInterval(this.pingIntervalId);
      }
    }, 30000);
  }

  /**
   * Clear all timers
   */
  private clearTimers(): void {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    if (this.pingIntervalId) {
      clearInterval(this.pingIntervalId);
      this.pingIntervalId = null;
    }
  }
}