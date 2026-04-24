from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class StockData:
    """Main stock data model (supports all Finviz fields)"""
    ticker: str
    company_name: str
    sector: str
    industry: str
    country: Optional[str] = None
    
    # Basic price & volume data
    price: Optional[float] = None
    price_change: Optional[float] = None
    price_change_percent: Optional[float] = None
    volume: Optional[int] = None
    avg_volume: Optional[int] = None
    relative_volume: Optional[float] = None
    
    # New: detailed OHLC data
    prev_close: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    change_from_open: Optional[float] = None
    trades_count: Optional[int] = None
    
    # After-hours trading data
    premarket_price: Optional[float] = None
    premarket_change: Optional[float] = None
    premarket_change_percent: Optional[float] = None
    afterhours_price: Optional[float] = None
    afterhours_change: Optional[float] = None
    afterhours_change_percent: Optional[float] = None
    
    # Market data
    market_cap: Optional[float] = None
    income: Optional[float] = None
    sales: Optional[float] = None
    book_value_per_share: Optional[float] = None
    cash_per_share: Optional[float] = None
    dividend: Optional[float] = None
    dividend_yield: Optional[float] = None
    employees: Optional[int] = None
    
    # New: index & classification info
    index: Optional[str] = None  # Index membership (S&P500, etc.)
    optionable: Optional[bool] = None
    shortable: Optional[bool] = None
    ipo_date: Optional[str] = None
    
    # Valuation metrics
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg: Optional[float] = None
    ps_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    price_to_cash: Optional[float] = None
    price_to_free_cash_flow: Optional[float] = None
    
    # Profitability metrics
    eps: Optional[float] = None
    eps_this_y: Optional[float] = None
    eps_next_y: Optional[float] = None
    eps_past_5y: Optional[float] = None
    eps_next_5y: Optional[float] = None
    sales_past_5y: Optional[float] = None
    eps_growth_this_y: Optional[float] = None
    eps_growth_next_y: Optional[float] = None
    eps_growth_past_5y: Optional[float] = None
    eps_growth_next_5y: Optional[float] = None
    sales_growth_qtr: Optional[float] = None
    eps_growth_qtr: Optional[float] = None
    eps_next_q: Optional[float] = None  # New: next quarter EPS estimate
    
    # Financial health metrics
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    lt_debt_to_equity: Optional[float] = None
    
    # Profitability margins
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    profit_margin: Optional[float] = None
    
    # ROE / ROA / ROI
    roe: Optional[float] = None
    roa: Optional[float] = None
    roi: Optional[float] = None
    roic: Optional[float] = None  # New: return on invested capital
    
    # Dividend data
    payout_ratio: Optional[float] = None
    
    # Ownership structure
    insider_ownership: Optional[float] = None
    insider_transactions: Optional[float] = None
    institutional_ownership: Optional[float] = None
    institutional_transactions: Optional[float] = None
    float_short: Optional[float] = None
    short_ratio: Optional[float] = None
    short_interest: Optional[float] = None
    
    # Share counts
    shares_outstanding: Optional[float] = None
    shares_float: Optional[float] = None
    float_percentage: Optional[float] = None  # New: Float %
    
    # Technical & performance indicators
    volatility: Optional[float] = None
    volatility_week: Optional[float] = None  # New: weekly volatility
    volatility_month: Optional[float] = None  # New: monthly volatility
    beta: Optional[float] = None
    atr: Optional[float] = None
    
    # New: short-term performance
    performance_1min: Optional[float] = None
    performance_2min: Optional[float] = None
    performance_3min: Optional[float] = None
    performance_5min: Optional[float] = None
    performance_10min: Optional[float] = None
    performance_15min: Optional[float] = None
    performance_30min: Optional[float] = None
    performance_1h: Optional[float] = None
    performance_2h: Optional[float] = None
    performance_4h: Optional[float] = None
    
    # Performance
    performance_1w: Optional[float] = None
    performance_1m: Optional[float] = None
    performance_3m: Optional[float] = None
    performance_6m: Optional[float] = None
    performance_ytd: Optional[float] = None
    performance_1y: Optional[float] = None
    performance_2y: Optional[float] = None
    performance_3y: Optional[float] = None
    performance_5y: Optional[float] = None
    performance_10y: Optional[float] = None  # New: 10-year performance
    performance_since_inception: Optional[float] = None  # New: performance since inception
    
    # Moving averages
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    above_sma_20: Optional[bool] = None
    above_sma_50: Optional[bool] = None
    above_sma_200: Optional[bool] = None
    sma_20_relative: Optional[float] = None
    sma_50_relative: Optional[float] = None
    sma_200_relative: Optional[float] = None
    
    # 52-week high & low
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    high_52w_relative: Optional[float] = None
    low_52w_relative: Optional[float] = None
    
    # New: 50-day high & low
    day_50_high: Optional[float] = None
    day_50_low: Optional[float] = None
    all_time_high: Optional[float] = None
    all_time_low: Optional[float] = None
    
    # Technical indicators
    rsi: Optional[float] = None
    rsi_14: Optional[float] = None
    rel_volume: Optional[float] = None
    avg_true_range: Optional[float] = None
    
    # Earnings data
    earnings_date: Optional[str] = None
    earnings_timing: Optional[str] = None
    eps_surprise: Optional[float] = None
    revenue_surprise: Optional[float] = None
    eps_estimate: Optional[float] = None
    revenue_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    revenue_actual: Optional[float] = None
    eps_qoq_growth: Optional[float] = None
    sales_qoq_growth: Optional[float] = None
    eps_revision: Optional[float] = None
    revenue_revision: Optional[float] = None
    
    # Analyst recommendation & target price
    target_price: Optional[float] = None
    analyst_recommendation: Optional[str] = None
    
    # Options data
    average_volume: Optional[int] = None
    
    # ETF-specific fields (new)
    single_category: Optional[str] = None
    asset_type: Optional[str] = None
    etf_type: Optional[str] = None
    sector_theme: Optional[str] = None
    region: Optional[str] = None
    active_passive: Optional[str] = None
    net_expense_ratio: Optional[float] = None
    total_holdings: Optional[int] = None
    aum: Optional[float] = None  # Assets Under Management
    nav: Optional[float] = None  # Net Asset Value
    nav_percent: Optional[float] = None
    
    # ETF flow data (new)
    net_flows_1m: Optional[float] = None
    net_flows_1m_percent: Optional[float] = None
    net_flows_3m: Optional[float] = None
    net_flows_3m_percent: Optional[float] = None
    net_flows_ytd: Optional[float] = None
    net_flows_ytd_percent: Optional[float] = None
    net_flows_1y: Optional[float] = None
    net_flows_1y_percent: Optional[float] = None
    
    # Other Finviz metrics
    gap: Optional[float] = None
    tags: Optional[str] = None  # New: tags
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StockData':
        """Create from dictionary."""
        return cls(**data)

