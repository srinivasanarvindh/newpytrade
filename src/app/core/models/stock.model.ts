export interface Stock {
  symbol: string;
  company: string;
  exchange?: string;
  sector?: string;
  currency?: string;
  price?: number;
  lastPrice?: number;
  change?: number;
  changePercent?: number;
  volume?: number;
  technical?: {
    rsi?: number;
    macd?: number;
    signal?: number;
    histogram?: number;
    ema50?: number;
    ema200?: number;
    sma50?: number;
    sma200?: number;
  };
  fundamental?: {
    market_cap?: number;
    pe_ratio?: number;
    dividend_yield?: number;
    eps?: number;
    revenue_growth?: number;
    debt_to_equity?: number;
  };
  prediction?: {
    predicted_change?: number;
    confidence?: number;
    target_price?: number;
  };
}

export interface StockPrice {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adjClose?: number;
}

export interface StockData {
  symbol: string;
  prices: StockPrice[];
  name?: string;
  exchange?: string;
  currency?: string;
}

export interface PriceData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface RSIData {
  date: string;
  value: number;
}

export interface MACDData {
  date: string;
  macd: number;
  signal: number;
  histogram: number;
}

export interface CompanyDetails {
  symbol: string;
  name: string;
  exchange: string;
  sector: string;
  industry: string;
  description: string;
  website: string;
  logoUrl?: string;
  country: string;
  currency: string;
}

export interface TechnicalIndicators {
  symbol: string;
  rsi: number;
  macd: number;
  signal: number;
  histogram: number;
  ema50: number;
  ema200: number;
  sma50: number;
  sma200: number;
  atr: number;
  upperBollingerBand: number;
  lowerBollingerBand: number;
  middleBollingerBand: number;
}

export interface FinancialMetrics {
  marketCap?: number;
  priceToBook?: number;
  priceToSales?: number;
  pegRatio?: number;
  evToEbitda?: number;
}

export interface BalanceSheetInformation {
  totalAssets?: number;
  totalLiabilities?: number;
  totalStockholderEquity?: number;
  longTermDebt?: number;
  currentAssets?: number;
  currentLiabilities?: number;
  inventory?: number;
}

export interface IncomeStatement {
  totalRevenue?: number;
  operatingIncome?: number;
  netIncome?: number;
  grossProfit?: number;
}

export interface GrowthIndicators {
  revenueGrowthYoY?: number;
  profitMargins?: number;
  roe?: number;
  roa?: number;
}

export interface RiskIndicators {
  debtToEquityRatio?: number;
  interestCoverageRatio?: number;
  beta?: number;
  quickRatio?: number;
}

export interface Dividends {
  payoutRatio?: number;
  dividendGrowthRate?: number;
}

export interface CashFlowStatement {
  operatingCashFlow?: number;
  investingCashFlow?: number;
  financingCashFlow?: number;
  cashFlowToDebtRatio?: number;
}

export interface ProfitabilityIndicators {
  grossMargin?: number;
  operatingMargin?: number;
  netMargin?: number;
}

export interface LiquidityIndicators {
  cashRatio?: number;
  workingCapital?: number;
}

export interface InvestorInsightMetrics {
  eps?: number;
  peRatio?: number;
  revenueGrowth?: number;
  debtToEquity?: number;
  earningsGrowthYoY?: number;
  currentRatio?: number;
}

export interface FundamentalData {
  symbol: string;
  faDetailedInfo: {
    financialMetrics: FinancialMetrics;
    companyOverview: {
      companyName?: string;
      sector?: string;
      industry?: string;
    };
    growthIndicators: GrowthIndicators;
    riskIndicators: RiskIndicators;
    dividends: Dividends;
    cashFlowStatement: CashFlowStatement;
    incomeStatement: IncomeStatement;
    balanceSheetInformation: BalanceSheetInformation;
    profitabilityIndicators: ProfitabilityIndicators;
    liquidityIndicators: LiquidityIndicators;
    investorInsightMetrics: InvestorInsightMetrics;
  };
}

export interface PredictionData {
  symbol: string;
  predictions: number[];
  dates: string[];
}

export interface IndexData {
  name: string;
  value: number;
  change: number;
  changePercent: number;
}

export interface TradingSignal {
  type: 'bullish' | 'bearish' | 'neutral';
  strength: number;
  strategy: string;
  indicator: string;
  description: string;
}

export interface MarketNews {
  title: string;
  date: string;
  source: string;
  url: string;
  summary: string;
}
