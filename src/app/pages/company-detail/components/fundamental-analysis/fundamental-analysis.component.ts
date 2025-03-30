import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { FundamentalData } from '../../../../core/models/stock.model';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-fundamental-analysis',
  templateUrl: './fundamental-analysis.component.html',
  styleUrls: ['./fundamental-analysis.component.scss'],
  standalone: true,
  imports: [
    CommonModule
  ]
})
export class FundamentalAnalysisComponent implements OnChanges {
  @Input() fundamentalData: FundamentalData | null = null;
  
  overallRating: {
    score: number;
    interpretation: string;
    description: string;
  } = {
    score: 0,
    interpretation: 'Neutral',
    description: 'Not enough data available for a comprehensive analysis.'
  };
  
  valuationStatus: 'Undervalued' | 'Fairly Valued' | 'Overvalued' | 'Unknown' = 'Unknown';
  growthStatus: 'Strong' | 'Moderate' | 'Weak' | 'Unknown' = 'Unknown';
  financialHealthStatus: 'Strong' | 'Moderate' | 'Weak' | 'Unknown' = 'Unknown';
  profitabilityStatus: 'Strong' | 'Moderate' | 'Weak' | 'Unknown' = 'Unknown';
  
  metricInterpretations: {
    category: string;
    metrics: {
      name: string;
      value: number | null | undefined;
      interpretation: string;
      status: 'positive' | 'negative' | 'neutral' | 'unknown';
    }[];
  }[] = [];

  constructor() { }

  ngOnChanges(changes: SimpleChanges): void {
    // Debug log to track data received
    console.log('Fundamental Analysis received data:', {
      fundamentalData: this.fundamentalData
    });
    
    // Always try to analyze data regardless of whether it has changed
    // This ensures the component always displays something meaningful
    this.analyzeFundamentalData();
    
    // Make sure we have at least some default metrics data if none available
    if (this.metricInterpretations.length === 0) {
      this.metricInterpretations = [{
        category: 'Company Status',
        metrics: [{
          name: 'Data Availability',
          value: null,
          interpretation: 'Fundamental data is currently unavailable. This could be due to data source limitations or the company being newly listed.',
          status: 'unknown'
        }]
      }];
    }
  }