@dataclass
class NewsData:
    """News data model"""
    ticker: str
    title: str
    source: str
    date: datetime
    url: str
    category: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert datetime to string
        data['date'] = self.date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsData':
        """Create from dictionary."""
        # Convert string date to datetime
        if isinstance(data.get('date'), str):
            data['date'] = datetime.fromisoformat(data['date'])
        return cls(**data)

@dataclass
class SectorPerformance:
    """Sector performance data model"""
    sector: str
    performance_1d: float
    performance_1w: float
    performance_1m: float
    performance_3m: float
    performance_6m: float
    performance_1y: float
    stock_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SectorPerformance':
        """Create from dictionary."""
        return cls(**data)

@dataclass
class EarningsData:
    """Earnings data model"""
    ticker: str
    company_name: str
    earnings_date: str
    earnings_timing: str  # "before" or "after"
    
    # Price data
    pre_earnings_price: Optional[float] = None
    post_earnings_price: Optional[float] = None
    premarket_price: Optional[float] = None
    afterhours_price: Optional[float] = None
    current_price: Optional[float] = None
    price_change_percent: Optional[float] = None
    gap_percent: Optional[float] = None
    
    # Volume data
    volume: Optional[int] = None
    avg_volume: Optional[int] = None
    relative_volume: Optional[float] = None
    
    # Earnings results & surprises
    eps_surprise: Optional[float] = None
    revenue_surprise: Optional[float] = None
    eps_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    revenue_estimate: Optional[float] = None
    revenue_actual: Optional[float] = None
    earnings_revision: Optional[str] = None
    
    # Market reaction & analysis
    market_reaction: Optional[str] = None  # "positive", "negative", "neutral"
    volatility: Optional[float] = None
    beta: Optional[float] = None
    performance_4w: Optional[float] = None
    recovery_from_decline: Optional[bool] = None
    trading_opportunity_score: Optional[float] = None  # 1-10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EarningsData':
        """Create from dictionary."""
        return cls(**data)

@dataclass
class ScreeningResult:
    """Container for screening results"""
    query_parameters: Dict[str, Any]
    results: list
    total_count: int
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'query_parameters': self.query_parameters,
            'results': [stock.to_dict() for stock in self.results],
            'total_count': self.total_count,
            'execution_time': self.execution_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScreeningResult':
        """Create from dictionary."""
        results = [StockData.from_dict(item) for item in data.get('results', [])]
        return cls(
            query_parameters=data.get('query_parameters', {}),
            results=results,
            total_count=data.get('total_count', 0),
            execution_time=data.get('execution_time')
        )

