import { Component, OnInit, HostListener } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { MainService } from '../../core/services/main.service';

@Component({
  selector: 'app-toolspage',
  templateUrl: './toolspage.component.html',
  styleUrls: ['./toolspage.component.css'],
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDialogModule
  ]
})
export class ToolspageComponent implements OnInit {
  isDropdownOpen = false;
  options = ['Short-Term', 'Medium-Term', 'Long-Term'];
  selectedOption: string = '';

  searchText: string = '';
  items = ['Apple', 'Banana', 'Cherry', 'Grapes', 'Orange', 'Pineapple'];

  isLoading: boolean = false;
  isError: boolean = false;
  errorMessage: string = '';
  isTradeButtonEnabled: boolean = false;
  isTradeTypesVisible: boolean = false;
  isTradeButtonsEnabled: boolean = false;

  selectedCountry: string = '';
  selectedMarket: string = '';
  selectedMarketDivision: string = '';
  selectedCompanies: string[] = [];
  selectAll: boolean = false;
  allSelected = false;
  
  // Pagination variables
  companiesPerPage: number = 50; // Show 50 companies per page
  currentCompanyPage: number = 1;
  totalCompanyPages: number = 1;

  countryList = ["United States", "India", "Sweden", "Canada", "United Kingdom", "Germany", "Japan", "China", "Hong Kong", "Saudi Arabia", "Australia", "Singapore", "Sri Lanka"];

  marketList: { [key: string]: string[] } = {
    "United States": ["Dow Jones & Company indices", "Standard & Poor's indices", "Nasdaq indices", "Russell Indexes", "Value Line indices","Wilshire indices"],
    "India": ["NSE (National Stock Exchange of India)", "BSE (Bombay Stock Exchange)"],
    "Canada": ["TSX Venture Exchange", "TSX Composite Index"]
  };

  marketDivision: { [key: string]: string[] } = {
    "NSE (National Stock Exchange of India)": ["NIFTY 50", "NIFTY 100", "NIFTY 500", "NIFTY Midcap 150"],
    "BSE (Bombay Stock Exchange)": ["BSE 30", "BSE 100  BSE", "BSE 500  BSE", "BSE Midcap","BSE Smallcap"],
    "Standard & Poor's indices": ["S&P 100", "S&P 500", "S&P MidCap 400", "S&P SmallCap 600","S&P 1500"],
    "Dow Jones & Company indices": ["Dow Jones Industrial Average", "Dow Jones Transportation Average","Dow Jones Utility Average"],
    "Nasdaq indices": ["Nasdaq Composite(NA)", "Nasdaq-100","Nasdaq Financial-100(NA)"],
    "Russell Indexes": ["Russell 3000(NA)", "Russell 1000", "Russell Top 200(NA)", "Russell MidCap(NA)", "Russell 2500(NA)","Russell Small Cap Completeness(NA)"]
  };

  companyList: { [key: string]: any[] } = {
    // Indian indices
    "NIFTY 50": [],
    "NIFTY 100": [],
    "NIFTY 500": [],
    "NIFTY BANK": [],
    "NIFTY MIDCAP 50": [],
    "NIFTY SMALLCAP 50": [],
    "NIFTY Midcap 150": [],
    "S&P BSE - 30": [],
    "S&P BSE - 100": [],
    // US indices
    "S&P 100": [],
    "S&P 500": [],
    "S&P MidCap 400": [],
    "S&P SmallCap 600": [],
    "S&P 1500": [],
    "Dow Jones Industrial Average": [],
    "Dow Jones Transportation Average": [],
    "Dow Jones Utility Average": [],
    "NASDAQ-100": [],
    "NASDAQ Composite": [],
    "Russell 1000": [],
    // European indices
    "FTSE 100": [],
    "DAX": [],
    "CAC 40": [],
    // Asian indices
    "Nikkei 225": [],
    "Hang Seng Index": [],
    "Shanghai Composite Index": [],
    "Straits Times Index": [],
    // Australian & NZ
    "S&P/ASX 200": [],
    "NZX 50": [],
    // Middle East
    "Tadawul All Share Index": []
  };

  // Rearranged trade buttons to put AI Trading in the same row with Options & Future
  tradeButtons = [
    { label: 'Intraday', icon: 'fas fa-bolt', routeurl: '/intraday-trading', isShowDropDown: true },
    { label: 'Swing Trading', icon: 'fas fa-chart-line', routeurl: '/swing-trading', isShowDropDown: false },
    { label: 'Scalping', icon: 'fas fa-stopwatch', routeurl: null, isShowDropDown: true },
    { label: 'Positional Trading', icon: 'fas fa-chart-bar', routeurl: null, isShowDropDown: true },
    { label: 'Options & Future', icon: 'fas fa-exchange-alt', routeurl: null, isShowDropDown: true },
    { label: 'AI Trading', icon: 'fas fa-robot', routeurl: null, isShowDropDown: true },
    { label: 'Long Term Investment', icon: 'fas fa-hourglass', routeurl: null, isShowDropDown: true },
    { label: 'Short Term Investment', icon: 'fas fa-hand-holding-usd', routeurl: null, isShowDropDown: true }
  ];
   