  analyzeFundamentalData(): void {
    if (!this.fundamentalData || !this.fundamentalData.faDetailedInfo) {
      this.setDefaultValues();
      return;
    }
    
    const faData = this.fundamentalData.faDetailedInfo;
    this.metricInterpretations = [];
    
    // Analyze Valuation Metrics
    const valuationMetrics = [
      {
        name: 'P/E Ratio',
        value: faData.investorInsightMetrics.peRatio,
        interpretation: this.interpretPERatio(faData.investorInsightMetrics.peRatio),
        status: this.getMetricStatus(faData.investorInsightMetrics.peRatio, 25, 10, true)
      },
      {
        name: 'Price-to-Book Ratio',
        value: faData.financialMetrics.priceToBook,
        interpretation: this.interpretPBRatio(faData.financialMetrics.priceToBook),
        status: this.getMetricStatus(faData.financialMetrics.priceToBook, 3, 1, true)
      },
      {
        name: 'Price-to-Sales Ratio',
        value: faData.financialMetrics.priceToSales,
        interpretation: this.interpretPSRatio(faData.financialMetrics.priceToSales),
        status: this.getMetricStatus(faData.financialMetrics.priceToSales, 5, 1, true)
      },
      {
        name: 'PEG Ratio',
        value: faData.financialMetrics.pegRatio,
        interpretation: this.interpretPEGRatio(faData.financialMetrics.pegRatio),
        status: this.getMetricStatus(faData.financialMetrics.pegRatio, 1.5, 1, true)
      },
      {
        name: 'EV/EBITDA',
        value: faData.financialMetrics.evToEbitda,
        interpretation: this.interpretEVEBITDA(faData.financialMetrics.evToEbitda),
        status: this.getMetricStatus(faData.financialMetrics.evToEbitda, 15, 8, true)
      }
    ];
    
    this.metricInterpretations.push({
      category: 'Valuation Metrics',
      metrics: valuationMetrics as any
    });
    
    // Analyze Growth Metrics
    const growthMetrics = [
      {
        name: 'Revenue Growth',
        value: faData.investorInsightMetrics.revenueGrowth,
        interpretation: this.interpretRevenueGrowth(faData.investorInsightMetrics.revenueGrowth),
        status: this.getMetricStatus(faData.investorInsightMetrics.revenueGrowth, 0.05, 0.15, false)
      },
      {
        name: 'Earnings Growth (YoY)',
        value: faData.investorInsightMetrics.earningsGrowthYoY,
        interpretation: this.interpretEarningsGrowth(faData.investorInsightMetrics.earningsGrowthYoY),
        status: this.getMetricStatus(faData.investorInsightMetrics.earningsGrowthYoY, 0.05, 0.2, false)
      },
      {
        name: 'ROE',
        value: faData.growthIndicators.roe,
        interpretation: this.interpretROE(faData.growthIndicators.roe),
        status: this.getMetricStatus(faData.growthIndicators.roe, 0.1, 0.2, false)
      },
      {
        name: 'ROA',
        value: faData.growthIndicators.roa,
        interpretation: this.interpretROA(faData.growthIndicators.roa),
        status: this.getMetricStatus(faData.growthIndicators.roa, 0.05, 0.1, false)
      }
    ];
    
    this.metricInterpretations.push({
      category: 'Growth Metrics',
      metrics: growthMetrics as any
    });
    
    // Analyze Financial Health Metrics
    const financialHealthMetrics = [
      {
        name: 'Debt-to-Equity Ratio',
        value: faData.investorInsightMetrics.debtToEquity,
        interpretation: this.interpretDebtToEquity(faData.investorInsightMetrics.debtToEquity),
        status: this.getMetricStatus(faData.investorInsightMetrics.debtToEquity, 2, 0.5, true)
      },
      {
        name: 'Current Ratio',
        value: faData.investorInsightMetrics.currentRatio,
        interpretation: this.interpretCurrentRatio(faData.investorInsightMetrics.currentRatio),
        status: this.getMetricStatus(faData.investorInsightMetrics.currentRatio, 1, 2, false)
      },
      {
        name: 'Quick Ratio',
        value: faData.riskIndicators.quickRatio,
        interpretation: this.interpretQuickRatio(faData.riskIndicators.quickRatio),
        status: this.getMetricStatus(faData.riskIndicators.quickRatio, 1, 1.5, false)
      },
      {
        name: 'Interest Coverage',
        value: faData.riskIndicators.interestCoverageRatio,
        interpretation: this.interpretInterestCoverage(faData.riskIndicators.interestCoverageRatio),
        status: this.getMetricStatus(faData.riskIndicators.interestCoverageRatio, 2, 4, false)
      }
    ];
    
    this.metricInterpretations.push({
      category: 'Financial Health',
      metrics: financialHealthMetrics as any
    });
    
    // Analyze Profitability Metrics
    const profitabilityMetrics = [
      {
        name: 'Gross Margin',
        value: faData.profitabilityIndicators.grossMargin,
        interpretation: this.interpretGrossMargin(faData.profitabilityIndicators.grossMargin),
        status: this.getMetricStatus(faData.profitabilityIndicators.grossMargin, 0.2, 0.4, false)
      },
      {
        name: 'Operating Margin',
        value: faData.profitabilityIndicators.operatingMargin,
        interpretation: this.interpretOperatingMargin(faData.profitabilityIndicators.operatingMargin),
        status: this.getMetricStatus(faData.profitabilityIndicators.operatingMargin, 0.1, 0.2, false)
      },
      {
        name: 'Net Margin',
        value: faData.profitabilityIndicators.netMargin,
        interpretation: this.interpretNetMargin(faData.profitabilityIndicators.netMargin),
        status: this.getMetricStatus(faData.profitabilityIndicators.netMargin, 0.05, 0.1, false)
      },
      {
        name: 'EPS',
        value: faData.investorInsightMetrics.eps,
        interpretation: this.interpretEPS(faData.investorInsightMetrics.eps),
        status: this.getMetricStatus(faData.investorInsightMetrics.eps, 0, 5, false)
      }
    ];
    
    this.metricInterpretations.push({
      category: 'Profitability',
      metrics: profitabilityMetrics as any
    });
    
    // Calculate overall ratings
    this.calculateOverallRatings();
  }

