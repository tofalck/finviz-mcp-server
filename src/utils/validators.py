import re
from typing import Optional, List, Any, Dict, Tuple, Union
from ..constants import ALL_PARAMETERS

def validate_ticker(ticker: str) -> bool:
    """
    Validate a ticker symbol.
    
    Args:
        ticker: Ticker symbol
        
    Returns:
        Whether the ticker is valid
    """
    if not ticker or not isinstance(ticker, str):
        return False
    
    # Basic pattern check (1-5 uppercase letters)
    pattern = r'^[A-Z]{1,5}$'
    return bool(re.match(pattern, ticker.upper()))

def validate_tickers(tickers: str) -> bool:
    """
    Validate multiple ticker symbols.
    
    Args:
        tickers: Comma-separated ticker symbol string
        
    Returns:
        Whether all tickers are valid
    """
    if not tickers or not isinstance(tickers, str):
        return False
    
    # Split by comma and validate each ticker
    ticker_list = [t.strip() for t in tickers.split(',') if t.strip()]
    
    if not ticker_list:
        return False
    
    # Check that all tickers are valid
    return all(validate_ticker(ticker) for ticker in ticker_list)

def parse_tickers(tickers: str) -> List[str]:
    """
    Convert a comma-separated ticker string to a list.
    
    Args:
        tickers: Comma-separated ticker symbol string
        
    Returns:
        List of ticker symbols
    """
    if not tickers or not isinstance(tickers, str):
        return []
    
    # Split by comma, strip whitespace, and convert to uppercase
    return [t.strip().upper() for t in tickers.split(',') if t.strip()]