  constructor(private router: Router, private mainService: MainService, private dialog: MatDialog) { }
  
  // Public method to navigate to swing trading page
  navigateToSwingTrading(): void {
    console.log('Navigating to Swing Trading page');
    
    // First, set the selected companies in the main service
    if (this.selectedCompanies.length > 0) {
      this.mainService.setData(this.selectedCompanies.map(symbol => ({ symbol })));
      
      // Default to Short-Term if no option is selected
      const timeframe = this.selectedOption || 'Short-Term';
      this.mainService.setSwingTrading(timeframe);
    }
    
    // Navigate to the swing trading page
    this.router.navigateByUrl('/swing-trading');
  }

  ngOnInit() {
    this.loadIndicesData();
  }

  get filteredItems() {
    return this.items.filter(item =>
      item.toLowerCase().includes(this.searchText.toLowerCase())
    );
  }

  toggleDropdown(event?: Event) {
    if (event) {
      event.stopPropagation(); // Prevent event bubbling
    }
    this.isDropdownOpen = !this.isDropdownOpen;
    console.log('Dropdown toggled:', this.isDropdownOpen);
  }

  selectOption(option: string, event?: Event) {
    if (event) {
      event.stopPropagation(); // Prevent event bubbling
    }
    console.log('Option selected:', option);
    this.selectedOption = option; // Update the button label with the selected option
    this.isDropdownOpen = false; // Close the dropdown after selection
    
    // Also set the timeframe in the main service
    this.mainService.setSwingTrading(option);
  }

  navigateTo(route: string) {
    this.router.navigate([route]);
  }

  getMarket(): string[] {
    return this.selectedCountry ? this.marketList[this.selectedCountry] || [] : [];
  }

  getMarketDivision(): string[] {
    return this.selectedMarket ? this.marketDivision[this.selectedMarket] || [] : [];
  }