  setDefaultValues(): void {
    this.overallRating = {
      score: 0,
      interpretation: 'Neutral',
      description: 'Not enough data available for a comprehensive analysis.'
    };
    
    this.valuationStatus = 'Unknown';
    this.growthStatus = 'Unknown';
    this.financialHealthStatus = 'Unknown';
    this.profitabilityStatus = 'Unknown';
    
    this.metricInterpretations = [];
  }

  getMetricStatus(value: number | null | undefined, moderateThreshold: number, goodThreshold: number, isLowerBetter: boolean): 'positive' | 'negative' | 'neutral' | 'unknown' {
    if (value === null || value === undefined) {
      return 'unknown';
    }
    
    if (isLowerBetter) {
      if (value <= goodThreshold) return 'positive';
      if (value <= moderateThreshold) return 'neutral';
      return 'negative';
    } else {
      if (value >= goodThreshold) return 'positive';
      if (value >= moderateThreshold) return 'neutral';
      return 'negative';
    }
  }

  // Interpretation methods for each metric
  interpretPERatio(peRatio: number | null | undefined): string {
    if (peRatio === null || peRatio === undefined) return 'No data available.';
    
    if (peRatio < 0) return 'Negative P/E indicates the company is operating at a loss.';
    if (peRatio < 10) return 'Low P/E may indicate an undervalued stock or market concerns about future growth.';
    if (peRatio < 20) return 'Moderate P/E within typical market range.';
    if (peRatio < 30) return 'Higher P/E suggests market expects strong future growth.';
    return 'Very high P/E usually indicates market expects exceptional growth or profitability improvements.';
  }

  interpretPBRatio(pbRatio: number | null | undefined): string {
    if (pbRatio === null || pbRatio === undefined) return 'No data available.';
    
    if (pbRatio < 1) return 'Trading below book value, may indicate undervaluation or underlying problems.';
    if (pbRatio < 3) return 'Moderate P/B ratio, typically reasonable for established companies.';
    return 'Higher P/B ratio may indicate strong expected returns or overvaluation.';
  }

  interpretPSRatio(psRatio: number | null | undefined): string {
    if (psRatio === null || psRatio === undefined) return 'No data available.';
    
    if (psRatio < 1) return 'Low P/S ratio may indicate undervaluation relative to sales.';
    if (psRatio < 3) return 'Moderate P/S ratio, generally reasonable valuation.';
    if (psRatio < 5) return 'Higher P/S ratio, typical for companies with strong growth or high margins.';
    return 'Very high P/S ratio, suggests high growth expectations or potential overvaluation.';
  }

  interpretPEGRatio(pegRatio: number | null | undefined): string {
    if (pegRatio === null || pegRatio === undefined) return 'No data available.';
    
    if (pegRatio < 0) return 'Negative PEG suggests recent or expected earnings decline.';
    if (pegRatio < 1) return 'PEG < 1 often indicates an undervalued stock relative to growth rate.';
    if (pegRatio < 1.5) return 'Moderate PEG ratio, generally considered reasonably valued.';
    return 'Higher PEG ratio may indicate overvaluation relative to growth prospects.';
  }

  interpretEVEBITDA(evEbitda: number | null | undefined): string {
    if (evEbitda === null || evEbitda === undefined) return 'No data available.';
    
    if (evEbitda < 8) return 'Low EV/EBITDA suggests potential undervaluation.';
    if (evEbitda < 15) return 'Moderate EV/EBITDA, generally considered reasonably valued.';
    return 'Higher EV/EBITDA may indicate overvaluation or high growth expectations.';
  }

  interpretRevenueGrowth(growth: number | null | undefined): string {
    if (growth === null || growth === undefined) return 'No data available.';
    
    if (growth < 0) return 'Negative revenue growth indicates business contraction.';
    if (growth < 0.05) return 'Low revenue growth below inflation, may be concerning.';
    if (growth < 0.15) return 'Moderate revenue growth, generally positive.';
    return 'Strong revenue growth, indicates expanding business.';
  }

  interpretEarningsGrowth(growth: number | null | undefined): string {
    if (growth === null || growth === undefined) return 'No data available.';
    
    if (growth < 0) return 'Negative earnings growth indicates profitability challenges.';
    if (growth < 0.05) return 'Low earnings growth, may signal competitive or operational issues.';
    if (growth < 0.20) return 'Moderate earnings growth, generally positive.';
    return 'Strong earnings growth, indicates improving profitability.';
  }

