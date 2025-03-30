import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { TradingTerm, TradingTermDetail } from '@core/models/stock.model';

@Component({
  selector: 'app-trading-term-selector',
  templateUrl: './trading-term-selector.component.html',
  styleUrls: ['./trading-term-selector.component.scss']
})
export class TradingTermSelectorComponent implements OnChanges {
  @Input() availableTerms: TradingTermDetail[] = [];
  @Input() selectedTerm: TradingTerm = TradingTerm.INTRADAY;
  @Output() termChanged = new EventEmitter<TradingTerm>();
  
  displayTerms: TradingTermDetail[] = [];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['availableTerms']) {
      this.displayTerms = this.availableTerms.filter(term => term.suitable);
      
      // If selectedTerm is not suitable, select the first suitable one
      if (this.displayTerms.length > 0 && !this.displayTerms.some(term => term.id === this.selectedTerm)) {
        this.selectTerm(this.displayTerms[0].id);
      }
    }
  }

  selectTerm(term: TradingTerm): void {
    this.selectedTerm = term;
    this.termChanged.emit(term);
  }
}