  // Return all companies for the selected market division
  getAllCompanies(): any[] {
    console.log('*** getAllCompanies called ***');
    if (!this.selectedMarketDivision) {
      console.log('No market division selected, returning empty array');
      return [];
    }
    
    // The selectedMarketDivision is the display name - we need to find the actual index name
    // For debugging
    console.log('Selected Market Division:', this.selectedMarketDivision);
    console.log('Selected Market:', this.selectedMarket);
    console.log('Selected Country:', this.selectedCountry);
    console.log('Available company lists:', Object.keys(this.companyList));
    
    // First, try standardizing the market division name to a known format
    const standardizedName = this.standardizeMarketDivisionName(this.selectedMarketDivision);
    console.log(`Standardized market division name: ${standardizedName}`);
    
    // Check if we have data for the standardized name
    if (standardizedName !== this.selectedMarketDivision && 
        this.companyList[standardizedName] && 
        this.companyList[standardizedName].length > 0) {
      console.log(`Found ${this.companyList[standardizedName].length} companies for standardized match: ${standardizedName}`);
      return this.companyList[standardizedName];
    }
    
    // Next, check if there's a case-insensitive match
    const companyKey = Object.keys(this.companyList).find(key => 
      key.toLowerCase() === this.selectedMarketDivision.toLowerCase());
    
    if (companyKey && this.companyList[companyKey] && this.companyList[companyKey].length > 0) {
      console.log(`Found exact case-insensitive match: ${companyKey} with ${this.companyList[companyKey].length} companies`);
      return this.companyList[companyKey];
    }
    
    // Direct match - try using the selected market division directly
    if (this.companyList[this.selectedMarketDivision] && this.companyList[this.selectedMarketDivision].length > 0) {
      console.log(`Found ${this.companyList[this.selectedMarketDivision].length} companies for exact match: ${this.selectedMarketDivision}`);
      return this.companyList[this.selectedMarketDivision];
    }
    
    // Map of common name variations to standardized index names
    const indexNameMap: {[key: string]: string} = {
      // BSE indices
      'S&P BSE - 30': 'S&P BSE - 30',
      'BSE SENSEX': 'S&P BSE - 30',
      'SENSEX': 'S&P BSE - 30',
      'S&P BSE SENSEX': 'S&P BSE - 30',
      'S&P BSE - 100': 'S&P BSE - 100',
      'BSE 100': 'S&P BSE - 100',
      'S&P BSE - 500': 'S&P BSE - 500',
      'BSE 500': 'S&P BSE - 500',
      'S&P BSE MidCap': 'S&P BSE MidCap',
      
      // NIFTY indices
      'NIFTY 50': 'NIFTY 50',
      'NIFTY50': 'NIFTY 50',
      'NIFTY BANK': 'NIFTY BANK',
      'NIFTY MIDCAP 50': 'NIFTY MIDCAP 50',
      'NIFTY SMALLCAP 50': 'NIFTY SMALLCAP 50',
      
      // US indices
      'S&P 100': 'S&P 100',
      'S&P 500': 'S&P 500',
      'Dow Jones Industrial Average': 'Dow Jones Industrial Average',
      'DJIA': 'Dow Jones Industrial Average',
      'NASDAQ-100': 'NASDAQ-100',
      'NASDAQ 100': 'NASDAQ-100',
      'NASDAQ Composite': 'NASDAQ Composite'
    };
    
    // Check for direct mapping
    if (indexNameMap[this.selectedMarketDivision] && 
        this.companyList[indexNameMap[this.selectedMarketDivision]]) {
      const indexName = indexNameMap[this.selectedMarketDivision];
      console.log(`Found direct map match: ${indexName} for ${this.selectedMarketDivision}`);
      return this.companyList[indexName];
    }
    
    // For some indices, like "S&P BSE - 30", we need to match based on partial name
    // First check if it's a BSE market division
    if (this.selectedMarketDivision.includes('BSE')) {
      console.log('Checking for BSE indices...');
      const bseIndices = Object.keys(this.companyList).filter(key => key.includes('BSE'));
      console.log('Available BSE indices:', bseIndices);
      if (bseIndices.length > 0) {
        console.log(`Found BSE index: ${bseIndices[0]} for ${this.selectedMarketDivision}`);
        return this.companyList[bseIndices[0]] || [];
      }
    }
    
    // Check if it's a NIFTY market division
    if (this.selectedMarketDivision.includes('NIFTY')) {
      console.log('Checking for NIFTY indices...');
      const niftyIndices = Object.keys(this.companyList).filter(key => key.includes('NIFTY'));
      console.log('Available NIFTY indices:', niftyIndices);
      if (niftyIndices.length > 0) {
        // Try to find the most specific match
        let bestMatch = niftyIndices[0];
        let bestMatchScore = 0;
        
        for (const index of niftyIndices) {
          // Calculate similarity score (simple version - count matching words)
          const selectedWords = this.selectedMarketDivision.split(' ');
          const indexWords = index.split(' ');
          let matchingWords = 0;
          
          for (const word of selectedWords) {
            if (indexWords.includes(word)) {
              matchingWords++;
            }
          }
          
          if (matchingWords > bestMatchScore) {
            bestMatchScore = matchingWords;
            bestMatch = index;
          }
        }
        
        console.log(`Found best NIFTY index match: ${bestMatch} for ${this.selectedMarketDivision} (score: ${bestMatchScore})`);
        return this.companyList[bestMatch] || [];
      }
    }
    
    // Try to find a similar index by removing spaces and special characters
    console.log('Trying fuzzy matching...');
    const normalizedSelected = this.selectedMarketDivision.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
    for (const key of Object.keys(this.companyList)) {
      const normalizedKey = key.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
      if (normalizedKey.includes(normalizedSelected) || normalizedSelected.includes(normalizedKey)) {
        console.log(`Found fuzzy match: ${key} for ${this.selectedMarketDivision}`);
        return this.companyList[key];
      }
    }
    
    // If all else fails, log the issue and return an empty array
    console.warn(`No companies found for market division: ${this.selectedMarketDivision}`);
    return [];
  }
  
  // Re-enabled pagination functionality with 10 items per page
  getPaginatedCompanies(): any[] {
    const allCompanies = this.getAllCompanies();
    const itemsPerPage = 10;
    const startIndex = (this.currentCompanyPage - 1) * itemsPerPage;
    
    // Update pagination info whenever this method is called
    if (allCompanies.length > 0) {
      this.updatePaginationInfo(allCompanies.length);
    }
    
    return allCompanies.slice(startIndex, startIndex + itemsPerPage);
  }
  
  // For backward compatibility
  getCompanies(): any[] {
    return this.getAllCompanies();
  }
  
  // Re-enabled pagination info calculation
  updatePaginationInfo(totalItems: number): void {
    const itemsPerPage = 10;
    this.totalCompanyPages = Math.ceil(totalItems / itemsPerPage);
    
    // Make sure current page is valid
    if (this.currentCompanyPage > this.totalCompanyPages) {
      this.currentCompanyPage = 1;
    }
  }
  
  // Re-enabled previous page functionality
  prevCompanyPage(event: Event): void {
    event.stopPropagation();
    if (this.currentCompanyPage > 1) {
      this.currentCompanyPage--;
    }
  }
  
  // Re-enabled next page functionality
  nextCompanyPage(event: Event): void {
    event.stopPropagation();
    if (this.currentCompanyPage < this.totalCompanyPages) {
      this.currentCompanyPage++;
    }
  }
 