  interpretROE(roe: number | null | undefined): string {
    if (roe === null || roe === undefined) return 'No data available.';
    
    if (roe < 0) return 'Negative ROE indicates the company is not generating returns on equity.';
    if (roe < 0.1) return 'Low ROE, below average efficiency in generating profits from equity.';
    if (roe < 0.2) return 'Moderate ROE, reasonably efficient use of equity.';
    return 'High ROE, indicates efficient use of equity to generate profits.';
  }

  interpretROA(roa: number | null | undefined): string {
    if (roa === null || roa === undefined) return 'No data available.';
    
    if (roa < 0) return 'Negative ROA indicates the company is not generating returns on assets.';
    if (roa < 0.05) return 'Low ROA, below average efficiency in using assets.';
    if (roa < 0.1) return 'Moderate ROA, reasonably efficient use of assets.';
    return 'High ROA, indicates efficient use of assets to generate profits.';
  }

  interpretDebtToEquity(ratio: number | null | undefined): string {
    if (ratio === null || ratio === undefined) return 'No data available.';
    
    if (ratio < 0.5) return 'Low debt levels relative to equity, conservative financial structure.';
    if (ratio < 1.5) return 'Moderate leverage, generally manageable debt levels.';
    if (ratio < 2) return 'Higher leverage, may present some financial risk.';
    return 'High debt relative to equity, potentially concerning financial risk.';
  }

  interpretCurrentRatio(ratio: number | null | undefined): string {
    if (ratio === null || ratio === undefined) return 'No data available.';
    
    if (ratio < 1) return 'Current ratio below 1 indicates potential liquidity concerns.';
    if (ratio < 2) return 'Moderate current ratio, generally sufficient short-term liquidity.';
    return 'Strong current ratio, indicates robust short-term financial health.';
  }

  interpretQuickRatio(ratio: number | null | undefined): string {
    if (ratio === null || ratio === undefined) return 'No data available.';
    
    if (ratio < 1) return 'Quick ratio below 1 may indicate potential short-term liquidity issues.';
    if (ratio < 1.5) return 'Moderate quick ratio, generally adequate liquidity.';
    return 'Strong quick ratio, indicates robust liquidity position.';
  }

  interpretInterestCoverage(ratio: number | null | undefined): string {
    if (ratio === null || ratio === undefined) return 'No data available.';
    
    if (ratio < 1.5) return 'Low interest coverage, indicates potential debt servicing issues.';
    if (ratio < 3) return 'Moderate interest coverage, generally adequate for debt servicing.';
    if (ratio < 5) return 'Good interest coverage, comfortable ability to service debt.';
    return 'Strong interest coverage, very comfortable buffer for debt servicing.';
  }

  interpretGrossMargin(margin: number | null | undefined): string {
    if (margin === null || margin === undefined) return 'No data available.';
    
    if (margin < 0.2) return 'Low gross margin, may indicate weak pricing power or high production costs.';
    if (margin < 0.4) return 'Moderate gross margin, generally healthy.';
    return 'Strong gross margin, indicates good pricing power or cost efficiency.';
  }

  interpretOperatingMargin(margin: number | null | undefined): string {
    if (margin === null || margin === undefined) return 'No data available.';
    
    if (margin < 0.05) return 'Low operating margin, may indicate operational inefficiencies.';
    if (margin < 0.15) return 'Moderate operating margin, reasonably efficient operations.';
    return 'Strong operating margin, indicates efficient operations.';
  }

  interpretNetMargin(margin: number | null | undefined): string {
    if (margin === null || margin === undefined) return 'No data available.';
    
    if (margin < 0.03) return 'Low net margin, limited profitability after all expenses.';
    if (margin < 0.08) return 'Moderate net margin, reasonably profitable.';
    return 'Strong net margin, indicates highly profitable business.';
  }

  interpretEPS(eps: number | null | undefined): string {
    if (eps === null || eps === undefined) return 'No data available.';
    
    if (eps < 0) return 'Negative EPS indicates the company is currently unprofitable.';
    if (eps < 1) return 'Low EPS, minimal profit per share.';
    if (eps < 5) return 'Moderate EPS, reasonable profit per share.';
    return 'Strong EPS, indicates significant profit per share.';
  }

