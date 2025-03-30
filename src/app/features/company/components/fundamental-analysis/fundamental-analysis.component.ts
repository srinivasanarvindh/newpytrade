import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { FundamentalData } from '@core/models/stock.model';

interface FundamentalIndicator {
  name: string;
  value: number | string;
  status: 'positive' | 'negative' | 'neutral';
  change?: number;
  description: string;
}

interface FundamentalGroup {
  name: string;
  indicators: FundamentalIndicator[];
}

@Component({
  selector: 'app-fundamental-analysis',
  templateUrl: './fundamental-analysis.component.html',
  styleUrls: ['./fundamental-analysis.component.scss']
})
export class FundamentalAnalysisComponent implements OnChanges {
  @Input() fundamentalData: FundamentalData | null = null;
  @Input() isLoading: boolean = true;

  fundamentalGroups: FundamentalGroup[] = [];
  overallScore: number = 0;
  scoreCategory: 'strong' | 'moderate' | 'weak' = 'moderate';
  
  // Company overview
  companyName: string = '';
  sector: string = '';
  industry: string = '';
  
  // Key metrics
  eps: number | null = null;
  peRatio: number | null = null;
  revenueGrowth: number | null = null;
  debtToEquity: number | null = null;

  constructor() { }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['fundamentalData'] && this.fundamentalData) {
      this.processFundamentalData();
    }
  }

  private processFundamentalData(): void {
    if (!this.fundamentalData) {
      return;
    }
    
    // Extract company overview
    if (this.fundamentalData.companyOverview) {
      this.companyName = this.fundamentalData.companyOverview['Company Name'] || '';
      this.sector = this.fundamentalData.companyOverview['Sector'] || '';
      this.industry = this.fundamentalData.companyOverview['Industry'] || '';
    }
    
    // Extract key metrics
    if (this.fundamentalData.investorInsightMetrics) {
      this.eps = this.fundamentalData.investorInsightMetrics['EPS'] || null;
      this.peRatio = this.fundamentalData.investorInsightMetrics['P/E Ratio'] || null;
      this.revenueGrowth = this.fundamentalData.investorInsightMetrics['Revenue Growth'] || null;
      this.debtToEquity = this.fundamentalData.investorInsightMetrics['Debt-to-Equity Ratio'] || null;
    }
    
    // Calculate overall score
    this.overallScore = this.fundamentalData.overall_fa_score || this.calculateOverallScore();
    
    // Determine score category
    if (this.overallScore >= 70) {
      this.scoreCategory = 'strong';
    } else if (this.overallScore >= 40) {
      this.scoreCategory = 'moderate';
    } else {
      this.scoreCategory = 'weak';
    }
    
    // Organize indicators into groups
    this.organizeIndicators();
  }

  private calculateOverallScore(): number {
    // Calculate a simple score based on key metrics
    let score = 50; // Start with neutral score
    
    if (this.fundamentalData) {
      // EPS - positive EPS is good
      if (this.eps && this.eps > 0) {
        score += 10;
      } else if (this.eps && this.eps < 0) {
        score -= 10;
      }
      
      // P/E Ratio - lower is better (but not negative)
      if (this.peRatio && this.peRatio > 0 && this.peRatio < 15) {
        score += 10;
      } else if (this.peRatio && this.peRatio > 30) {
        score -= 5;
      }
      
      // Revenue Growth - higher is better
      if (this.revenueGrowth && this.revenueGrowth > 0.10) {
        score += 10;
      } else if (this.revenueGrowth && this.revenueGrowth < 0) {
        score -= 10;
      }
      
      // Debt-to-Equity - lower is better
      if (this.debtToEquity && this.debtToEquity < 1) {
        score += 10;
      } else if (this.debtToEquity && this.debtToEquity > 2) {
        score -= 10;
      }
    }
    
    return Math.min(100, Math.max(0, score));
  }

  private organizeIndicators(): void {
    this.fundamentalGroups = [];
    
    if (!this.fundamentalData) {
      return;
    }
    
    // Valuation metrics
    const valuationIndicators: FundamentalIndicator[] = [];
    if (this.fundamentalData.financialMetrics) {
      if (this.fundamentalData.financialMetrics['Market Cap'] !== undefined) {
        valuationIndicators.push({
          name: 'Market Cap',
          value: this.formatCurrency(this.fundamentalData.financialMetrics['Market Cap']),
          status: 'neutral',
          description: 'Total market value of a company\'s outstanding shares'
        });
      }
      
      if (this.fundamentalData.financialMetrics['Price-to-Book (P/B) Ratio'] !== undefined) {
        const pbRatio = this.fundamentalData.financialMetrics['Price-to-Book (P/B) Ratio'];
        valuationIndicators.push({
          name: 'P/B Ratio',
          value: this.formatNumber(pbRatio),
          status: pbRatio < 3 ? 'positive' : (pbRatio > 5 ? 'negative' : 'neutral'),
          description: 'Price-to-Book ratio compares a company\'s market value to its book value'
        });
      }
      
      if (this.fundamentalData.financialMetrics['Price-to-Sales (P/S) Ratio'] !== undefined) {
        const psRatio = this.fundamentalData.financialMetrics['Price-to-Sales (P/S) Ratio'];
        valuationIndicators.push({
          name: 'P/S Ratio',
          value: this.formatNumber(psRatio),
          status: psRatio < 2 ? 'positive' : (psRatio > 4 ? 'negative' : 'neutral'),
          description: 'Price-to-Sales ratio compares a company\'s market value to its revenue'
        });
      }
      
      if (this.fundamentalData.financialMetrics['PEG Ratio'] !== undefined) {
        const pegRatio = this.fundamentalData.financialMetrics['PEG Ratio'];
        valuationIndicators.push({
          name: 'PEG Ratio',
          value: this.formatNumber(pegRatio),
          status: pegRatio < 1 ? 'positive' : (pegRatio > 2 ? 'negative' : 'neutral'),
          description: 'Price/Earnings to Growth ratio factors in a company\'s expected earnings growth'
        });
      }
      
      if (this.fundamentalData.financialMetrics['EV/EBITDA'] !== undefined) {
        const evToEbitda = this.fundamentalData.financialMetrics['EV/EBITDA'];
        valuationIndicators.push({
          name: 'EV/EBITDA',
          value: this.formatNumber(evToEbitda),
          status: evToEbitda < 8 ? 'positive' : (evToEbitda > 12 ? 'negative' : 'neutral'),
          description: 'Enterprise Value to EBITDA ratio is used to determine a company\'s value'
        });
      }
    }
    
    if (this.fundamentalData.investorInsightMetrics) {
      if (this.fundamentalData.investorInsightMetrics['P/E Ratio'] !== undefined) {
        const peRatio = this.fundamentalData.investorInsightMetrics['P/E Ratio'];
        valuationIndicators.push({
          name: 'P/E Ratio',
          value: this.formatNumber(peRatio),
          status: peRatio < 15 ? 'positive' : (peRatio > 25 ? 'negative' : 'neutral'),
          description: 'Price-to-Earnings ratio measures a company\'s current share price relative to its EPS'
        });
      }
    }
    
    if (valuationIndicators.length > 0) {
      this.fundamentalGroups.push({
        name: 'Valuation Metrics',
        indicators: valuationIndicators
      });
    }
    
    // Growth indicators
    const growthIndicators: FundamentalIndicator[] = [];
    if (this.fundamentalData.growthIndicators) {
      if (this.fundamentalData.growthIndicators['Revenue Growth (YoY)'] !== undefined) {
        const revenueGrowth = this.fundamentalData.growthIndicators['Revenue Growth (YoY)'];
        growthIndicators.push({
          name: 'Revenue Growth (YoY)',
          value: this.formatPercentage(revenueGrowth),
          status: revenueGrowth > 0.05 ? 'positive' : (revenueGrowth < 0 ? 'negative' : 'neutral'),
          description: 'Year-over-year growth in company revenue'
        });
      }
      
      if (this.fundamentalData.growthIndicators['Profit Margins'] !== undefined) {
        const profitMargins = this.fundamentalData.growthIndicators['Profit Margins'];
        growthIndicators.push({
          name: 'Profit Margins',
          value: this.formatPercentage(profitMargins),
          status: profitMargins > 0.1 ? 'positive' : (profitMargins < 0 ? 'negative' : 'neutral'),
          description: 'Net profit as a percentage of revenue'
        });
      }
      
      if (this.fundamentalData.growthIndicators['ROE (Return on Equity)'] !== undefined) {
        const roe = this.fundamentalData.growthIndicators['ROE (Return on Equity)'];
        growthIndicators.push({
          name: 'ROE',
          value: this.formatPercentage(roe),
          status: roe > 0.15 ? 'positive' : (roe < 0.05 ? 'negative' : 'neutral'),
          description: 'Return on Equity measures a company\'s profitability relative to its equity'
        });
      }
      
      if (this.fundamentalData.growthIndicators['ROA (Return on Assets)'] !== undefined) {
        const roa = this.fundamentalData.growthIndicators['ROA (Return on Assets)'];
        growthIndicators.push({
          name: 'ROA',
          value: this.formatPercentage(roa),
          status: roa > 0.05 ? 'positive' : (roa < 0.02 ? 'negative' : 'neutral'),
          description: 'Return on Assets measures a company\'s profitability relative to its total assets'
        });
      }
    }
    
    if (this.fundamentalData.investorInsightMetrics) {
      if (this.fundamentalData.investorInsightMetrics['Earnings Growth(YoY)'] !== undefined) {
        const earningsGrowth = this.fundamentalData.investorInsightMetrics['Earnings Growth(YoY)'];
        if (earningsGrowth !== 'N/A') {
          growthIndicators.push({
            name: 'Earnings Growth (YoY)',
            value: this.formatPercentage(earningsGrowth),
            status: earningsGrowth > 0.1 ? 'positive' : (earningsGrowth < 0 ? 'negative' : 'neutral'),
            description: 'Year-over-year growth in earnings per share'
          });
        }
      }
    }
    
    if (growthIndicators.length > 0) {
      this.fundamentalGroups.push({
        name: 'Growth Indicators',
        indicators: growthIndicators
      });
    }
    
    // Profitability indicators
    const profitabilityIndicators: FundamentalIndicator[] = [];
    if (this.fundamentalData.profitabilityIndicators) {
      if (this.fundamentalData.profitabilityIndicators['Gross Margin'] !== undefined) {
        const grossMargin = this.fundamentalData.profitabilityIndicators['Gross Margin'];
        profitabilityIndicators.push({
          name: 'Gross Margin',
          value: this.formatPercentage(grossMargin),
          status: grossMargin > 0.4 ? 'positive' : (grossMargin < 0.2 ? 'negative' : 'neutral'),
          description: 'Gross profit as a percentage of revenue'
        });
      }
      
      if (this.fundamentalData.profitabilityIndicators['Operating Margin'] !== undefined) {
        const operatingMargin = this.fundamentalData.profitabilityIndicators['Operating Margin'];
        profitabilityIndicators.push({
          name: 'Operating Margin',
          value: this.formatPercentage(operatingMargin),
          status: operatingMargin > 0.15 ? 'positive' : (operatingMargin < 0.05 ? 'negative' : 'neutral'),
          description: 'Operating profit as a percentage of revenue'
        });
      }
      
      if (this.fundamentalData.profitabilityIndicators['Net Margin'] !== undefined) {
        const netMargin = this.fundamentalData.profitabilityIndicators['Net Margin'];
        profitabilityIndicators.push({
          name: 'Net Margin',
          value: this.formatPercentage(netMargin),
          status: netMargin > 0.1 ? 'positive' : (netMargin < 0.03 ? 'negative' : 'neutral'),
          description: 'Net profit as a percentage of revenue'
        });
      }
    }
    
    if (this.fundamentalData.investorInsightMetrics) {
      if (this.fundamentalData.investorInsightMetrics['EPS'] !== undefined) {
        const eps = this.fundamentalData.investorInsightMetrics['EPS'];
        profitabilityIndicators.push({
          name: 'EPS (TTM)',
          value: this.formatCurrency(eps),
          status: eps > 0 ? 'positive' : (eps < 0 ? 'negative' : 'neutral'),
          description: 'Earnings Per Share (Trailing Twelve Months)'
        });
      }
    }
    
    if (profitabilityIndicators.length > this.fundamentalData.incomeStatement ) {
      this.fundamentalGroups.push({
        name: 'Profitability',
        indicators: profitabilityIndicators
      });
    }
    
    // Financial health indicators
    const financialHealthIndicators: FundamentalIndicator[] = [];
    if (this.fundamentalData.balanceSheetInformation) {
      if (this.fundamentalData.balanceSheetInformation['Total Assets'] !== undefined && 
          this.fundamentalData.balanceSheetInformation['Total Liabilities'] !== undefined) {
        const assets = this.fundamentalData.balanceSheetInformation['Total Assets'];
        const liabilities = this.fundamentalData.balanceSheetInformation['Total Liabilities'];
        const assetToDebtRatio = assets / liabilities;
        
        financialHealthIndicators.push({
          name: 'Asset to Debt Ratio',
          value: this.formatNumber(assetToDebtRatio),
          status: assetToDebtRatio > 2 ? 'positive' : (assetToDebtRatio < 1.2 ? 'negative' : 'neutral'),
          description: 'Ratio of total assets to total liabilities'
        });
      }
      
      if (this.fundamentalData.balanceSheetInformation['Current Assets'] !== undefined && 
          this.fundamentalData.balanceSheetInformation['Current Liabilities'] !== undefined) {
        const currentAssets = this.fundamentalData.balanceSheetInformation['Current Assets'];
        const currentLiabilities = this.fundamentalData.balanceSheetInformation['Current Liabilities'];
        const currentRatio = currentAssets / currentLiabilities;
        
        financialHealthIndicators.push({
          name: 'Current Ratio',
          value: this.formatNumber(currentRatio),
          status: currentRatio > 1.5 ? 'positive' : (currentRatio < 1 ? 'negative' : 'neutral'),
          description: 'Ratio of current assets to current liabilities'
        });
      }
    }
    
    if (this.fundamentalData.riskIndicators) {
      if (this.fundamentalData.riskIndicators['Debt-to-Equity Ratio(Risk)'] !== undefined) {
        const debtToEquity = this.fundamentalData.riskIndicators['Debt-to-Equity Ratio(Risk)'];
        financialHealthIndicators.push({
          name: 'Debt-to-Equity Ratio',
          value: this.formatNumber(debtToEquity),
          status: debtToEquity < 1 ? 'positive' : (debtToEquity > 2 ? 'negative' : 'neutral'),
          description: 'Ratio of total debt to shareholders\' equity'
        });
      }
      
      if (this.fundamentalData.riskIndicators['Quick Ratio'] !== undefined) {
        const quickRatio = this.fundamentalData.riskIndicators['Quick Ratio'];
        financialHealthIndicators.push({
          name: 'Quick Ratio',
          value: this.formatNumber(quickRatio),
          status: quickRatio > 1 ? 'positive' : (quickRatio < 0.7 ? 'negative' : 'neutral'),
          description: 'Measure of a company\'s ability to pay short-term obligations'
        });
      }
      
      if (this.fundamentalData.riskIndicators['Interest Coverage Ratio'] !== undefined) {
        const interestCoverage = this.fundamentalData.riskIndicators['Interest Coverage Ratio'];
        financialHealthIndicators.push({
          name: 'Interest Coverage',
          value: this.formatNumber(interestCoverage),
          status: interestCoverage > 3 ? 'positive' : (interestCoverage < 1.5 ? 'negative' : 'neutral'),
          description: 'Ability of a company to pay interest on its outstanding debt'
        });
      }
    }
    
    if (financialHealthIndicators.length > 0) {
      this.fundamentalGroups.push({
        name: 'Financial Health',
        indicators: financialHealthIndicators
      });
    }
    
    // Dividend information
    const dividendIndicators: FundamentalIndicator[] = [];
    if (this.fundamentalData.dividends) {
      if (this.fundamentalData.dividends['Payout Ratio'] !== undefined) {
        const payoutRatio = this.fundamentalData.dividends['Payout Ratio'];
        dividendIndicators.push({
          name: 'Payout Ratio',
          value: this.formatPercentage(payoutRatio),
          status: payoutRatio > 0 && payoutRatio < 0.75 ? 'positive' : (payoutRatio > 1 ? 'negative' : 'neutral'),
          description: 'Percentage of earnings paid as dividends'
        });
      }
      
      if (this.fundamentalData.dividends['Dividend Growth Rate'] !== undefined) {
        const dividendGrowth = this.fundamentalData.dividends['Dividend Growth Rate'];
        dividendIndicators.push({
          name: 'Dividend Growth Rate',
          value: this.formatPercentage(dividendGrowth),
          status: dividendGrowth > 0.05 ? 'positive' : (dividendGrowth < 0 ? 'negative' : 'neutral'),
          description: 'Annual growth rate of dividend payments'
        });
      }
    }
    
    if (dividendIndicators.length > 0) {
      this.fundamentalGroups.push({
        name: 'Dividend Information',
        indicators: dividendIndicators
      });
    }
  }

  private formatCurrency(value: number | undefined | null): string {
    if (value === undefined || value === null) {
      return 'N/A';
    }
    
    if (Math.abs(value) >= 1e12) {
      return `$${(value / 1e12).toFixed(2)}T`;
    } else if (Math.abs(value) >= 1e9) {
      return `$${(value / 1e9).toFixed(2)}B`;
    } else if (Math.abs(value) >= 1e6) {
      return `$${(value / 1e6).toFixed(2)}M`;
    } else if (Math.abs(value) >= 1e3) {
      return `$${(value / 1e3).toFixed(2)}K`;
    } else {
      return `$${value.toFixed(2)}`;
    }
  }

  private formatPercentage(value: number | undefined | null): string {
    if (value === undefined || value === null) {
      return 'N/A';
    }
    
    // Check if value is already in percentage format (e.g., 15.5 instead of 0.155)
    if (Math.abs(value) > 1 && Math.abs(value) < 100) {
      return `${value.toFixed(2)}%`;
    } else {
      return `${(value * 100).toFixed(2)}%`;
    }
  }

  private formatNumber(value: number | undefined | null): string {
    if (value === undefined || value === null) {
      return 'N/A';
    }
    
    return value.toFixed(2);
  }
}