  // Toggle selection of all companies across all pages
  toggleSelectAll() {
    // Get all companies for the selected market division
    const allCompanies = this.getAllCompanies();
    const allTickers = allCompanies.map(company => company.symbol);
    
    // Get companies for the current page (for UI state only)
    const paginatedCompanies = this.getPaginatedCompanies();
    const paginatedTickers = paginatedCompanies.map(company => company.symbol);
    
    if (this.allSelected) {
      // Deselect all companies
      this.selectedCompanies = [];
      console.log('Deselected all companies');
    } else {
      // Select all companies from all pages
      this.selectedCompanies = [...allTickers];
      console.log(`Selected all ${this.selectedCompanies.length} companies from all pages`);
    }
    
    this.allSelected = !this.allSelected;
  }
  
  // Helper method to standardize market division names
  private standardizeMarketDivisionName(name: string): string {
    // Convert common variations of the same index to a standard form
    const nameLower = name.toLowerCase();
    
    // NIFTY indices
    if (nameLower.includes('nifty') && nameLower.includes('50') && !nameLower.includes('next') && 
        !nameLower.includes('midcap') && !nameLower.includes('smallcap')) {
      return 'NIFTY 50';
    }
    if (nameLower.includes('nifty') && nameLower.includes('next') && nameLower.includes('50')) {
      return 'NIFTY NEXT 50';
    }
    if (nameLower.includes('nifty') && nameLower.includes('midcap') && nameLower.includes('50')) {
      return 'NIFTY MIDCAP 50';
    }
    if (nameLower.includes('nifty') && nameLower.includes('smallcap') && nameLower.includes('50')) {
      return 'NIFTY SMALLCAP 50';
    }
    if (nameLower.includes('nifty') && nameLower.includes('bank')) {
      return 'NIFTY BANK';
    }
    
    // BSE indices
    if ((nameLower.includes('bse') || nameLower.includes('sensex')) && nameLower.includes('30')) {
      return 'S&P BSE - 30';
    }
    if (nameLower.includes('bse') && nameLower.includes('100')) {
      return 'S&P BSE - 100';
    }
    if (nameLower.includes('bse') && nameLower.includes('500')) {
      return 'S&P BSE - 500';
    }
    if (nameLower.includes('bse') && nameLower.includes('midcap')) {
      return 'S&P BSE MidCap';
    }
    
    // US indices
    if (nameLower.includes('s&p') && nameLower.includes('500')) {
      return 'S&P 500';
    }
    if (nameLower.includes('s&p') && nameLower.includes('100')) {
      return 'S&P 100';
    }
    if (nameLower.includes('dow') && nameLower.includes('jones')) {
      return 'Dow Jones Industrial Average';
    }
    if (nameLower.includes('nasdaq') && nameLower.includes('100')) {
      return 'NASDAQ-100';
    }
    if (nameLower.includes('nasdaq') && nameLower.includes('composite')) {
      return 'NASDAQ Composite';
    }
    
    // Return the original name if no standardization was applied
    return name;
  }

  // Check if all companies in the current page are selected
  toggleSelection() {
    // Get only companies for the current page
    const paginatedTickers = this.getPaginatedCompanies().map(company => company.symbol);
    
    // Check if all companies in the current pagination are selected
    this.allSelected = 
      paginatedTickers.length > 0 && 
      paginatedTickers.every(symbol => this.selectedCompanies.includes(symbol));
  }

  toggleCompanySelection(symbol: string) {
    const index = this.selectedCompanies.indexOf(symbol);
    if (index === -1) {
      this.selectedCompanies.push(symbol);
    } else {
      this.selectedCompanies.splice(index, 1);
    }
    this.toggleSelection();
  }
  
  // Debug method to check available companies 
  logAvailableCompanies() {
    console.log('Available companies in market division:', this.selectedMarketDivision);
    
    // Use the same logic as getAllCompanies but with more detailed logging
    const companies = this.getAllCompanies();
    
    console.log(`Found ${companies.length} companies for ${this.selectedMarketDivision}`);
    
    // Log the first 5 companies for verification
    if (companies.length > 0) {
      console.log('Sample companies:', companies.slice(0, 5).map(c => ({
        symbol: c.symbol,
        company: c.company
      })));
    }
    
    // Log all available indices for debugging
    console.log('All available indices:', Object.keys(this.companyList).map(key => ({
      name: key,
      count: (this.companyList[key] || []).length
    })));
  }

  /**
   * Helper method to get the original index of a trading strategy button
   * when using sliced arrays in the template
   * @param sliceIndex The index within the sliced array
   * @param offset The starting index of the slice
   * @returns The original index in the tradeButtons array
   */
  getOriginalIndex(sliceIndex: number, offset: number): number {
    return sliceIndex + offset;
  }

  // Load market structure data from the indices API endpoint
  private loadIndicesData() {
    this.isLoading = true;
    
    // First, get the market structure (countries and indices)
    this.mainService.getMarketStructure().subscribe({
      next: (indicesData) => {
        // Build country and market structure from indices data
        this.buildMarketStructure(indicesData);
        
        // After building the structure, load the companies data
        this.fetchCompaniesData();
      },
      error: (error) => {
        console.error('Error loading indices data:', error);
        this.isError = true;
        this.errorMessage = 'Failed to load market structure. Please try again.';
        this.isLoading = false;
      }
    });
  }
  