def validate_price_range(min_price: Optional[Union[int, float, str]], max_price: Optional[Union[int, float, str]]) -> bool:
    """
    Validate a price range.
    
    Args:
        min_price: Minimum price (numeric or Finviz preset format 'o5', 'u10')
        max_price: Maximum price (numeric or Finviz preset format 'o5', 'u10')
        
    Returns:
        Whether the price range is valid
    """
    def _convert_to_float(value):
        """Convert a price value to a float (also handles Finviz format)."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Finviz preset format (e.g. 'o5', 'u10')
            if value.startswith(('o', 'u')):
                try:
                    return float(value[1:])
                except ValueError:
                    return None
            # For numeric string case
            try:
                return float(value)
            except ValueError:
                return None
        return None
    
    min_val = _convert_to_float(min_price)
    max_val = _convert_to_float(max_price)
    
    if min_val is not None and min_val < 0:
        return False
    
    if max_val is not None and max_val < 0:
        return False
    
    if min_val is not None and max_val is not None:
        return min_val <= max_val
    
    return True

def validate_market_cap(market_cap: str) -> bool:
    """
    Validate a market cap filter value.
    
    Args:
        market_cap: Market cap filter value
        
    Returns:
        Whether the market cap filter is valid
    """
    return market_cap in ALL_PARAMETERS['cap']

def validate_earnings_date(earnings_date: str) -> bool:
    """
    Validate an earnings date filter value.
    
    Args:
        earnings_date: Earnings date filter value
        
    Returns:
        Whether the earnings date filter is valid
    """
    # Define valid earnings date values at API level
    valid_api_values = {
        'today_after',
        'today_before', 
        'tomorrow_after',
        'tomorrow_before',
        'yesterday_after',
        'yesterday_before',
        'this_week',
        'next_week',
        'within_2_weeks',
        'thisweek',
        'nextweek',
        'nextdays5'
    }
    
    return earnings_date in valid_api_values

def validate_sector(sector: str) -> bool:
    """
    Validate a sector name.
    
    Args:
        sector: Sector name
        
    Returns:
        Whether the sector name is valid
    """
    # Valid sector names at the API level
    valid_api_sectors = {
        # User-friendly sector names
        'Basic Materials',
        'Communication Services', 
        'Consumer Cyclical',
        'Consumer Defensive',
        'Energy',
        'Financial',
        'Healthcare',
        'Industrials',
        'Real Estate',
        'Technology',
        'Utilities',
        # Internal parameter values are also accepted
        'basicmaterials',
        'communicationservices',
        'consumercyclical', 
        'consumerdefensive',
        'energy',
        'financial',
        'healthcare',
        'industrials',
        'realestate',
        'technology',
        'utilities'
    }
    
    return sector in valid_api_sectors

def validate_percentage(value: float, min_val: float = -100, max_val: float = 1000) -> bool:
    """
    Validate a percentage value.
    
    Args:
        value: Percentage value
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Whether the percentage value is valid
    """
    return min_val <= value <= max_val

def validate_volume(volume: Union[int, float, str]) -> bool:
    """
    Validate a volume value (supports both numeric and Finviz string formats).
    
    Args:
        volume: Volume value (numeric or Finviz format: o100, u500, 500to2000, etc.)
        
    Returns:
        Whether the volume value is valid
    """
    if isinstance(volume, (int, float)):
        return volume >= 0
    
    if isinstance(volume, str):
        # Also check for numeric strings (both integers and floats)
        try:
            return float(volume) >= 0
        except ValueError:
            pass  # If not numeric, proceed to Finviz format check below
            
        # Validate Finviz average volume format
        
        # Under/Over patterns (fixed values)
        fixed_patterns = {
            # Under patterns
            'u50', 'u100', 'u500', 'u750', 'u1000',
            # Over patterns  
            'o50', 'o100', 'o200', 'o300', 'o400', 'o500', 'o750', 'o1000', 'o2000',
            # Existing range patterns (backward compatibility)
            '100to500', '100to1000', '500to1000', '500to10000',
            # Custom
            'frange'
        }
        
        if volume in fixed_patterns:
            return True
        
        # Validate custom range pattern (numbertonumber)
        # e.g.: 500to2000, 100to500, 1000to5000
        import re
        range_pattern = r'^\d+to\d*$'
        if re.match(range_pattern, volume):
            return True
        
        return False
    
    return False

def validate_screening_params(params: Dict[str, Any]) -> List[str]:
    """
    Validate screening parameters (full version).
    
    Args:
        params: Screening parameters
        
    Returns:
        List of error messages (empty list means all valid)
    """
    errors = []
    
    # Validate basic parameters
    basic_params = {
        'exchange': 'exch',
        'index': 'idx', 
        'sector': 'sec',
        'industry': 'ind',
        'country': 'geo',
        'market_cap': 'cap',
        'price': 'sh_price',
        'target_price': 'targetprice',
        'dividend_yield': 'fa_div',
        'short_float': 'sh_short',
        'analyst_recommendation': 'an_recom',
        'option_short': 'sh_opt',
        'earnings_date': 'earningsdate',
        'ipo_date': 'ipodate',
        'average_volume': 'sh_avgvol',
        'relative_volume': 'sh_relvol',
        'current_volume': 'sh_curvol',
        'trades': 'sh_trades',
        'shares_outstanding': 'sh_outstanding',
        'float': 'sh_float'
    }
    
    for param_name, param_key in basic_params.items():
        if param_name in params and params[param_name] is not None:
            if params[param_name] not in ALL_PARAMETERS[param_key]:
                errors.append(f"Invalid {param_name}: {params[param_name]}")
    
    # Check price range
    min_price = params.get('min_price')
    max_price = params.get('max_price')
    if not validate_price_range(min_price, max_price):
        errors.append("Invalid price range")
    
    # Check numeric ranges
    numeric_range_params = [
        'pe_min', 'pe_max', 'forward_pe_min', 'forward_pe_max',
        'peg_min', 'peg_max', 'ps_min', 'ps_max', 'pb_min', 'pb_max',
        'debt_equity_min', 'debt_equity_max', 'roe_min', 'roe_max',
        'roi_min', 'roi_max', 'roa_min', 'roa_max',
        'gross_margin_min', 'gross_margin_max',
        'operating_margin_min', 'operating_margin_max',
        'net_margin_min', 'net_margin_max',
        'rsi_min', 'rsi_max', 'beta_min', 'beta_max',
        'dividend_yield_min', 'dividend_yield_max',
        'volume_min', 'avg_volume_min', 'relative_volume_min',
        'price_change_min', 'price_change_max',
        'performance_week_min', 'performance_month_min',
        'performance_quarter_min', 'performance_halfyear_min',
        'performance_year_min', 'performance_ytd_min',
        'volatility_week_min', 'volatility_month_min',
        'week52_high_distance_min', 'week52_low_distance_min',
        'eps_growth_this_year_min', 'eps_growth_next_year_min',
        'eps_growth_past_5_years_min', 'eps_growth_next_5_years_min',
        'sales_growth_quarter_min', 'sales_growth_past_5_years_min',
        'insider_ownership_min', 'insider_ownership_max',
        'institutional_ownership_min', 'institutional_ownership_max'
    ]
    
    for param in numeric_range_params:
        if param in params and params[param] is not None:
            if not isinstance(params[param], (int, float)):
                errors.append(f"Invalid {param}: must be numeric")
    
    # Multiple sectors check
    if 'sectors' in params and params['sectors']:
        for sector in params['sectors']:
            if not validate_sector(sector):
                errors.append(f"Invalid sector: {sector}")
    
    # Excluded sectors check
    if 'exclude_sectors' in params and params['exclude_sectors']:
        for sector in params['exclude_sectors']:
            if not validate_sector(sector):
                errors.append(f"Invalid exclude_sector: {sector}")
    
    # SMA filter check
    if 'sma_filter' in params and params['sma_filter'] is not None:
        valid_sma_filters = ['above_sma20', 'above_sma50', 'above_sma200', 
                            'below_sma20', 'below_sma50', 'below_sma200', 'none']
        if params['sma_filter'] not in valid_sma_filters:
            errors.append(f"Invalid sma_filter: {params['sma_filter']}")
    
    # Sort criteria check
    if 'sort_by' in params and params['sort_by'] is not None:
        valid_sort_options = [
            'ticker', 'company', 'sector', 'industry', 'country',
            'market_cap', 'pe', 'price', 'change', 'volume',
            'price_change', 'relative_volume', 'performance_week',
            'performance_month', 'performance_quarter', 'performance_year',
            'analyst_recom', 'avg_volume', 'dividend_yield',
            'eps', 'sales', 'float', 'insider_own', 'inst_own',
            'rsi', 'volatility', 'earnings_date', 'ipo_date'
        ]
        if params['sort_by'] not in valid_sort_options:
            errors.append(f"Invalid sort_by: {params['sort_by']}")
    
    # Sort order check
    if 'sort_order' in params and params['sort_order'] is not None:
        if params['sort_order'] not in ['asc', 'desc']:
            errors.append(f"Invalid sort_order: {params['sort_order']}")
    
    # Maximum results count check
    if 'max_results' in params and params['max_results'] is not None:
        max_results = params['max_results']
        if not isinstance(max_results, int) or max_results <= 0 or max_results > 10000:
            errors.append(f"Invalid max_results: {max_results} (must be 1-10000)")
    
    # View check
    if 'view' in params and params['view'] is not None:
        valid_views = ['111', '121', '131', '141', '151', '161', '171']
        if params['view'] not in valid_views:
            errors.append(f"Invalid view: {params['view']}")
    
    return errors

def validate_data_fields(fields: List[str]) -> List[str]:
    """
    Check validity of data fields (complete version)
    
    Args:
        fields: List of data fields
        
    Returns:
        List of invalid fields
    """
    # Dynamically get valid fields from FINVIZ_COMPREHENSIVE_FIELD_MAPPING in constants.py
    try:
        from ..constants import FINVIZ_COMPREHENSIVE_FIELD_MAPPING
    except ImportError:
        # When run directly
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from constants import FINVIZ_COMPREHENSIVE_FIELD_MAPPING
    
    valid_fields = set(FINVIZ_COMPREHENSIVE_FIELD_MAPPING.keys())
    
    # Additional valid fields (for backward compatibility)
    additional_valid_fields = {
        # Alternative field names reported in errors
        'eps_growth_this_y', 'eps_growth_next_y', 'eps_growth_next_5y',
        'eps_growth_past_5y', 'sales_growth_qtr', 'eps_growth_qtr', 
        'sales_growth_qoq', 'performance_1w', 'performance_1m',
        'recommendation', 'analyst_recommendation',
        'insider_own', 'institutional_own', 'insider_ownership', 'institutional_ownership',
        
        # Correct alternative names for invalid field names reported in errors
        'roi',  # Alternative name for roic (Return on Invested Capital)
        'debt_equity',  # Alternative name for debt_to_equity
        'book_value',  # Alternative name for book_value_per_share
        'performance_week',  # Alternative name for performance_1w
        'performance_month',  # Alternative name for performance_1m
        'short_float',  # Alternative name for float_short
        
        # Other alternative field names
        'profit_margin',  # Alias for profit_margin
        'all',  # Special key for retrieving all fields
        
        # Finviz field names actually retrieved (104 fields)
        '200_day_simple_moving_average', '20_day_simple_moving_average', '50_day_high', 
        '50_day_low', '50_day_simple_moving_average', '52_week_high', '52_week_low', 
        'after_hours_change', 'after_hours_close', 'all_time_high', 'all_time_low', 
        'analyst_recom', 'average_true_range', 'average_volume', 'beta', 'book_sh', 
        'cash_sh', 'change', 'change_from_open', 'company', 'country', 'current_ratio', 
        'dividend', 'dividend_yield', 'earnings_date', 'employees', 'eps_growth_next_5_years', 
        'eps_growth_next_year', 'eps_growth_past_5_years', 'eps_growth_quarter_over_quarter', 
        'eps_growth_this_year', 'eps_next_q', 'eps_surprise', 'eps_ttm', 'float_percent', 
        'forward_p_e', 'gap', 'gross_margin', 'high', 'income', 'index', 'industry', 
        'insider_ownership', 'insider_transactions', 'institutional_ownership', 
        'institutional_transactions', 'ipo_date', 'low', 'lt_debt_equity', 'market_cap', 
        'no', 'open', 'operating_margin', 'optionable', 'p_b', 'p_cash', 'p_e', 
        'p_free_cash_flow', 'p_s', 'payout_ratio', 'peg', 'performance_10_minutes', 
        'performance_15_minutes', 'performance_1_hour', 'performance_1_minute', 
        'performance_2_hours', 'performance_2_minutes', 'performance_30_minutes', 
        'performance_3_minutes', 'performance_4_hours', 'performance_5_minutes', 
        'performance_half_year', 'performance_month', 'performance_quarter', 
        'performance_week', 'performance_year', 'performance_ytd', 'prev_close', 
        'price', 'profit_margin', 'quick_ratio', 'relative_strength_index_14', 
        'relative_volume', 'return_on_assets', 'return_on_equity', 'return_on_invested_capital', 
        'revenue_surprise', 'sales', 'sales_growth_past_5_years', 'sales_growth_quarter_over_quarter', 
        'sector', 'shares_float', 'shares_outstanding', 'short_float', 'short_interest', 
        'short_ratio', 'shortable', 'target_price', 'ticker', 'total_debt_equity', 
        'trades', 'volatility_month', 'volatility_week', 'volume'
    }
    
    valid_fields.update(additional_valid_fields)
    
    return [field for field in fields if field not in valid_fields]

def validate_exchange(exchange: str) -> bool:
    """
    Check validity of exchange filter
    
    Args:
        exchange: Exchange code
        
    Returns:
        Whether the exchange code is valid
    """
    return exchange in ALL_PARAMETERS['exch']

def validate_index(index: str) -> bool:
    """
    Check validity of index filter
    
    Args:
        index: Index code
        
    Returns:
        Whether the index code is valid
    """
    return index in ALL_PARAMETERS['idx']

def validate_industry(industry: str) -> bool:
    """
    Check validity of industry filter
    
    Args:
        industry: Industry code
        
    Returns:
        Whether the industry code is valid
    """
    return industry in ALL_PARAMETERS['ind']

def validate_country(country: str) -> bool:
    """
    Check validity of country filter
    
    Args:
        country: Country code
        
    Returns:
        Whether the country code is valid
    """
    return country in ALL_PARAMETERS['geo']

def validate_price_filter(price: str) -> bool:
    """
    Check validity of price filter
    
    Args:
        price: Price filter
        
    Returns:
        Whether the price filter is valid
    """
    return price in ALL_PARAMETERS['sh_price']

def validate_target_price(target_price: str) -> bool:
    """
    Check validity of target price filter
    
    Args:
        target_price: Target price filter
        
    Returns:
        Whether the target price filter is valid
    """
    return target_price in ALL_PARAMETERS['targetprice']

def validate_dividend_yield_filter(dividend_yield: str) -> bool:
    """
    Check validity of dividend yield filter
    
    Args:
        dividend_yield: Dividend yield filter
        
    Returns:
        Whether the dividend yield filter is valid
    """
    return dividend_yield in ALL_PARAMETERS['fa_div']

def validate_short_float(short_float: str) -> bool:
    """
    Check validity of short ratio filter
    
    Args:
        short_float: Short float filter
        
    Returns:
        Whether the short ratio filter is valid
    """
    return short_float in ALL_PARAMETERS['sh_short']

def validate_analyst_recommendation(analyst_rec: str) -> bool:
    """
    Check validity of analyst recommendation filter
    
    Args:
        analyst_rec: Analyst recommendation filter
        
    Returns:
        Whether the analyst recommendation filter is valid
    """
    return analyst_rec in ALL_PARAMETERS['an_recom']

def validate_option_short(option_short: str) -> bool:
    """
    Check validity of option/short filter
    
    Args:
        option_short: Option/short filter
        
    Returns:
        Whether the option/short filter is valid
    """
    return option_short in ALL_PARAMETERS['sh_opt']

def validate_ipo_date(ipo_date: str) -> bool:
    """
    Check validity of IPO date filter
    
    Args:
        ipo_date: IPO date filter
        
    Returns:
        Whether the IPO date filter is valid
    """
    return ipo_date in ALL_PARAMETERS['ipodate']

def validate_volume_filter(volume_type: str, volume_filter: str) -> bool:
    """
    Check validity of volume-related filters
    
    Args:
        volume_type: Volume type ('sh_avgvol', 'sh_relvol', 'sh_curvol', 'sh_trades')
        volume_filter: Volume filter
        
    Returns:
        Whether the volume filter is valid
    """
    if volume_type in ALL_PARAMETERS:
        return volume_filter in ALL_PARAMETERS[volume_type]
    return False

def validate_shares_filter(shares_type: str, shares_filter: str) -> bool:
    """
    Check validity of shares-related filters
    
    Args:
        shares_type: Shares type ('sh_outstanding', 'sh_float')
        shares_filter: Shares filter
        
    Returns:
        Whether the shares filter is valid
    """
    if shares_type in ALL_PARAMETERS:
        return shares_filter in ALL_PARAMETERS[shares_type]
    return False

def validate_custom_range(param_name: str, min_val: Optional[float], max_val: Optional[float]) -> bool:
    """
    Check validity of custom range parameter
    
    Args:
        param_name: Parameter name
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Whether the custom range is valid
    """
    # Validate only for numeric parameters
    numeric_params = {
        'price', 'market_cap', 'pe', 'forward_pe', 'peg', 'ps', 'pb',
        'debt_equity', 'roe', 'roi', 'roa', 'dividend_yield',
        'volume', 'avg_volume', 'relative_volume', 'rsi', 'beta'
    }
    
    if param_name not in numeric_params:
        return False
    
    if min_val is not None and max_val is not None:
        return min_val <= max_val
    
    return True

def get_all_valid_values() -> Dict[str, List[str]]:
    """
    Get all valid parameter values
    
    Returns:
        Dictionary of parameter names and valid values
    """
    return {param: list(values.keys()) for param, values in ALL_PARAMETERS.items()}

def validate_parameter_combination(params: Dict[str, Any]) -> List[str]:
    """
    Check validity of parameter combinations
    
    Args:
        params: Parameter dictionary
        
    Returns:
        List of combination errors
    """
    errors = []
    
    # Check exclusive combination of ETF and stocks
    if params.get('exclude_etfs') and params.get('only_etfs'):
        errors.append("Cannot exclude and include ETFs simultaneously")
    
    # Price range combination check
    price_filters = ['price', 'price_min', 'price_max']
    price_count = sum(1 for p in price_filters if p in params and params[p] is not None)
    if price_count > 1:
        errors.append("Use either price filter OR price_min/max, not both")
    
    # Volume range combination check
    volume_filters = ['average_volume', 'avg_volume_min', 'volume_min']
    volume_count = sum(1 for v in volume_filters if v in params and params[v] is not None)
    if volume_count > 1:
        errors.append("Use either volume filter OR volume_min, not both")
    
    # Relative volume range combination check
    rel_volume_filters = ['relative_volume', 'relative_volume_min']
    rel_volume_count = sum(1 for rv in rel_volume_filters if rv in params and params[rv] is not None)
    if rel_volume_count > 1:
        errors.append("Use either relative_volume filter OR relative_volume_min, not both")
    
    return errors

def sanitize_input(value: Any) -> Any:
    """
    Sanitize input value
    
    Args:
        value: Input value
        
    Returns:
        Sanitized value
    """
    if isinstance(value, str):
        # Basic sanitization to prevent SQL injection and XSS attacks
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        for char in dangerous_chars:
            value = value.replace(char, '')
        return value.strip()

    return value


def validate_and_normalize_raw_filters(raw_filters: str) -> Tuple[List[str], str]:
    """
    Validate and normalize raw FinViz filter codes.

    Accepts comma-separated filter tokens like "cap_small,fa_div_o3,fa_pe_u20".
    Whitespace around tokens is stripped. Pipe characters are allowed for
    compound date filters (e.g. "earningsdate_yesterdayafter|todaybefore").

    Args:
        raw_filters: Comma-separated raw FinViz filter codes.

    Returns:
        Tuple of (errors, normalized) where *errors* is a list of validation
        error strings (empty on success) and *normalized* is the cleaned
        comma-joined string with whitespace removed.
    """
    errors = []  # type: List[str]

    if not raw_filters or not isinstance(raw_filters, str):
        return (["raw_filters must be a non-empty string"], "")

    tokens = raw_filters.split(",")
    stripped = [t.strip() for t in tokens]
    valid_tokens = [t for t in stripped if t]  # drop empty strings

    if not valid_tokens:
        return (["raw_filters must contain at least one valid filter token"], "")

    if len(valid_tokens) > 30:
        return ([f"Too many filter tokens ({len(valid_tokens)}). Maximum is 30."], "")

    token_pattern = re.compile(r'^[a-z0-9_.\-|]+$')
    for token in valid_tokens:
        if not token_pattern.match(token):
            errors.append(f"Invalid filter token: '{token}' (only lowercase a-z, 0-9, _, ., -, | allowed)")

    normalized = ",".join(valid_tokens) if not errors else ""
    return (errors, normalized)


def validate_raw_sort_order(order: str) -> List[str]:
    """
    Validate a raw FinViz sort order string (e.g. "-marketcap", "change").

    A leading '-' indicates descending order; the rest must be lowercase
    alphanumeric or underscore.

    Args:
        order: Sort order string.

    Returns:
        List of error strings (empty on success).
    """
    errors = []  # type: List[str]
    if not order or not isinstance(order, str):
        return ["order must be a non-empty string"]
    if not re.match(r'^-?[a-z0-9_]+$', order):
        errors.append(f"Invalid sort order: '{order}' (only lowercase a-z, 0-9, _, optional leading '-')")
    return errors


def validate_signal(signal: str) -> List[str]:
    """
    Validate a raw FinViz signal string (e.g. "ta_topgainers").

    Args:
        signal: Signal string.

    Returns:
        List of error strings (empty on success).
    """
    errors = []  # type: List[str]
    if not signal or not isinstance(signal, str):
        return ["signal must be a non-empty string"]
    if not re.match(r'^[a-z0-9_]+$', signal):
        errors.append(f"Invalid signal: '{signal}' (only lowercase a-z, 0-9, _ allowed)")
    return errors