  calculateOverallRatings(): void {
    // Count positive, neutral, and negative metrics by category
    const categories = ['Valuation Metrics', 'Growth Metrics', 'Financial Health', 'Profitability'];
    const categoryCounts: {[key: string]: {positive: number, neutral: number, negative: number, total: number}} = {};
    
    for (const category of categories) {
      categoryCounts[category] = {positive: 0, neutral: 0, negative: 0, total: 0};
    }
    
    for (const category of this.metricInterpretations) {
      if (!categoryCounts[category.category]) continue;
      
      for (const metric of category.metrics) {
        if (metric.status === 'positive') categoryCounts[category.category].positive++;
        else if (metric.status === 'neutral') categoryCounts[category.category].neutral++;
        else if (metric.status === 'negative') categoryCounts[category.category].negative++;
        
        if (metric.status !== 'unknown') categoryCounts[category.category].total++;
      }
    }
    
    // Set category statuses
    if (categoryCounts['Valuation Metrics'].total > 0) {
      const positiveRatio = categoryCounts['Valuation Metrics'].positive / categoryCounts['Valuation Metrics'].total;
      const negativeRatio = categoryCounts['Valuation Metrics'].negative / categoryCounts['Valuation Metrics'].total;
      
      if (positiveRatio > 0.5) this.valuationStatus = 'Undervalued';
      else if (negativeRatio > 0.5) this.valuationStatus = 'Overvalued';
      else this.valuationStatus = 'Fairly Valued';
    }
    
    if (categoryCounts['Growth Metrics'].total > 0) {
      const positiveRatio = categoryCounts['Growth Metrics'].positive / categoryCounts['Growth Metrics'].total;
      const negativeRatio = categoryCounts['Growth Metrics'].negative / categoryCounts['Growth Metrics'].total;
      
      if (positiveRatio > 0.5) this.growthStatus = 'Strong';
      else if (negativeRatio > 0.5) this.growthStatus = 'Weak';
      else this.growthStatus = 'Moderate';
    }
    
    if (categoryCounts['Financial Health'].total > 0) {
      const positiveRatio = categoryCounts['Financial Health'].positive / categoryCounts['Financial Health'].total;
      const negativeRatio = categoryCounts['Financial Health'].negative / categoryCounts['Financial Health'].total;
      
      if (positiveRatio > 0.5) this.financialHealthStatus = 'Strong';
      else if (negativeRatio > 0.5) this.financialHealthStatus = 'Weak';
      else this.financialHealthStatus = 'Moderate';
    }
    
    if (categoryCounts['Profitability'].total > 0) {
      const positiveRatio = categoryCounts['Profitability'].positive / categoryCounts['Profitability'].total;
      const negativeRatio = categoryCounts['Profitability'].negative / categoryCounts['Profitability'].total;
      
      if (positiveRatio > 0.5) this.profitabilityStatus = 'Strong';
      else if (negativeRatio > 0.5) this.profitabilityStatus = 'Weak';
      else this.profitabilityStatus = 'Moderate';
    }
    
    // Calculate overall score
    let totalPositive = 0;
    let totalNegative = 0;
    let totalMetrics = 0;
    
    for (const category of categories) {
      totalPositive += categoryCounts[category].positive;
      totalNegative += categoryCounts[category].negative;
      totalMetrics += categoryCounts[category].total;
    }
    
    if (totalMetrics > 0) {
      const score = Math.round(((totalPositive * 1) + (totalNegative * -1)) / totalMetrics * 50 + 50);
      
      this.overallRating.score = score;
      
      if (score >= 70) {
        this.overallRating.interpretation = 'Strong Buy';
        this.overallRating.description = 'Fundamentally strong company with attractive valuation, good growth, and solid financial health.';
      } else if (score >= 60) {
        this.overallRating.interpretation = 'Buy';
        this.overallRating.description = 'Good fundamentals with more positive than negative indicators, suggesting potential upside.';
      } else if (score >= 40) {
        this.overallRating.interpretation = 'Neutral';
        this.overallRating.description = 'Mixed fundamentals with both strengths and weaknesses, suggesting a hold position.';
      } else if (score >= 30) {
        this.overallRating.interpretation = 'Sell';
        this.overallRating.description = 'Weak fundamentals with more negative than positive indicators, suggesting potential downside.';
      } else {
        this.overallRating.interpretation = 'Strong Sell';
        this.overallRating.description = 'Fundamentally weak company with concerning financial metrics and poor growth prospects.';
      }
    }
  }
}