  // Build market structure from indices data
  private buildMarketStructure(indicesData: any[]) {
    if (!indicesData || !Array.isArray(indicesData)) {
      console.error('Invalid indices data format');
      return;
    }
    
    // Group indices by country and exchange
    const marketStructure: any = {};
    
    // Build the market structure from the API data
    const groupedIndices: Record<string, Record<string, string[]>> = {};
    
    // Process each index from the API data
    for (const index of indicesData) {
      let country = 'Global';
      let market = 'Other Markets';
      
      // Handle Indian indices
      if (index.name.includes('NIFTY') || index.name.includes('GIFT')) {
        country = 'India';
        market = 'NSE (National Stock Exchange of India)';
      } else if (index.name.includes('BSE') || index.name.includes('SENSEX')) {
        country = 'India';
        market = 'BSE (Bombay Stock Exchange)';
      } 
      // Handle US indices
      else if (index.name.includes('S&P')) {
        country = 'United States';
        market = 'Standard & Poor\'s indices';
      } else if (index.name.includes('Dow Jones')) {
        country = 'United States';
        market = 'Dow Jones & Company indices';
      } else if (index.name.includes('NASDAQ')) {
        country = 'United States';
        market = 'Nasdaq indices';
      } else if (index.name.includes('Russell')) {
        country = 'United States';
        market = 'Russell Indexes';
      }
      // Handle European indices
      else if (index.name.includes('FTSE')) {
        country = 'United Kingdom';
        market = 'London Stock Exchange';
      } else if (index.name.includes('DAX')) {
        country = 'Germany';
        market = 'Frankfurt Stock Exchange';
      } else if (index.name.includes('CAC')) {
        country = 'France';
        market = 'Euronext Paris';
      }
      // Handle Asian indices
      else if (index.name.includes('Nikkei') || index.name.includes('TOPIX')) {
        country = 'Japan';
        market = 'Tokyo Stock Exchange';
      } else if (index.name.includes('Hang Seng')) {
        country = 'Hong Kong';
        market = 'Hong Kong Stock Exchange';
      } else if (index.name.includes('Shanghai') || index.name.includes('SSE')) {
        country = 'China';
        market = 'Shanghai Stock Exchange';
      } else if (index.name.includes('Straits Times')) {
        country = 'Singapore';
        market = 'Singapore Exchange';
      } else if (index.name.includes('Tadawul')) {
        country = 'Saudi Arabia';
        market = 'Saudi Stock Exchange (Tadawul)';
      } else if (index.name.includes('ASX')) {
        country = 'Australia';
        market = 'Australian Securities Exchange';
      } else if (index.name.includes('NZX')) {
        country = 'New Zealand';
        market = 'New Zealand Exchange';
      }
      
      // Initialize country and market if needed
      if (!groupedIndices[country]) {
        groupedIndices[country] = {};
      }
      if (!groupedIndices[country][market]) {
        groupedIndices[country][market] = [];
      }
      
      // Add the index to the appropriate country and market
      groupedIndices[country][market].push(index.name);
    }
    
    // Add the grouped indices to the market structure
    for (const [country, markets] of Object.entries(groupedIndices)) {
      marketStructure[country] = markets;
    }
    
    // Add essential structures that might be missing from API data
    if (!marketStructure['India']) {
      marketStructure['India'] = {
        'NSE (National Stock Exchange of India)': ['NIFTY 50', 'NIFTY BANK', 'NIFTY MIDCAP 50', 'NIFTY SMALLCAP 50'],
        'BSE (Bombay Stock Exchange)': ['S&P BSE - 30', 'S&P BSE - 100', 'S&P BSE - 500', 'S&P BSE MidCap']
      };
    }
    
    if (!marketStructure['United States']) {
      marketStructure['United States'] = {
        'Standard & Poor\'s indices': ['S&P 100', 'S&P 500'],
        'Dow Jones & Company indices': ['Dow Jones Industrial Average'],
        'Nasdaq indices': ['NASDAQ Composite', 'NASDAQ-100']
      };
    }
    
    // For other countries - add structure with exact backend names
    marketStructure['United Kingdom'] = {
      'London Stock Exchange': ['FTSE 100', 'FTSE 250', 'FTSE 350']
    };
    
    marketStructure['Japan'] = {
      'Tokyo Stock Exchange': ['Nikkei 225', 'Nikkei 400', 'TOPIX']
    };
    
    marketStructure['China'] = {
      'Shanghai Stock Exchange': ['Shanghai Composite Index', 'SSE 50', 'CSI 300'],
      'Hong Kong Stock Exchange': ['Hang Seng Index', 'Hang Seng China Enterprises']
    };
    
    marketStructure['Germany'] = {
      'Frankfurt Stock Exchange': ['DAX', 'MDAX', 'TecDAX']
    };
    
    marketStructure['France'] = {
      'Euronext Paris': ['CAC 40']
    };
    
    marketStructure['Canada'] = {
      'Toronto Stock Exchange': ['S&P/TSX Composite', 'S&P/TSX 60']
    };
    
    marketStructure['Australia'] = {
      'Australian Securities Exchange': ['S&P/ASX 200', 'S&P/ASX 50']
    };
    
    marketStructure['New Zealand'] = {
      'New Zealand Exchange': ['NZX 50']
    };
    
    marketStructure['Sweden'] = {
      'Stockholm Stock Exchange': ['OMX Stockholm 30', 'OMX Stockholm 60']
    };
    
    marketStructure['Singapore'] = {
      'Singapore Exchange': ['Straits Times Index', 'FTSE ST All-Share']
    };
    
    marketStructure['Sri Lanka'] = {
      'Colombo Stock Exchange': ['All Share Price Index', 'S&P SL20']
    };
    
    marketStructure['Saudi Arabia'] = {
      'Saudi Stock Exchange (Tadawul)': ['Tadawul All Share Index']
    };
    
    marketStructure['Hong Kong'] = {
      'Hong Kong Stock Exchange': ['Hang Seng Index', 'Hang Seng China Enterprises', 'Hang Seng Tech']
    };
    
    // Update the market list with all countries
    this.countryList = Object.keys(marketStructure);
    this.marketList = {};
    this.marketDivision = {};
    
    // Build marketList and marketDivision
    for (const country in marketStructure) {
      this.marketList[country] = Object.keys(marketStructure[country]);
      
      for (const market of this.marketList[country]) {
        this.marketDivision[market] = marketStructure[country][market];
      }
    }
    
    console.log('Built market structure from indices data:', {
      countries: this.countryList.length,
      markets: Object.keys(this.marketList).reduce((total, country) => total + this.marketList[country].length, 0),
      divisions: Object.keys(this.marketDivision).reduce((total, market) => total + this.marketDivision[market].length, 0)
    });
  }