# Old mapping constants have been removed and consolidated into constants.py

# Finviz field mapping constants (simple version retained for compatibility)
FINVIZ_FIELD_MAPPING = {
    # Basic info
    'ticker': 'Ticker',
    'company': 'Company',
    'sector': 'Sector',
    'industry': 'Industry',
    'country': 'Country',
    
    # Price & volume
    'price': 'Price',
    'change': 'Change',
    'change_percent': 'Change',
    'volume': 'Volume',
    'avg_volume': 'Average Volume',
    'relative_volume': 'Relative Volume',
    
    # Market data
    'market_cap': 'Market Cap',
    'pe_ratio': 'P/E',
    'forward_pe': 'Forward P/E',
    'peg': 'PEG',
    'eps': 'EPS (ttm)',
    'dividend_yield': 'Dividend Yield',
    
    # Technical indicators
    'rsi': 'Relative Strength Index (14)',
    'beta': 'Beta',
    'volatility': 'Volatility (Week)',
    'performance_1w': 'Performance (Week)',
    'performance_1m': 'Performance (Month)',
    'performance_ytd': 'Performance (YTD)',
    
    # Moving averages
    'sma_20': '20-Day Simple Moving Average',
    'sma_50': '50-Day Simple Moving Average',
    'sma_200': '200-Day Simple Moving Average',
    
    # Other
    'target_price': 'Target Price',
    'analyst_recom': 'Analyst Recom',
    'insider_own': 'Insider Ownership',
    'institutional_own': 'Institutional Ownership',
    'short_interest': 'Short Interest',
    'week_52_high': '52-Week High',
    'week_52_low': '52-Week Low',
    'earnings_date': 'Earnings Date'
}

# Sector constants
SECTORS = [
    'Basic Materials',
    'Communication Services', 
    'Consumer Cyclical',
    'Consumer Defensive',
    'Energy',
    'Financial Services',
    'Healthcare',
    'Industrials',
    'Real Estate',
    'Technology',
    'Utilities'
]

# Market cap filter constants
MARKET_CAP_FILTERS = {
    'mega': 'Mega ($200bln and more)',
    'large': 'Large ($10bln to $200bln)',
    'mid': 'Mid ($2bln to $10bln)',
    'small': 'Small ($300mln to $2bln)',
    'micro': 'Micro ($50mln to $300mln)',
    'nano': 'Nano (under $50mln)',
    'smallover': 'Small+ ($300mln and more)',
    'midover': 'Mid+ ($2bln and more)'
}

@dataclass
class UpcomingEarningsData:
    """Upcoming earnings data model"""
    ticker: str
    company_name: str
    sector: str
    industry: str
    earnings_date: str
    earnings_timing: str  # "before" or "after"
    
    # Basic stock price data
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    avg_volume: Optional[int] = None
    
    # Earnings forecast data
    eps_estimate: Optional[float] = None
    revenue_estimate: Optional[float] = None
    eps_estimate_revision: Optional[float] = None
    revenue_estimate_revision: Optional[float] = None
    analyst_count: Optional[int] = None
    estimate_trend: Optional[str] = None  # "improving", "declining", "stable"
    
    # Historical surprise data
    historical_eps_surprise: Optional[list] = None
    historical_revenue_surprise: Optional[list] = None
    avg_eps_surprise: Optional[float] = None
    avg_revenue_surprise: Optional[float] = None
    
    # Valuation & recommendation data
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg: Optional[float] = None
    target_price: Optional[float] = None
    target_price_upside: Optional[float] = None
    analyst_recommendation: Optional[str] = None
    recent_rating_changes: Optional[list] = None
    
    # Risk assessment metrics
    volatility: Optional[float] = None
    beta: Optional[float] = None
    short_interest: Optional[float] = None
    short_ratio: Optional[float] = None
    insider_ownership: Optional[float] = None
    institutional_ownership: Optional[float] = None
    
    # Performance & technical indicators
    performance_1w: Optional[float] = None
    performance_1m: Optional[float] = None
    performance_3m: Optional[float] = None
    sma_200_relative: Optional[float] = None
    rsi: Optional[float] = None
    
    # Options activity (optional)
    options_volume: Optional[int] = None
    put_call_ratio: Optional[float] = None
    implied_volatility: Optional[float] = None
    

    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpcomingEarningsData':
        """Create from dictionary."""
        return cls(**data)

@dataclass
class SECFilingData:
    """SEC filing data model"""
    ticker: str
    filing_date: str
    report_date: str
    form: str
    description: str
    filing_url: str
    document_url: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SECFilingData':
        """Create from dictionary."""
        return cls(**data)