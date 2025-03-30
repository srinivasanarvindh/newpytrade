import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { LivePriceComponent } from './components/live-price/live-price.component';

const MODULES = [
  CommonModule,
  RouterModule,
  FormsModule,
  ReactiveFormsModule,
  HttpClientModule
];

// LivePriceComponent is now a standalone component, so we don't include it in COMPONENTS
const COMPONENTS: any[] = [];

const STANDALONE_COMPONENTS = [
  LivePriceComponent
];

@NgModule({
  declarations: [...COMPONENTS],
  imports: [
    ...MODULES,
    ...STANDALONE_COMPONENTS
  ],
  exports: [
    ...MODULES,
    ...COMPONENTS,
    ...STANDALONE_COMPONENTS
  ]
})
export class SharedModule { }
