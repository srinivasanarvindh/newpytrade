import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-spinner',
  templateUrl: './loading-spinner.component.html',
  styleUrls: ['./loading-spinner.component.scss'],
  standalone: true,
  imports: [
    CommonModule
  ]
})
export class LoadingSpinnerComponent {
  @Input() diameter = 40;
  @Input() color = '#1e88e5';
}
