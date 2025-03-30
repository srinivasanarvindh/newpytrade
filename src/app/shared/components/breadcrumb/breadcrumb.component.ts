import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

interface BreadcrumbItem {
  label: string;
  link?: string;
}

@Component({
  selector: 'app-breadcrumb',
  templateUrl: './breadcrumb.component.html',
  styleUrls: ['./breadcrumb.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    RouterModule
  ]
})
export class BreadcrumbComponent implements OnChanges {
  @Input() items: BreadcrumbItem[] = [];
  
  displayItems: BreadcrumbItem[] = [];
  
  ngOnChanges(changes: SimpleChanges): void {
    if (changes['items']) {
      this.processItems();
    }
  }
  
  private processItems(): void {
    // Make sure there's always a home item
    if (this.items.length === 0 || this.items[0].label !== 'Home') {
      this.displayItems = [{ label: 'Home', link: '/' }, ...this.items];
    } else {
      this.displayItems = [...this.items];
    }
  }
}