  // Fetch the company data from the API with optimized loading
  private fetchCompaniesData() {
    this.isLoading = true;

    // Use a tiered approach for loading data
    // Start with essential indices and then load the rest
    const essentialIndices = [
      // Indian indices (high priority)
      'NIFTY 50',
      'NIFTY BANK',
      'S&P BSE - 30', // BSE SENSEX
      // US indices (high priority)
      'S&P 100',
      'Dow Jones Industrial Average'
    ];
    
    const secondaryIndices = [
      // Medium priority Indian indices
      'NIFTY MIDCAP 50',
      'NIFTY SMALLCAP 50',
      'S&P BSE - 100', // BSE 100
      // US indices (medium priority)
      'S&P 500',
      'NASDAQ-100',
    ];

    const lowPriorityIndices = [
      // Lower priority international indices
      'NASDAQ Composite',
      'FTSE 100',
      'DAX',
      'CAC 40',
      'Nikkei 225',
      'Hang Seng Index',
      'Shanghai Composite Index',
      'Straits Times Index',
      'S&P/ASX 200',
      'NZX 50',
      'Tadawul All Share Index'
    ];
    
    console.log('Loading essential indices first:', essentialIndices);
    
    // Load essential indices first and then continue with the rest
    this.loadIndicesBatch(essentialIndices).then(() => {
      // Mark as loaded for initial use - allow UI interaction after essential data is loaded
      this.isLoading = false;
      
      // Continue loading secondary indices in the background
      this.loadIndicesBatch(secondaryIndices).then(() => {
        // Finally load low priority indices
        this.loadIndicesBatch(lowPriorityIndices).then(() => {
          console.log('Completed loading ALL companies data');
        });
      });
    })
    .catch(error => {
      console.error('Error loading essential companies data:', error);
      this.isError = true;
      this.errorMessage = 'Failed to load companies data. Please try again.';
      this.isLoading = false;
    });
  }
  
  // Load a batch of indices
  private loadIndicesBatch(indices: string[]): Promise<void[]> {
    // Create promises for loading indices in the batch
    const loadPromises = indices.map(indexName => {
      return this.loadIndexConstituents(indexName);
    });
    
    return Promise.all(loadPromises);
  }
  
  // Load constituents for a specific index
  private loadIndexConstituents(indexName: string): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      // Don't load if already loaded (prevent duplicates)
      if (this.companyList[indexName] && this.companyList[indexName].length > 0) {
        console.log(`Skipping already loaded index: ${indexName}`);
        resolve();
        return;
      }
      
      console.log(`Loading constituents for ${indexName}`);
      
      // Add special handling for BSE indices
      if (indexName.includes('BSE')) {
        // For BSE indices, try to load fallback data from special BSE endpoint
        this.loadBSEStocks(indexName).then(resolve).catch(() => {
          // If BSE fallback fails, try the normal endpoint
          this.loadRegularConstituents(indexName).then(resolve).catch(resolve);
        });
        return;
      }
      
      // Add special handling for NIFTY indices
      if (indexName.includes('NIFTY')) {
        // For NIFTY indices, try to load from dedicated NSE endpoint
        this.loadNiftyStocks(indexName).then(resolve).catch(() => {
          // If NSE fallback fails, try the normal endpoint
          this.loadRegularConstituents(indexName).then(resolve).catch(resolve);
        });
        return;
      }
      
