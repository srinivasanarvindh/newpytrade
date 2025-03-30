import { Directive, Input, ElementRef, HostListener, Renderer2 } from '@angular/core';

@Directive({
  selector: '[appTooltip]'
})
export class TooltipDirective {
  @Input('appTooltip') tooltipText: string = '';
  @Input() tooltipPosition: 'top' | 'bottom' | 'left' | 'right' = 'top';
  
  private tooltip: HTMLElement | null = null;
  private delay = 300;
  private timeout: any;

  constructor(private el: ElementRef, private renderer: Renderer2) { }

  @HostListener('mouseenter') onMouseEnter() {
    this.timeout = setTimeout(() => {
      this.showTooltip();
    }, this.delay);
  }

  @HostListener('mouseleave') onMouseLeave() {
    if (this.timeout) {
      clearTimeout(this.timeout);
    }
    if (this.tooltip) {
      this.hideTooltip();
    }
  }

  private showTooltip() {
    this.tooltip = this.renderer.createElement('div');
    this.renderer.addClass(this.tooltip, 'tooltip-container');
    const text = this.renderer.createText(this.tooltipText);
    this.renderer.appendChild(this.tooltip, text);
    
    // Add position-specific class
    this.renderer.addClass(this.tooltip, `tooltip-${this.tooltipPosition}`);
    
    // Append to body
    this.renderer.appendChild(document.body, this.tooltip);
    
    // Position the tooltip
    this.positionTooltip();
    
    // Add show class for animation
    setTimeout(() => {
      if (this.tooltip) {
        this.renderer.addClass(this.tooltip, 'tooltip-show');
      }
    }, 10);
  }

  private positionTooltip() {
    if (!this.tooltip) return;
    
    const hostPos = this.el.nativeElement.getBoundingClientRect();
    const tooltipPos = this.tooltip.getBoundingClientRect();
    
    const scrollPos = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
    
    let top, left;
    
    switch (this.tooltipPosition) {
      case 'top':
        top = hostPos.top - tooltipPos.height - 10;
        left = hostPos.left + (hostPos.width - tooltipPos.width) / 2;
        break;
      case 'bottom':
        top = hostPos.bottom + 10;
        left = hostPos.left + (hostPos.width - tooltipPos.width) / 2;
        break;
      case 'left':
        top = hostPos.top + (hostPos.height - tooltipPos.height) / 2;
        left = hostPos.left - tooltipPos.width - 10;
        break;
      case 'right':
        top = hostPos.top + (hostPos.height - tooltipPos.height) / 2;
        left = hostPos.right + 10;
        break;
    }
    
    // Add scrolling position
    top += scrollPos;
    
    // Set tooltip position
    this.renderer.setStyle(this.tooltip, 'top', `${top}px`);
    this.renderer.setStyle(this.tooltip, 'left', `${left}px`);
  }

  private hideTooltip() {
    if (this.tooltip) {
      this.renderer.removeClass(this.tooltip, 'tooltip-show');
      
      // Remove from DOM after animation completes
      setTimeout(() => {
        if (this.tooltip) {
          this.renderer.removeChild(document.body, this.tooltip);
          this.tooltip = null;
        }
      }, 300);
    }
  }
}