      // For all other indices, load normally
      this.loadRegularConstituents(indexName).then(resolve).catch(resolve);
    });
  }
  
  // Load regular constituents from the index API
  private loadRegularConstituents(indexName: string): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      // Encode the index name for the URL
      const encodedIndexName = encodeURIComponent(indexName);
      
      // Add timeout to prevent long-running requests
      const timeoutMs = 10000; // 10 seconds
      let isResolved = false;
      
      // Create timeout for the request
      const timeout = setTimeout(() => {
        if (!isResolved) {
          console.warn(`Timeout loading constituents for ${indexName}`);
          this.companyList[indexName] = [];
          isResolved = true;
          reject(new Error('Timeout'));
        }
      }, timeoutMs);
      
      // Fetch the constituents
      this.mainService.getConstituents(encodedIndexName).subscribe({
        next: (constituentsData: any[]) => {
          clearTimeout(timeout);
          
          if (!isResolved) {
            if (constituentsData && Array.isArray(constituentsData)) {
              // Filter out invalid entries without symbols or company names
              const validConstituents = constituentsData.filter(item => 
                item && item.symbol && item.company);
                
              if (validConstituents.length > 0) {
                this.companyList[indexName] = validConstituents;
                console.log(`Successfully loaded ${validConstituents.length} constituents for ${indexName}`);
                isResolved = true;
                resolve();
              } else {
                console.warn(`No valid constituents found for ${indexName}`);
                isResolved = true;
                reject(new Error('No valid constituents'));
              }
            } else {
              console.warn(`No constituents data found for ${indexName}`);
              isResolved = true;
              reject(new Error('No constituent data'));
            }
          }
        },
        error: (error: Error) => {
          clearTimeout(timeout);
          
          if (!isResolved) {
            console.error(`Error loading constituents for ${indexName}:`, error);
            isResolved = true;
            reject(error);
          }
        }
      });
    });
  }
  
  // Special handler for BSE stocks
  private loadBSEStocks(indexName: string): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      // Create sample stock data for BSE if API fails
      const fallbackBSEStocks = [
        { symbol: 'RELIANCE.BSE', company: 'Reliance Industries Ltd', sector: 'Energy', price: 2840.45 },
        { symbol: 'TCS.BSE', company: 'Tata Consultancy Services Ltd', sector: 'Information Technology', price: 3560.75 },
        { symbol: 'HDFCBANK.BSE', company: 'HDFC Bank Ltd', sector: 'Financials', price: 1680.20 },
        { symbol: 'INFY.BSE', company: 'Infosys Ltd', sector: 'Information Technology', price: 1420.50 },
        { symbol: 'HINDUNILVR.BSE', company: 'Hindustan Unilever Ltd', sector: 'Consumer Staples', price: 2575.30 },
        { symbol: 'ICICIBANK.BSE', company: 'ICICI Bank Ltd', sector: 'Financials', price: 980.15 },
        { symbol: 'SBIN.BSE', company: 'State Bank of India', sector: 'Financials', price: 620.40 },
        { symbol: 'BHARTIARTL.BSE', company: 'Bharti Airtel Ltd', sector: 'Communication Services', price: 875.25 },
        { symbol: 'ITC.BSE', company: 'ITC Ltd', sector: 'Consumer Staples', price: 440.60 },
        { symbol: 'KOTAKBANK.BSE', company: 'Kotak Mahindra Bank Ltd', sector: 'Financials', price: 1780.90 }
      ];
      
      // Try to get BSE stocks from a special endpoint or use fallback
      this.mainService.getBSEStocks().subscribe({
        next: (stocksData: any[]) => {
          if (stocksData && Array.isArray(stocksData) && stocksData.length > 0) {
            // Use API data if valid
            const validStocks = stocksData.filter(item => item && item.symbol && item.company);
            if (validStocks.length > 0) {
              this.companyList[indexName] = validStocks;
              console.log(`Successfully loaded ${validStocks.length} BSE stocks for ${indexName}`);
              resolve();
            } else {
              // Use fallback if filtered data is empty
              this.companyList[indexName] = fallbackBSEStocks;
              console.log(`Using ${fallbackBSEStocks.length} BSE stocks for ${indexName}`);
              resolve();
            }
          } else {
            // Use fallback if API returns empty data
            this.companyList[indexName] = fallbackBSEStocks;
            console.log(`Using ${fallbackBSEStocks.length} BSE stocks for ${indexName}`);
            resolve();
          }
        },
        error: (error: Error) => {
          // Use fallback on error
          console.error(`Error loading BSE stocks for ${indexName}:`, error);
          this.companyList[indexName] = fallbackBSEStocks;
          console.log(`Using ${fallbackBSEStocks.length} BSE stocks for ${indexName}`);
          resolve();
        }
      });
    });
  }
  
  // Special handler for NIFTY stocks
  private loadNiftyStocks(indexName: string): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      // Create sample stock data for NIFTY if API fails
      const fallbackNiftyStocks = [
        { symbol: 'RELIANCE.NS', company: 'Reliance Industries Ltd', sector: 'Energy', price: 2845.20 },
        { symbol: 'TCS.NS', company: 'Tata Consultancy Services Ltd', sector: 'Information Technology', price: 3565.50 },
        { symbol: 'HDFCBANK.NS', company: 'HDFC Bank Ltd', sector: 'Financials', price: 1682.40 },
        { symbol: 'INFY.NS', company: 'Infosys Ltd', sector: 'Information Technology', price: 1418.70 },
        { symbol: 'HINDUNILVR.NS', company: 'Hindustan Unilever Ltd', sector: 'Consumer Staples', price: 2580.90 },
        { symbol: 'ICICIBANK.NS', company: 'ICICI Bank Ltd', sector: 'Financials', price: 975.30 },
        { symbol: 'SBIN.NS', company: 'State Bank of India', sector: 'Financials', price: 621.80 },
        { symbol: 'BHARTIARTL.NS', company: 'Bharti Airtel Ltd', sector: 'Communication Services', price: 874.10 },
        { symbol: 'ITC.NS', company: 'ITC Ltd', sector: 'Consumer Staples', price: 441.20 },
        { symbol: 'KOTAKBANK.NS', company: 'Kotak Mahindra Bank Ltd', sector: 'Financials', price: 1778.60 }
      ];
      
      // Try to get NIFTY stocks from a special endpoint or use fallback
      this.mainService.getNiftyStocks().subscribe({
        next: (stocksData: any[]) => {
          if (stocksData && Array.isArray(stocksData) && stocksData.length > 0) {
            // Use API data if valid
            const validStocks = stocksData.filter(item => item && item.symbol && item.company);
            if (validStocks.length > 0) {
              this.companyList[indexName] = validStocks;
              console.log(`Successfully loaded ${validStocks.length} NIFTY stocks for ${indexName}`);
              resolve();
            } else {
              // Use fallback if filtered data is empty
              this.companyList[indexName] = fallbackNiftyStocks;
              console.log(`Using ${fallbackNiftyStocks.length} NIFTY stocks for ${indexName}`);
              resolve();
            }
          } else {
            // Use fallback if API returns empty data
            this.companyList[indexName] = fallbackNiftyStocks;
            console.log(`Using ${fallbackNiftyStocks.length} NIFTY stocks for ${indexName}`);
            resolve();
          }
        },
        error: (error: Error) => {
          // Use fallback on error
          console.error(`Error loading NIFTY stocks for ${indexName}:`, error);
          this.companyList[indexName] = fallbackNiftyStocks;
          console.log(`Using ${fallbackNiftyStocks.length} NIFTY stocks for ${indexName}`);
          resolve();
        }
      });
    });
  }

  calcSignalTrade(routeUrl: string | null, index: number) {
    if (!routeUrl) {
      return; // Feature not implemented yet
    }

    // Set the selected companies in the main service regardless of strategy
    this.mainService.setData(this.selectedCompanies.map(symbol => ({ symbol })));

    if (index === 1) { 
      // Swing Trading selected
      // Default to Short-Term if no option is selected
      const timeframe = this.selectedOption || 'Short-Term';
      this.mainService.setSwingTrading(timeframe);

      // Navigate to the swing trading page using the passed routeUrl
      this.router.navigateByUrl(routeUrl);
    } else {
      // Handle other trading strategies - use the routeUrl passed from the template
      this.router.navigateByUrl(routeUrl);
      console.log(`Navigating to: ${routeUrl}`);
    }
  }

  openSearchPopup() {
    // Implement search popup if needed
  }

  // Refresh backend data cache
  refreshCache() {
    this.isLoading = true;
    this.mainService.refreshCache().subscribe({
      next: (response) => {
        console.log('Cache refresh response:', response);
        // Reload market data after cache refresh
        this.loadIndicesData();
        // Show success message
        alert('Market data cache refreshed successfully! Loading fresh data...');
      },
      error: (error) => {
        console.error('Error refreshing cache:', error);
        this.isLoading = false;
        alert('Failed to refresh market data cache. Please try again.');
      }
    });
  }

  // Close the dropdown when clicking outside
  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    // Only take action if the dropdown is open
    if (this.isDropdownOpen) {
      const targetElement = event.target as HTMLElement;
      
      // Check if the click was on a dropdown-related element
      const clickedOnDropdownElement = 
        targetElement.classList.contains('caret-btn') || 
        targetElement.parentElement?.classList.contains('caret-btn') ||
        targetElement.classList.contains('dropdown-menu') ||
        targetElement.parentElement?.classList.contains('dropdown-menu');
      
      // If clicking outside dropdown-related elements, close it
      if (!clickedOnDropdownElement) {
        this.isDropdownOpen = false;
      }
    }
  }
}