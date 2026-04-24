#!/usr/bin/env python3
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .utils.validators import validate_ticker, validate_tickers, parse_tickers, validate_market_cap, validate_earnings_date, validate_price_range, validate_sector, validate_volume, validate_screening_params, validate_data_fields, validate_and_normalize_raw_filters, validate_raw_sort_order, validate_signal
from .utils.formatters import format_large_number
from .finviz_client.base import FinvizClient
from .finviz_client.screener import FinvizScreener
from .finviz_client.news import FinvizNewsClient
from .finviz_client.sector_analysis import FinvizSectorAnalysisClient
from .finviz_client.sec_filings import FinvizSECFilingsClient
from .field_discovery.tools import register_field_discovery_tools
# from .finviz_client.edgar_client import EdgarAPIClient  # Disabled due to missing dependency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = FastMCP("Finviz MCP Server")

# Initialize Finviz clients
finviz_api_key = os.getenv('FINVIZ_API_KEY')
finviz_client = FinvizClient(api_key=finviz_api_key)
finviz_screener = FinvizScreener(api_key=finviz_api_key)
finviz_news = FinvizNewsClient(api_key=finviz_api_key)
finviz_sector = FinvizSectorAnalysisClient(api_key=finviz_api_key)
finviz_sec = FinvizSECFilingsClient(api_key=finviz_api_key)

# Initialize EDGAR API client
# edgar_client = EdgarAPIClient()  # Disabled due to missing dependency

# Create stub for EDGAR client when disabled
class EdgarClientStub:
    def get_filing_document_content(self, *args, **kwargs):
        return {"status": "error", "error": "EDGAR API client is disabled due to missing dependencies"}
    
    def get_multiple_filing_contents(self, *args, **kwargs):
        return []
    
    def get_company_filings(self, *args, **kwargs):
        return []
    
    def _get_cik_from_ticker(self, *args, **kwargs):
        return None
    
    def get_company_concept(self, *args, **kwargs):
        return {"error": "EDGAR API client is disabled due to missing dependencies"}
    
    @property
    def client(self):
        class StubClient:
            def get_company_facts(self, *args, **kwargs):
                return None
        return StubClient()

edgar_client = EdgarClientStub()

@server.tool()
def earnings_screener(
    earnings_date: str,
    market_cap: Optional[str] = None,
    min_price: Optional[Union[int, float, str]] = None,
    max_price: Optional[Union[int, float, str]] = None,
    min_volume: Optional[Union[int, float, str]] = None,
    sectors: Optional[List[str]] = None,
    premarket_price_change: Optional[Dict[str, Any]] = None,
    afterhours_price_change: Optional[Dict[str, Any]] = None
) -> List[TextContent]:
    """
    Screen stocks with upcoming earnings announcements
    
    Args:
        earnings_date: Earnings date specification (today_after, tomorrow_before, this_week, within_2_weeks)
        market_cap: Market cap filter (small, mid, large, mega)
        min_price: Minimum stock price
        max_price: Maximum stock price
        min_volume: Minimum volume
        sectors: Target sectors
        premarket_price_change: Pre-market price change filter
        afterhours_price_change: After-hours price change filter
    """
    try:
        # Validate parameters
        if not validate_earnings_date(earnings_date):
            raise ValueError(f"Invalid earnings_date: {earnings_date}")
        
        if market_cap is not None and not validate_market_cap(market_cap):
            raise ValueError(f"Invalid market_cap: {market_cap}")
        
        if not validate_price_range(min_price, max_price):
            raise ValueError("Invalid price range")
        
        if min_volume is not None and not validate_volume(min_volume):
            raise ValueError(f"Invalid min_volume: {min_volume}")
        
        if sectors:
            for sector in sectors:
                if not validate_sector(sector):
                    raise ValueError(f"Invalid sector: {sector}")
        
        # Prepare parameters
        params = {
            'earnings_date': earnings_date,
            'market_cap': market_cap,
            'min_price': min_price,
            'max_price': max_price,
            'min_volume': min_volume,
            'sectors': sectors or [],
            'premarket_price_change': premarket_price_change,
            'afterhours_price_change': afterhours_price_change
        }
        
        results = finviz_screener.earnings_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No stocks found matching the criteria.")]
        
        output_lines = [
            f"Earnings Screening Results ({len(results)} stocks found):",
            "=" * 60,
            "",
            "Default Screening Conditions Applied:",
            "- Market Cap: Small and above ($300M+)",
            "- Earnings Date: Yesterday after-hours OR today before-market",
            "- EPS Revision: Positive (upward revision)",
            "- Average Volume: 200,000+",
            "- Price: $10+",
            "- Price Trend: Positive change",
            "- 4-Week Performance: 0% to negative (recovery candidates)",
            "- Volatility: 1x and above",
            "- Stocks Only: ETFs excluded",
            "- Sort: EPS Surprise (descending)",
            "",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Change: {stock.price_change:.2f}%" if stock.price_change else "Change: N/A",
                f"EPS Surprise: {stock.eps_surprise:.2f}%" if stock.eps_surprise else "EPS Surprise: N/A",
                f"Revenue Surprise: {stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "Revenue Surprise: N/A",
                f"Volatility: {stock.volatility:.2f}" if stock.volatility else "Volatility: N/A",
                f"1M Performance: {stock.performance_1m:.2f}%" if stock.performance_1m else "1M Performance: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in earnings_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def volume_surge_screener() -> List[TextContent]:
    """
    Screen stocks with volume surge and price increase (fixed conditions)
    
    Fixed filter conditions (cannot be changed):
    f=cap_smallover,ind_stocksonly,sh_avgvol_o100,sh_price_o10,sh_relvol_o1.5,ta_change_u2,ta_sma200_pa&ft=4&o=-change
    
    - Market cap: small or above ($300M+)
    - Stocks only: ETFs excluded
    - Average volume: 100,000+
    - Stock price: $10 or more
    - Relative volume: 1.5x or more
    - Price change: +2% or more
    - Above 200-day moving average
    - Sorted by price change descending
    - Retrieve all records (no limit)
    
    No parameters - all conditions are fixed
    """
    try:
        # Run with fixed conditions (no parameters)
        results = finviz_screener.volume_surge_screener()
        
        if not results:
            return [TextContent(type="text", text="No stocks found matching the fixed volume surge criteria.")]
        
        # Display fixed conditions
        fixed_conditions = [
            "Fixed filter conditions:",
            "- Market cap: small or above ($300M+)",
            "- Stocks only: ETFs excluded",
            "- Average volume: 100,000+",
            "- Stock price: $10 or more",
            "- Relative volume: 1.5x or more",
            "- Price change: +2% or more",
            "- Above 200-day moving average",
            "- Sorted by price change descending",
            "- Retrieve all records (no limit)"
        ]
        
        # Concise output format (tickers only)
        output_lines = [
            f"Volume Surge Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ] + fixed_conditions + ["", "Detected Tickers:", "-" * 40, ""]
        
        # Display tickers 10 per line
        tickers = [stock.ticker for stock in results]
        for i in range(0, len(tickers), 10):
            line_tickers = tickers[i:i+10]
            output_lines.append(" | ".join(line_tickers))
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in volume_surge_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]



@server.tool()
def get_stock_fundamentals(
    ticker: str,
    data_fields: Optional[List[str]] = None
) -> List[TextContent]:
    """
    Get fundamental data for individual stocks (all 128 columns supported)
    
    Args:
        ticker: Stock ticker
        data_fields: Data fields to retrieve (all fields if not specified)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        # Validate data fields
        if data_fields:
            field_errors = validate_data_fields(data_fields)
            if field_errors:
                raise ValueError(f"Invalid data fields: {', '.join(field_errors)}")
        
        # Get fundamental data
        fundamental_data = finviz_client.get_stock_fundamentals(ticker, data_fields)
        
        if not fundamental_data:
            return [TextContent(type="text", text=f"No data found for ticker: {ticker}")]
        
        # Format output with categories
        output_lines = [
            f"📊 Fundamental Data for {ticker}:",
            "=" * 60,
            ""
        ]
        
        # Helper function for data retrieval
        def get_data(key, default=None):
            if isinstance(fundamental_data, dict):
                return fundamental_data.get(key, default)
            else:
                return getattr(fundamental_data, key, default)
        
        # Display important basic info first
        basic_info = {
            'Company': get_data('company'),  # Actual retrieved field name
            'Sector': get_data('sector'),
            'Industry': get_data('industry'),
            'Country': get_data('country'),
            'Market Cap': get_data('market_cap'),  # Actual retrieved field name
            'Price': get_data('price'),
            'Volume': get_data('volume'),
            'Avg Volume': get_data('average_volume')  # Actual retrieved field name
        }
        
        output_lines.append("📋 Basic Information:")
        output_lines.append("-" * 30)
        for key, value in basic_info.items():
            if value is not None:
                if key == 'Price' and isinstance(value, (int, float)):
                    output_lines.append(f"{key:15}: ${value:.2f}")
                elif key in ['Volume', 'Avg Volume'] and isinstance(value, (int, float)):
                    output_lines.append(f"{key:15}: {value:,}")
                elif key == 'Market Cap' and isinstance(value, (int, float)):
                    # Market cap data stored in millions, multiply by 1M before converting
                    actual_value = value * 1e6  # Convert million-dollar unit to actual amount
                    if actual_value >= 1e12:  # 1 trillion or more
                        output_lines.append(f"{key:15}: ${actual_value/1e12:.2f}T")
                    elif actual_value >= 1e9:  # 1 billion or more
                        output_lines.append(f"{key:15}: ${actual_value/1e9:.2f}B")
                    elif actual_value >= 1e6:  # 1 million or more
                        output_lines.append(f"{key:15}: ${actual_value/1e6:.2f}M")
                    else:
                        output_lines.append(f"{key:15}: ${actual_value:,.0f}")
                else:
                    output_lines.append(f"{key:15}: {value}")
        output_lines.append("")
        
        # Valuation indicators - fix field names
        valuation_metrics = {
            'P/E Ratio': get_data('p_e'),  # Actual retrieved field name
            'Forward P/E': get_data('forward_p_e'),
            'PEG': get_data('peg'),
            'P/S Ratio': get_data('p_s'),
            'P/B Ratio': get_data('p_b'),
            'EPS': get_data('eps_ttm'),
            'Dividend Yield': get_data('dividend_yield')
        }
        
        if any(v is not None for v in valuation_metrics.values()):
            output_lines.append("💰 Valuation Metrics:")
            output_lines.append("-" * 30)
            for key, value in valuation_metrics.items():
                if value is not None:
                    if key == 'Dividend Yield' and isinstance(value, (int, float)):
                        output_lines.append(f"{key:15}: {value:.2f}%")
                    elif isinstance(value, (int, float)):
                        output_lines.append(f"{key:15}: {value:.2f}")
                    else:
                        output_lines.append(f"{key:15}: {value}")
            output_lines.append("")
        
        # Performance indicators - fix field names
        performance_metrics = {
            '1 Week': get_data('performance_week'),  # Actual retrieved field name
            '1 Month': get_data('performance_month'),  # Actual retrieved field name
            '3 Months': get_data('performance_quarter'),  # Actual retrieved field name
            '6 Months': get_data('performance_half_year'),  # Actual retrieved field name
            'YTD': get_data('performance_ytd'),
            '1 Year': get_data('performance_year')  # Actual retrieved field name
        }
        
        if any(v is not None for v in performance_metrics.values()):
            output_lines.append("📈 Performance:")
            output_lines.append("-" * 30)
            for key, value in performance_metrics.items():
                if value is not None and isinstance(value, (int, float)):
                    output_lines.append(f"{key:15}: {value:+.2f}%")
            output_lines.append("")
        
        # Earnings related data
        earnings_data = {
            'Earnings Date': get_data('earnings_date'),
            'EPS Surprise': get_data('eps_surprise'),
            'Revenue Surprise': get_data('revenue_surprise'),
            'EPS Growth QoQ': get_data('eps_growth_quarter_over_quarter'),
            'Sales Growth QoQ': get_data('sales_growth_quarter_over_quarter')
        }
        
        if any(v is not None for v in earnings_data.values()):
            output_lines.append("📊 Earnings Data:")
            output_lines.append("-" * 30)
            for key, value in earnings_data.items():
                if value is not None:
                    if key in ['EPS Surprise', 'Revenue Surprise', 'EPS Growth QoQ', 'Sales Growth QoQ'] and isinstance(value, (int, float)):
                        output_lines.append(f"{key:15}: {value:+.2f}%")
                    else:
                        output_lines.append(f"{key:15}: {value}")
            output_lines.append("")
        
        # Technical indicators
        technical_data = {
            'RSI': get_data('relative_strength_index_14'),
            'Beta': get_data('beta'),
            'Volatility': get_data('volatility_week'),
            'Relative Volume': get_data('relative_volume'),
            '20D SMA': get_data('20_day_simple_moving_average') or get_data('sma_20'),
            '50D SMA': get_data('50_day_simple_moving_average') or get_data('sma_50'),
            '200D SMA': get_data('200_day_simple_moving_average') or get_data('sma_200'),
            '52W High': get_data('52_week_high'),
            '52W Low': get_data('52_week_low')
        }
        
        if any(v is not None for v in technical_data.values()):
            output_lines.append("🔧 Technical Indicators:")
            output_lines.append("-" * 30)
            for key, value in technical_data.items():
                if value is not None:
                    if key in ['52W High', '52W Low'] and isinstance(value, (int, float)):
                        output_lines.append(f"{key:15}: ${value:.2f}")
                    elif isinstance(value, (int, float)):
                        output_lines.append(f"{key:15}: {value:.2f}")
                    else:
                        output_lines.append(f"{key:15}: {value}")
            output_lines.append("")
        
        # Summary of all fields
        # Determine if fundamental_data is a dict or object
        if isinstance(fundamental_data, dict):
            fundamental_data_dict = fundamental_data
        else:
            fundamental_data_dict = fundamental_data.to_dict() if hasattr(fundamental_data, 'to_dict') else dict(fundamental_data)
            
        non_null_fields = sum(1 for v in fundamental_data_dict.values() if v is not None)
        total_fields = len(fundamental_data_dict)
        
        output_lines.extend([
            f"📋 Data Coverage: {non_null_fields}/{total_fields} fields ({non_null_fields/total_fields*100:.1f}%)",
            f"🔍 All Available Fields: {', '.join(sorted([k for k, v in fundamental_data_dict.items() if v is not None]))}"
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_stock_fundamentals: {str(e)}")
        raise e  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Error in get_stock_fundamentals: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_multiple_stocks_fundamentals(
    tickers: List[str],
    data_fields: Optional[List[str]] = None
) -> List[TextContent]:
    """
    Bulk fetch fundamental data for multiple stocks (all 128 columns supported)
    
    Args:
        tickers: Stock ticker list
        data_fields: Data fields to retrieve (all fields if not specified)
    """
    try:
        if not tickers:
            raise ValueError("No tickers provided")
        
        # Validate all tickers
        invalid_tickers = [ticker for ticker in tickers if not validate_ticker(ticker)]
        if invalid_tickers:
            raise ValueError(f"Invalid tickers: {', '.join(invalid_tickers)}")
        
        # Validate data fields
        if data_fields:
            field_errors = validate_data_fields(data_fields)
            if field_errors:
                raise ValueError(f"Invalid data fields: {', '.join(field_errors)}")
        
        results = finviz_client.get_multiple_stocks_fundamentals(tickers, data_fields)
        
        if not results:
            return [TextContent(type="text", text="No data found for any of the provided tickers.")]
        
        # Format output with enhanced table view
        output_lines = [
            f"📊 Fundamental Data for {len(results)} stocks:",
            "=" * 80,
            ""
        ]
        
        # Create comparison table for key metrics
        key_metrics = [
            ('Ticker', 'ticker'),
            ('Company', 'company'),
            ('Sector', 'sector'),
            ('Price', 'price'),
            ('Market Cap', 'market_cap'),  # Actual retrieved field name
            ('P/E', 'p_e'),  # Actual retrieved field name
            ('Volume', 'volume'),
            ('1D Perf', 'change'),  # Today's performance
            ('1W Perf', 'performance_week'),  # Actual retrieved field name
            ('EPS Surprise', 'eps_surprise')  # Actual retrieved field name
        ]
        
        # Table header
        header = " | ".join([f"{name:12}" for name, _ in key_metrics])
        output_lines.append(header)
        output_lines.append("-" * len(header))
        
        # Helper function to get value from result (dict or object)
        def get_value(result, field):
            if isinstance(result, dict):
                return result.get(field)
            else:
                return getattr(result, field, None)
        
        # Table rows
        for result in results:
            row_values = []
            for name, field in key_metrics:
                value = get_value(result, field)
                if value is not None:
                    if field == 'price' and isinstance(value, (int, float)):
                        row_values.append(f"${value:.2f}".ljust(12))
                    elif field == 'market_cap' and isinstance(value, (int, float)):
                        # Market cap data stored in millions, multiply by 1M before converting
                        actual_value = value * 1e6  # Convert million-dollar unit to actual amount
                        if actual_value >= 1e12:  # 1 trillion or more
                            row_values.append(f"${actual_value/1e12:.1f}T".ljust(12))
                        elif actual_value >= 1e9:  # 1 billion or more
                            row_values.append(f"${actual_value/1e9:.1f}B".ljust(12))
                        elif actual_value >= 1e6:  # 1 million or more
                            row_values.append(f"${actual_value/1e6:.1f}M".ljust(12))
                        else:
                            row_values.append(f"${actual_value:,.0f}".ljust(12))
                    elif field in ['p_e', 'change', 'performance_week', 'eps_surprise'] and isinstance(value, (int, float)):
                        if field in ['change', 'performance_week']:
                            row_values.append(f"{value:.2f}%".ljust(12))
                        else:
                            row_values.append(f"{value:.2f}".ljust(12))
                    elif field == 'volume' and isinstance(value, (int, float)):
                        if value >= 1e6:
                            row_values.append(f"{value/1e6:.1f}M".ljust(12))
                        elif value >= 1e3:
                            row_values.append(f"{value/1e3:.1f}K".ljust(12))
                        else:
                            row_values.append(f"{value:,.0f}".ljust(12))
                    else:
                        str_value = str(value)
                        if len(str_value) > 12:
                            str_value = str_value[:9] + "..."
                        row_values.append(str_value.ljust(12))
                else:
                    row_values.append("N/A".ljust(12))
            
            row = " | ".join(row_values)
            output_lines.append(row)
        
        output_lines.append("")
        
        # Detailed breakdown for each stock
        output_lines.append("📋 Detailed Data:")
        output_lines.append("=" * 40)
        
        for i, result in enumerate(results, 1):
            ticker = get_value(result, 'ticker') or 'Unknown'
            company = get_value(result, 'company') or 'N/A'
            output_lines.append(f"\n{i}. {ticker} - {company}")
            output_lines.append("-" * 50)
            
            # Categorized data
            categories = {
                "📈 Performance": [
                    ('1D', 'change'), ('1W', 'performance_week'), ('1M', 'performance_month'), 
                    ('3M', 'performance_quarter'), ('YTD', 'performance_ytd')
                ],
                "💰 Valuation": [
                    ('P/E', 'p_e'), ('Forward P/E', 'forward_p_e'),
                    ('PEG', 'peg'), ('P/S', 'p_s'), ('P/B', 'p_b')
                ],
                "📊 Earnings": [
                    ('EPS', 'eps_ttm'), ('EPS Surprise', 'eps_surprise'),
                    ('Revenue Surprise', 'revenue_surprise'),
                    ('EPS Growth QoQ', 'eps_growth_quarter_over_quarter')
                ],
                "🔧 Technical": [
                    ('RSI', 'relative_strength_index_14'), ('Beta', 'beta'),
                    ('Volatility', 'volatility_week'), ('Relative Vol', 'relative_volume'),
                    ('20D SMA', '20_day_simple_moving_average'), ('50D SMA', '50_day_simple_moving_average'),
                    ('200D SMA', '200_day_simple_moving_average'), ('52W High', '52_week_high'),
                    ('52W Low', '52_week_low')
                ]
            }
            
            for category, fields in categories.items():
                values = [(name, get_value(result, field)) for name, field in fields if get_value(result, field) is not None]
                if values:
                    output_lines.append(f"  {category}: " + ", ".join([
                        f"{name}={val:.2f}{'%' if 'Performance' in category or name in ['EPS Surprise', 'Revenue Surprise'] else ''}"
                        if isinstance(val, (int, float)) else f"{name}={val}"
                        for name, val in values
                    ]))
            
            # Data coverage
            if isinstance(result, dict):
                result_dict = result
            elif hasattr(result, 'to_dict'):
                result_dict = result.to_dict()
            else:
                result_dict = vars(result) if hasattr(result, '__dict__') else {}
                
            non_null_fields = sum(1 for v in result_dict.values() if v is not None)
            total_fields = len(result_dict)
            output_lines.append(f"  📋 Data Coverage: {non_null_fields}/{total_fields} fields ({non_null_fields/total_fields*100:.1f}%)")
        
        # Summary
        output_lines.extend([
            "",
            "📊 Summary:",
            f"Total stocks processed: {len(results)}",
            f"Average data coverage: {sum(sum(1 for v in (result if isinstance(result, dict) else result.to_dict() if hasattr(result, 'to_dict') else vars(result) if hasattr(result, '__dict__') else {}).values() if v is not None)/len(result if isinstance(result, dict) else result.to_dict() if hasattr(result, 'to_dict') else vars(result) if hasattr(result, '__dict__') else {'dummy': None}) for result in results)/len(results)*100:.1f}%"
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_multiple_stocks_fundamentals: {str(e)}")
        raise e  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Error in get_multiple_stocks_fundamentals: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def trend_reversion_screener(
    market_cap: Optional[str] = "mid_large",
    eps_growth_qoq: Optional[float] = None,
    revenue_growth_qoq: Optional[float] = None,
    rsi_max: Optional[float] = None,
    sectors: Optional[List[str]] = None,
    exclude_sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    Screen trend reversal candidate stocks
    
    Args:
        market_cap: Market cap filter (mid_large, large, mega)
        eps_growth_qoq: Minimum EPS growth rate (QoQ)
        revenue_growth_qoq: Minimum revenue growth rate (QoQ)
        rsi_max: Maximum RSI value
        sectors: Target sectors
        exclude_sectors: Sectors to exclude
    """
    try:
        params = {
            'market_cap': market_cap,
            'eps_growth_qoq': eps_growth_qoq,
            'revenue_growth_qoq': revenue_growth_qoq,
            'rsi_max': rsi_max,
            'sectors': sectors or [],
            'exclude_sectors': exclude_sectors or []
        }
        
        results = finviz_screener.trend_reversion_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No trend reversal candidates found.")]
        
        output_lines = [
            f"Trend Reversal Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"P/E Ratio: {stock.pe_ratio:.2f}" if stock.pe_ratio else "P/E Ratio: N/A",
                f"RSI: {stock.rsi:.2f}" if stock.rsi else "RSI: N/A",
                f"EPS Growth: {stock.eps_qoq_growth:.2f}%" if stock.eps_qoq_growth else "EPS Growth: N/A",
                f"Revenue Growth: {stock.sales_qoq_growth:.2f}%" if stock.sales_qoq_growth else "Revenue Growth: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in trend_reversion_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def uptrend_screener() -> List[TextContent]:
    """
    Screen uptrend stocks (fixed conditions)
    
    Fixed filter conditions:
    - Market cap: micro or above ($50M+)
    - Average volume: 100K+
    - Stock price: 10 or more
    - Within 30% of 52-week high
    - 4-week performance positive
    - Above 20-day moving average
    - Above 200-day moving average
    - 50-day moving average above 200-day moving average
    - Stocks only
    - EPS growth rate (annual) sorted descending
    
    No parameters - all conditions are fixed
    """
    try:
        # Run with fixed parameters
        results = finviz_screener.uptrend_screener()
        
        if not results:
            return [TextContent(type="text", text="No stocks found matching the fixed uptrend criteria.")]
        
        # Display fixed conditions
        fixed_conditions = [
            "Fixed Filter Criteria:",
            "- Market Cap: Micro+ ($50M+)",
            "- Avg Volume: 100K+",
            "- Price: $10+",
            "- Within 30% of 52W high",
            "- 4W Performance: Up",
            "- Above SMA20",
            "- Above SMA200", 
            "- SMA50 above SMA200",
            "- Stocks only",
            "- Sorted by EPS growth YoY desc"
        ]
        
        # Display only tickers compactly
        tickers = [stock.ticker for stock in results]
        
        output_lines = [
            f"Uptrend Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ] + fixed_conditions + [
            "",
            f"Detected Stocks ({len(tickers)} items):",
            "-" * 40,
            ""
        ]
        
        # Display tickers 10 per line
        ticker_lines = []
        for i in range(0, len(tickers), 10):
            line_tickers = tickers[i:i+10]
            ticker_lines.append("  " + " | ".join(line_tickers))
        
        output_lines.extend(ticker_lines)
        output_lines.append("")
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in uptrend_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def dividend_growth_screener(
    market_cap: Optional[str] = "midover",
    min_dividend_yield: Optional[float] = 2.0,
    max_dividend_yield: Optional[float] = None,
    min_dividend_growth: Optional[float] = None,
    min_payout_ratio: Optional[float] = None,
    max_payout_ratio: Optional[float] = None,
    min_roe: Optional[float] = None,
    max_debt_equity: Optional[float] = None,
    max_pb_ratio: Optional[float] = 5.0,
    max_pe_ratio: Optional[float] = 30.0,
    eps_growth_5y_positive: Optional[bool] = True,
    eps_growth_qoq_positive: Optional[bool] = True,
    eps_growth_yoy_positive: Optional[bool] = True,
    sales_growth_5y_positive: Optional[bool] = True,
    sales_growth_qoq_positive: Optional[bool] = True,
    country: Optional[str] = "USA",
    stocks_only: Optional[bool] = True,
    sort_by: Optional[str] = "sma200",
    sort_order: Optional[str] = "asc",
    max_results: Optional[int] = 100
) -> List[TextContent]:
    """
    Screen dividend growth stocks
    
    Default conditions (can be changed):
    - Market cap: mid or above ($2B+)
    - Dividend yield: 2% or more
    - EPS 5-year growth: positive
    - EPS QoQ growth: positive
    - EPS YoY growth: positive
    - P/B ratio: 5 or less
    - P/E ratio: 30 or less
    - Sales 5-year growth: positive
    - Sales QoQ growth: positive
    - Region: United States
    - Stocks only
    - Sorted by 200-day moving average
    
    Args:
        market_cap: Market cap filter (default: midover)
        min_dividend_yield: Minimum dividend yield (default: 2.0)
        max_dividend_yield: Maximum dividend yield
        min_dividend_growth: Minimum dividend growth rate
        min_payout_ratio: Minimum payout ratio
        max_payout_ratio: Maximum payout ratio
        min_roe: Minimum ROE
        max_debt_equity: Maximum debt-to-equity ratio
        max_pb_ratio: Maximum P/B ratio (default: 5.0)
        max_pe_ratio: Maximum P/E ratio (default: 30.0)
        eps_growth_5y_positive: EPS 5-year growth positive (default: True)
        eps_growth_qoq_positive: EPS QoQ growth positive (default: True)
        eps_growth_yoy_positive: EPS YoY growth positive (default: True)
        sales_growth_5y_positive: Sales 5-year growth positive (default: True)
        sales_growth_qoq_positive: Sales QoQ growth positive (default: True)
        country: Region (default: USA)
        stocks_only: Stocks only (default: True)
        sort_by: Sort criteria (default: sma200)
        sort_order: Sort order (default: asc)
    """
    try:
        params = {
            'market_cap': market_cap,
            'min_dividend_yield': min_dividend_yield,
            'max_dividend_yield': max_dividend_yield,
            'min_dividend_growth': min_dividend_growth,
            'min_payout_ratio': min_payout_ratio,
            'max_payout_ratio': max_payout_ratio,
            'min_roe': min_roe,
            'max_debt_equity': max_debt_equity,
            'max_pb_ratio': max_pb_ratio,
            'max_pe_ratio': max_pe_ratio,
            'eps_growth_5y_positive': eps_growth_5y_positive,
            'eps_growth_qoq_positive': eps_growth_qoq_positive,
            'eps_growth_yoy_positive': eps_growth_yoy_positive,
            'sales_growth_5y_positive': sales_growth_5y_positive,
            'sales_growth_qoq_positive': sales_growth_qoq_positive,
            'country': country,
            'stocks_only': stocks_only,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'max_results': max_results
        }
        
        results = finviz_screener.dividend_growth_screener(**params)
        
        # Debug: log the first few results to check dividend_yield values
        if results:
            logger.info(f"Debug: First 3 results dividend yields: {[(stock.ticker, stock.dividend_yield) for stock in results[:3]]}")
            # Add a unique marker to verify code changes are active
            print(f"CLAUDE_DEBUG_MARKER: First 3 results dividend yields: {[(stock.ticker, stock.dividend_yield) for stock in results[:3]]}")
        
        if not results:
            return [TextContent(type="text", text="No dividend growth stocks found.")]
        
        # Display default conditions
        default_conditions = [
            "Default Criteria:",
            "- Market Cap: Mid+ ($2B+)",
            "- Dividend Yield: 2%+",
            "- EPS 5Y Growth: Positive",
            "- EPS QoQ Growth: Positive",
            "- EPS YoY Growth: Positive",
            "- P/B Ratio: ≤5",
            "- P/E Ratio: ≤30",
            "- Sales 5Y Growth: Positive",
            "- Sales QoQ Growth: Positive",
            "- Region: USA",
            "- Stocks Only",
            "- Sorted by SMA200"
        ]
        
        output_lines = [
            f"Dividend Growth Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ]
        
        # Display default conditions
        output_lines.extend(default_conditions)
        output_lines.extend(["", "=" * 60, ""])
        
        # Limit results to maximum count
        limited_results = results[:max_results] if max_results else results
        
        for stock in limited_results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Dividend Yield: {stock.dividend_yield:.2f}%" if stock.dividend_yield is not None else "Dividend Yield: N/A",
                f"P/E Ratio: {stock.pe_ratio:.2f}" if stock.pe_ratio else "P/E Ratio: N/A",
                f"Market Cap: {stock.market_cap}" if stock.market_cap else "Market Cap: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in dividend_growth_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def etf_screener(
    strategy_type: Optional[str] = "long",
    asset_class: Optional[str] = "equity",
    min_aum: Optional[float] = None,
    max_expense_ratio: Optional[float] = None
) -> List[TextContent]:
    """
    ETF strategy screening
    
    Args:
        strategy_type: Strategy type (long, short)
        asset_class: Asset class (equity, bond, commodity, currency)
        min_aum: Minimum assets under management
        max_expense_ratio: Maximum expense ratio
    """
    try:
        params = {
            'strategy_type': strategy_type,
            'asset_class': asset_class,
            'min_aum': min_aum,
            'max_expense_ratio': max_expense_ratio
        }
        
        results = finviz_screener.etf_screener(**params)
        
        if not results:
            return [TextContent(type="text", text="No ETFs found matching criteria.")]
        
        output_lines = [
            f"ETF Screening Results ({len(results)} ETFs found):",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Name: {stock.company_name}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"Volume: {stock.volume:,}" if stock.volume else "Volume: N/A",
                f"Change: {stock.price_change:.2f}%" if stock.price_change else "Change: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in etf_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def earnings_premarket_screener() -> List[TextContent]:
    """
    Screen stocks rising on pre-market earnings announcements (fixed conditions)
    
    Fixed filter conditions (cannot be changed):
    f=cap_smallover,earningsdate_todaybefore,sh_avgvol_o100,sh_price_o10,ta_change_u2&ft=4&o=-change
    
    - Market cap: small or above ($300M+)
    - Earnings: today before market open
    - Average volume: 100K+
    - Stock price: $10 or more
    - Price change: +2% or more
    - Stocks only
    - Sorted by price change descending
    
    No parameters - all conditions are fixed
    """
    try:
        # Run with fixed parameters
        results = finviz_screener.earnings_premarket_screener()
        
        if not results:
            return [TextContent(type="text", text="No stocks found matching the fixed premarket earnings criteria.")]
        
        # Display fixed conditions
        fixed_conditions = [
            "Fixed Filter Criteria:",
            "- Market Cap: Small+ ($300M+)",
            "- Earnings: Today premarket",
            "- Avg Volume: 100K+",
            "- Price: $10+",
            "- Price Change: 2%+ up",
            "- Stocks only",
            "- Sorted by price change desc"
        ]
        
        # Use detailed format output (fixed parameters)
        params = {'earnings_timing': 'today_before', 'market_cap': 'smallover'}
        formatted_output = _format_earnings_premarket_list(results, params)
        
        return [TextContent(type="text", text="\n".join(fixed_conditions + [""] + formatted_output))]
        
    except Exception as e:
        logger.error(f"Error in earnings_premarket_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def earnings_afterhours_screener() -> List[TextContent]:
    """
    Screen stocks rising in after-hours trading on post-market earnings announcements (fixed conditions)
    
    Fixed filter conditions (cannot be changed):
    f=ah_change_u2,cap_smallover,earningsdate_todayafter,sh_avgvol_o100,sh_price_o10&ft=4&o=-afterchange&ar=60
    
    - After-hours change: +2% or more
    - Market cap: small or above ($300M+)
    - Earnings: today after market close
    - Average volume: 100K+
    - Stock price: $10 or more
    - Stocks only
    - After-hours change sorted descending
    - Maximum results: 60
    
    No parameters - all conditions are fixed
    """
    try:
        # Run with fixed parameters
        results = finviz_screener.earnings_afterhours_screener()
        
        if not results:
            return [TextContent(type="text", text="No stocks found matching the fixed afterhours earnings criteria.")]
        
        # Display fixed conditions
        fixed_conditions = [
            "Fixed Filter Criteria:",
            "- After-hours Change: 2%+ up",
            "- Market Cap: Small+ ($300M+)",
            "- Earnings: Today after hours",
            "- Avg Volume: 100K+",
            "- Price: $10+",
            "- Stocks only",
            "- Sorted by after-hours change desc",
            "- Max results: 60"
        ]
        
        # Use detailed format output (fixed parameters)
        params = {'earnings_timing': 'today_after', 'market_cap': 'smallover'}
        formatted_output = _format_earnings_afterhours_list(results, params)
        
        return [TextContent(type="text", text="\n".join(fixed_conditions + [""] + formatted_output))]
        
    except Exception as e:
        logger.error(f"Error in earnings_afterhours_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def earnings_trading_screener() -> List[TextContent]:
    """
    Screen earnings trade target stocks (fixed conditions)
    
    Fixed filter conditions (cannot be changed):
    f=cap_smallover,earningsdate_yesterdayafter|todaybefore,fa_epsrev_ep,sh_avgvol_o200,sh_price_o10,ta_change_u,ta_perf_0to-4w,ta_volatility_1tox&ft=4&o=-epssurprise&ar=60

    - Market cap: small or above ($300M+)
    - Earnings: yesterday after close or today before open
    - EPS estimate: upward revision
    - Average volume: 200,000+
    - Stock price: $10 or more
    - Price trend: uptrend
    - 4-week performance: monthly positive (Month Above 0%)
    - Volatility: 1x or more
    - Stocks only
    - EPS surprise sorted descending
    - Maximum results: 60
    
    No parameters - all conditions are fixed
    """
    try:
        # Run with fixed conditions (no parameters)
        results = finviz_screener.earnings_trading_screener()
        
        if not results:
            return [TextContent(type="text", text="No stocks found matching the specified earnings trading criteria.")]
        
        # Display fixed conditions
        fixed_conditions = [
            "Fixed Filter Criteria:",
            "- Market Cap: Small+ ($300M+)",
            "- Earnings: Yesterday after hours or today premarket",
            "- EPS Forecast: Upward revision",
            "- Avg Volume: 200,000+",
            "- Price: $10+",
            "- Price Trend: Upward",
            "- 4W Performance: 0% to down (recovery candidate)",
            "- Volatility: 1x+",
            "- Stocks only",
            "- Sorted by EPS surprise desc",
            "- Max results: 60"
        ]
        
        # Concise output format (tickers only)
        output_lines = [
            f"Earnings Trading Screening Results ({len(results)} stocks found):",
            "=" * 60,
            ""
        ] + fixed_conditions + ["", "Detected Tickers:", "-" * 40, ""]
        
        # Display tickers 10 per line
        tickers = [stock.ticker for stock in results]
        for i in range(0, len(tickers), 10):
            line_tickers = tickers[i:i+10]
            output_lines.append(" | ".join(line_tickers))
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in earnings_trading_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]



@server.tool()
def get_stock_news(
    tickers: Union[str, List[str]],
    days_back: int = 7,
    news_type: Optional[str] = "all"
) -> List[TextContent]:
    """
    Get stock-related news
    
    Args:
        tickers: Stock tickers (single string, comma-separated string, or list)
        days_back: Number of days back for news
        news_type: News type (all, earnings, analyst, insider, general)
    """
    try:
        from .utils.validators import validate_tickers, parse_tickers
        
        # Validate tickers
        if not validate_tickers(tickers):
            raise ValueError(f"Invalid tickers: {tickers}")
        
        # Validate days_back
        if days_back <= 0:
            raise ValueError(f"Invalid days_back: {days_back}")
        
        # Parse tickers for display
        ticker_list = parse_tickers(tickers)
        ticker_display = ', '.join(ticker_list)
        
        # Get news data
        news_list = finviz_news.get_stock_news(tickers, days_back or 7, news_type or "all")
        
        if not news_list:
            return [TextContent(type="text", text=f"No news found for {ticker_display} in the last {days_back} days.")]
        
        # Format output
        if len(ticker_list) == 1:
            header = f"News for {ticker_display} (last {days_back} days):"
        else:
            header = f"News for {ticker_display} (last {days_back} days):"
        
        output_lines = [
            header,
            "=" * 50,
            ""
        ]
        
        for news in news_list:
            output_lines.extend([
                f"📰 {news.title}",
                f"🏢 Source: {news.source}",
                f"📅 Date: {news.date.strftime('%Y-%m-%d %H:%M')}",
                f"🏷️ Category: {news.category}",
                f"🔗 URL: {news.url}",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_stock_news: {str(e)}")
        raise e  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Error in get_stock_news: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_market_news(
    days_back: int = 3,
    max_items: int = 20
) -> List[TextContent]:
    """
    Get market-wide news
    
    Args:
        days_back: Number of days back for news
        max_items: Maximum number of items
    """
    try:
        # Get market news
        news_list = finviz_news.get_market_news(days_back or 3, max_items or 20)
        
        if not news_list:
            return [TextContent(type="text", text=f"No market news found in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"Market News (last {days_back} days):",
            "=" * 50,
            ""
        ]
        
        for news in news_list:
            output_lines.extend([
                f"📰 {news.title}",
                f"🏢 Source: {news.source}",
                f"📅 Date: {news.date.strftime('%Y-%m-%d %H:%M')}",
                f"🏷️ Category: {news.category}",
                f"🔗 URL: {news.url}",
                "-" * 30,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_market_news: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_sector_news(
    sector: str,
    days_back: int = 5,
    max_items: int = 15
) -> List[TextContent]:
    """
    Get news for a specific sector
    
    Args:
        sector: Sector name
        days_back: Number of days back for news
        max_items: Maximum number of items
    """
    try:
        # Get sector news
        news_list = finviz_news.get_sector_news(sector, days_back or 5, max_items or 15)
        
        if not news_list:
            return [TextContent(type="text", text=f"No news found for {sector} sector in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"{sector} Sector News (last {days_back} days):",
            "=" * 50,
            ""
        ]
        
        for news in news_list:
            output_lines.extend([
                f"📰 {news.title}",
                f"🏢 Source: {news.source}",
                f"📅 Date: {news.date.strftime('%Y-%m-%d %H:%M')}",
                f"🏷️ Category: {news.category}",
                f"🔗 URL: {news.url}",
                "-" * 30,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_sector_news: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_sector_performance(
    sectors: Optional[List[str]] = None
) -> List[TextContent]:
    """
    Sector performance analysis
    
    Args:
        sectors: Target sectors
    """
    try:
        # Get sector performance data
        sector_data = finviz_sector.get_sector_performance(sectors)
        
        if not sector_data:
            return [TextContent(type="text", text="No sector performance data found.")]
        
        # Format output
        output_lines = [
            "Sector Performance Analysis:",
            "=" * 60,
            ""
        ]
        
        # Adjust header row to match actual column data
        output_lines.extend([
            f"{'Sector':<30} {'Market Cap':<15} {'P/E':<8} {'Div Yield':<10} {'Change':<8} {'Stocks':<6}",
            "-" * 75
        ])
        
        # Data rows
        for sector in sector_data:
            output_lines.append(
                f"{sector.get('name', 'N/A'):<30} "
                f"{sector.get('market_cap', 'N/A'):<15} "
                f"{sector.get('pe_ratio', 'N/A'):<8} "
                f"{sector.get('dividend_yield', 'N/A'):<10} "
                f"{sector.get('change', 'N/A'):<8} "
                f"{sector.get('stocks', 'N/A'):<6}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_sector_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_industry_performance(
    industries: Optional[List[str]] = None
) -> List[TextContent]:
    """
    Industry performance analysis
    
    Args:
        industries: Target industries
    """
    try:
        # Get industry performance data
        industry_data = finviz_sector.get_industry_performance(industries)
        
        if not industry_data:
            return [TextContent(type="text", text="No industry performance data found.")]
        
        # Format output
        output_lines = [
            "Industry Performance Analysis:",
            "=" * 60,
            ""
        ]
        
        # Header row
        output_lines.extend([
            f"{'Industry':<40} {'Market Cap':<15} {'P/E':<8} {'Change':<8} {'Stocks':<6}",
            "-" * 80
        ])
        
        # Data rows
        for industry in industry_data:
            output_lines.append(
                f"{industry.get('industry', 'N/A'):<40} "
                f"{industry.get('market_cap', 'N/A'):<15} "
                f"{industry.get('pe_ratio', 'N/A'):<8} "
                f"{industry.get('change', 'N/A'):<8} "
                f"{industry.get('stocks', 'N/A'):<6}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_industry_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_country_performance(
    countries: Optional[List[str]] = None
) -> List[TextContent]:
    """
    Country market performance analysis
    
    Args:
        countries: Target countries
    """
    try:
        # Get country performance data
        country_data = finviz_sector.get_country_performance(countries)
        
        if not country_data:
            return [TextContent(type="text", text="No country performance data found.")]
        
        # Format output
        output_lines = [
            "Country Performance Analysis:",
            "=" * 60,
            ""
        ]
        
        # Header row
        output_lines.extend([
            f"{'Country':<30} {'Market Cap':<15} {'P/E':<8} {'Change':<8} {'Stocks':<6}",
            "-" * 70
        ])
        
        # Data rows
        for country in country_data:
            output_lines.append(
                f"{country.get('country', 'N/A'):<30} "
                f"{country.get('market_cap', 'N/A'):<15} "
                f"{country.get('pe_ratio', 'N/A'):<8} "
                f"{country.get('change', 'N/A'):<8} "
                f"{country.get('stocks', 'N/A'):<6}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_country_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_sector_specific_industry_performance(
    sector: str
) -> List[TextContent]:
    """
    Industry performance analysis within a specific sector
    
    Available sectors:
    - basicmaterials (Basic Materials)
    - communicationservices (Communication Services) 
    - consumercyclical (Consumer Cyclical)
    - consumerdefensive (Consumer Defensive)
    - energy (Energy)
    - financial (Financial)
    - healthcare (Healthcare)
    - industrials (Industrials)
    - realestate (Real Estate)
    - technology (Technology)
    - utilities (Utilities)
    
    Args:
        sector: Sector name (choose from the sector names above)
        timeframe: Analysis period (1d, 1w, 1m, 3m, 6m, 1y)
    """
    try:
        # Get sector-specific industry performance data
        industry_data = finviz_sector.get_sector_specific_industry_performance(sector)
        
        if not industry_data:
            return [TextContent(type="text", text=f"No industry performance data found for {sector} sector.")]
        
        # Format output
        sector_display = sector.replace('_', ' ').title()
        output_lines = [
            f"{sector_display} Sector - Industry Performance Analysis:",
            "=" * 70,
            ""
        ]
        
        # Header row
        output_lines.extend([
            f"{'Industry':<45} {'Market Cap':<15} {'P/E':<8} {'Change':<8} {'Stocks':<6}",
            "-" * 85
        ])
        
        # Data rows
        for industry in industry_data:
            output_lines.append(
                f"{industry.get('industry', 'N/A'):<45} "
                f"{industry.get('market_cap', 'N/A'):<15} "
                f"{industry.get('pe_ratio', 'N/A'):<8} "
                f"{industry.get('change', 'N/A'):<8} "
                f"{industry.get('stocks', 'N/A'):<6}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_sector_specific_industry_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_capitalization_performance() -> List[TextContent]:
    """
    Market cap performance analysis
    """
    try:
        # Get capitalization performance data
        cap_data = finviz_sector.get_capitalization_performance()
        
        if not cap_data:
            return [TextContent(type="text", text="No capitalization performance data found.")]
        
        # Format output
        output_lines = [
            "Capitalization Performance Analysis:",
            "=" * 70,
            ""
        ]
        
        # Header row
        output_lines.extend([
            f"{'Capitalization':<30} {'Market Cap':<15} {'P/E':<8} {'Change':<8} {'Stocks':<6}",
            "-" * 70
        ])
        
        # Data rows
        for cap in cap_data:
            output_lines.append(
                f"{cap.get('capitalization', 'N/A'):<30} "
                f"{cap.get('market_cap', 'N/A'):<15} "
                f"{cap.get('pe_ratio', 'N/A'):<8} "
                f"{cap.get('change', 'N/A'):<8} "
                f"{cap.get('stocks', 'N/A'):<6}"
            )
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_capitalization_performance: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_market_overview() -> List[TextContent]:
    """
    Get overall market overview (actual data)
    """
    try:
        import pandas as pd
        
        logger.info("Retrieving real market overview data...")
        
        # Major ETF tickers (matching user-provided data)
        major_etfs = ['SPY', 'QQQ', 'DIA', 'IWM', 'TLT', 'GLD']
        
        # 1. Bulk fetch actual data for major ETFs (using actual Finviz field names)
        logger.info("Fetching major ETF data using Finviz bulk API...")
        try:
            # Corresponds to actual Finviz response fields
            etf_data_bulk = finviz_client.get_multiple_stocks_fundamentals(
                major_etfs,
                data_fields=['ticker', 'company', 'price', 'change', 'volume', 'market_cap']
            )
            logger.info(f"Successfully retrieved data for {len(etf_data_bulk)} ETFs")
        except Exception as e:
            logger.warning(f"Bulk API failed: {e}, trying individual requests...")
            # Fallback: individual fetch
            etf_data_bulk = []
            for ticker in major_etfs:
                try:
                    data = finviz_client.get_stock_fundamentals(
                        ticker, 
                        data_fields=['ticker', 'company', 'price', 'change', 'volume', 'market_cap']
                    )
                    etf_data_bulk.append(data)
                except Exception as etf_error:
                    logger.warning(f"Failed to get data for {ticker}: {etf_error}")
                    etf_data_bulk.append({'ticker': ticker, 'error': str(etf_error)})
        
        # 2. Fetch market statistics in parallel
        logger.info("Calculating market statistics...")
        
        # Get volume surge stock count
        try:
            volume_surge_results = finviz_screener.volume_surge_screener()
            volume_surge_count = len(volume_surge_results) if volume_surge_results else 0
            # Statistical calculation
            if volume_surge_results:
                avg_rel_vol = sum([getattr(stock, 'relative_volume', 0) for stock in volume_surge_results if hasattr(stock, 'relative_volume') and stock.relative_volume]) / len(volume_surge_results)
                avg_change = sum([getattr(stock, 'price_change', 0) for stock in volume_surge_results if hasattr(stock, 'price_change') and stock.price_change]) / len(volume_surge_results)
            else:
                avg_rel_vol = 0
                avg_change = 0
        except Exception as e:
            logger.warning(f"Volume surge calculation failed: {e}")
            volume_surge_count = 0
            avg_rel_vol = 0
            avg_change = 0
        
        # Get uptrend stock count
        try:
            uptrend_results = finviz_screener.uptrend_screener()
            uptrend_count = len(uptrend_results) if uptrend_results else 0
            # Sector analysis
            if uptrend_results:
                sectors_count = {}
                for stock in uptrend_results:
                    sector = getattr(stock, 'sector', None)
                    if sector:
                        sectors_count[sector] = sectors_count.get(sector, 0) + 1
                top_sectors = dict(sorted(sectors_count.items(), key=lambda x: x[1], reverse=True)[:3])
            else:
                top_sectors = {}
        except Exception as e:
            logger.warning(f"Uptrend calculation failed: {e}")
            uptrend_count = 0
            top_sectors = {}
        
        # Earnings related statistics
        try:
            earnings_results = finviz_screener.earnings_screener(earnings_date="this_week")
            earnings_count = len(earnings_results) if earnings_results else 0
        except Exception as e:
            logger.warning(f"Earnings calculation failed: {e}")
            earnings_count = 0
        
        # ETF name mapping (matching actual Finviz)
        etf_names = {
            'SPY': 'SPDR S&P 500 ETF Trust',
            'QQQ': 'Invesco QQQ Trust Series 1',  
            'DIA': 'SPDR Dow Jones Industrial Average ETF',
            'IWM': 'iShares Russell 2000 ETF',
            'TLT': 'iShares 20+ Year Treasury Bond ETF',
            'GLD': 'SPDR Gold Shares ETF'
        }
        
        # Output format
        output_lines = [
            "🏛️ Real-time Market Overview",
            "=" * 70,
            f"📅 Data Retrieved: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"📊 Data Source: Finviz.com (Live Data)",
            "",
            "📈 Major ETF Price Data:",
            "-" * 50
        ]
        
        # Convert ETF data to dictionary (using ticker as key)
        etf_data_dict = {}
        
        # Convert bulk fetch data to ticker-based dictionary
        if isinstance(etf_data_bulk, list):
            for data_item in etf_data_bulk:
                if isinstance(data_item, dict):
                    ticker_key = data_item.get('ticker')
                    if ticker_key:
                        etf_data_dict[ticker_key] = data_item
                else:
                    # Object format
                    if hasattr(data_item, 'ticker'):
                        ticker_key = getattr(data_item, 'ticker')
                        if ticker_key:
                            etf_data_dict[ticker_key] = {
                                'ticker': getattr(data_item, 'ticker', ''),
                                'company': getattr(data_item, 'company', ''),
                                'price': getattr(data_item, 'price', None),
                                'change': getattr(data_item, 'change', None),
                                'volume': getattr(data_item, 'volume', None),
                                'market_cap': getattr(data_item, 'market_cap', None)
                            }
        
        logger.info(f"Converted {len(etf_data_dict)} ETF records to dictionary")
        
        # Display ETF data (search by ticker)
        for ticker in major_etfs:
            try:
                # Get ticker-corresponding data from dictionary
                etf_data = etf_data_dict.get(ticker)
                
                if etf_data and not etf_data.get('error'):
                    name = etf_names.get(ticker, ticker)
                    
                    # Safely retrieve data
                    def get_safe_data(key, default='N/A'):
                        value = etf_data.get(key, default)
                        return value if value is not None else default
                    
                    price = get_safe_data('price')
                    change = get_safe_data('change')
                    volume = get_safe_data('volume')
                    market_cap = get_safe_data('market_cap')
                    
                    # Format processing
                    if isinstance(price, (int, float)):
                        price_str = f"${price:.2f}"
                    else:
                        price_str = str(price)
                    
                    # Process change rate (use as-is from Finviz)
                    if isinstance(change, str) and '%' in change:
                        change_str = change  # Already includes % sign
                    elif isinstance(change, (int, float)):
                        change_str = f"{change:+.2f}%"
                    else:
                        change_str = str(change)
                    
                    # Format volume
                    if isinstance(volume, (int, float)):
                        volume_str = f"{int(volume):,}"
                    else:
                        volume_str = str(volume)
                    
                    # Format market cap  
                    market_cap_str = str(market_cap) if market_cap != 'N/A' else 'N/A'
                    
                    # Direction emoji
                    trend_emoji = "📈" if change_str.startswith('+') else "📉" if change_str.startswith('-') else "📊"
                    
                    output_lines.extend([
                        f"🔹 {ticker} ({name})",
                        f"   💰 Price: {price_str}  {trend_emoji} Change: {change_str}",
                        f"   📦 Volume: {volume_str}  💼 Market Cap: {market_cap_str}",
                        ""
                    ])
                else:
                    # If data cannot be retrieved, try individual fetch
                    logger.warning(f"No data found for {ticker} in bulk result, trying individual fetch...")
                    try:
                        individual_data = finviz_client.get_stock_fundamentals(
                            ticker, 
                            data_fields=['ticker', 'company', 'price', 'change', 'volume', 'market_cap']
                        )
                        if individual_data:
                            # Process individual fetch data
                            if hasattr(individual_data, 'ticker'):
                                etf_data = {
                                    'ticker': getattr(individual_data, 'ticker', ticker),
                                    'company': getattr(individual_data, 'company', ''),
                                    'price': getattr(individual_data, 'price', None),
                                    'change': getattr(individual_data, 'change', None),
                                    'volume': getattr(individual_data, 'volume', None),
                                    'market_cap': getattr(individual_data, 'market_cap', None)
                                }
                                logger.info(f"Successfully retrieved individual data for {ticker}")
                            else:
                                etf_data = individual_data
                        else:
                            etf_data = None
                    except Exception as individual_error:
                        logger.warning(f"Individual fetch also failed for {ticker}: {individual_error}")
                        etf_data = None
                    
                    # If individual fetch succeeds, display data
                    if etf_data and not etf_data.get('error'):
                        name = etf_names.get(ticker, ticker)
                        
                        # Safely retrieve data (individual fetch version)
                        def get_safe_data_individual(key, default='N/A'):
                            value = etf_data.get(key, default)
                            return value if value is not None else default
                        
                        price = get_safe_data_individual('price')
                        change = get_safe_data_individual('change')
                        volume = get_safe_data_individual('volume')
                        market_cap = get_safe_data_individual('market_cap')
                        
                        # Format processing
                        if isinstance(price, (int, float)):
                            price_str = f"${price:.2f}"
                        else:
                            price_str = str(price)
                        
                        # Process change rate
                        if isinstance(change, str) and '%' in change:
                            change_str = change
                        elif isinstance(change, (int, float)):
                            change_str = f"{change:+.2f}%"
                        else:
                            change_str = str(change)
                        
                        # Format volume
                        if isinstance(volume, (int, float)):
                            volume_str = f"{int(volume):,}"
                        else:
                            volume_str = str(volume)
                        
                        # Format market cap  
                        market_cap_str = str(market_cap) if market_cap != 'N/A' else 'N/A'
                        
                        # Direction emoji
                        trend_emoji = "📈" if change_str.startswith('+') else "📉" if change_str.startswith('-') else "📊"
                        
                        output_lines.extend([
                            f"🔹 {ticker} ({name}) [individual fetch]",
                            f"   💰 Price: {price_str}  {trend_emoji} Change: {change_str}",
                            f"   📦 Volume: {volume_str}  💼 Market Cap: {market_cap_str}",
                            ""
                        ])
                    else:
                        # If all retrieval methods fail
                        name = etf_names.get(ticker, ticker)
                        error_msg = etf_data.get('error', 'No data') if etf_data else 'No data'
                        output_lines.extend([
                            f"🔹 {ticker} ({name})",
                            f"   ⚠️ Data fetch error: {error_msg}",
                            ""
                        ])
                    
            except Exception as e:
                logger.warning(f"Failed to process data for {ticker}: {e}")
                output_lines.extend([
                    f"🔹 {ticker} ({etf_names.get(ticker, ticker)})",
                    f"   ⚠️ Data processing error: {str(e)[:30]}...",
                    ""
                ])
        
        # Display market statistics
        output_lines.extend([
            "📊 Market Activity Statistics:",
            "-" * 50,
            f"🔥 Volume Surge Stocks: {volume_surge_count} stocks",
            f"📈 Uptrend Stocks: {uptrend_count} stocks", 
            f"📋 Earnings This Week: {earnings_count} stocks",
            ""
        ])
        
        # Volume surge stocks detailed statistics
        if volume_surge_count > 0:
            output_lines.extend([
                "🔥 Volume Surge Details:",
                f"   📊 Avg Relative Volume: {avg_rel_vol:.1f}x",
                f"   📈 Avg Price Change: +{avg_change:.1f}%",
                ""
            ])
        
        # Major uptrend sectors
        if top_sectors:
            output_lines.extend([
                "📈 Uptrend Major Sectors:",
            ])
            for sector, count in top_sectors.items():
                output_lines.append(f"   🏢 {sector}: {count} stocks")
            output_lines.append("")
        
        output_lines.extend([
            "=" * 70,
            "💡 For detailed analysis, please use the following features:",
            "🔍 get_stock_fundamentals - Individual Stock Detailed Data",
            "🔥 volume_surge_screener - Volume Surge Stock Details",
            "📈 uptrend_screener - Uptrend Stock Details",
            "🏢 get_sector_performance - Sector performance analysis",
            "",
            f"🌐 Data Source: Finviz Elite (https://elite.finviz.com/)",
            f"⏰ Last updated: {pd.Timestamp.now().strftime('%H:%M:%S')}"
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_market_overview: {str(e)}")
        return [TextContent(type="text", text=f"❌ Failed to retrieve market overview: {str(e)}")]

@server.tool()
def get_relative_volume_stocks(
    min_relative_volume: Any,
    min_price: Optional[Union[int, float, str]] = None,
    sectors: Optional[List[str]] = None,
    max_results: int = 50
) -> List[TextContent]:
    """
    Detect stocks with abnormal relative volume
    
    Args:
        min_relative_volume: Minimum relative volume
        min_price: Minimum stock price
        sectors: Target sectors
        max_results: Maximum number of results
    """
    try:
        # Build screening parameters
        params = {
            'min_relative_volume': min_relative_volume,
            'min_price': min_price,
            'sectors': sectors or [],
            'max_results': max_results or 50
        }
        
        # Use volume surge screener as the base
        results = finviz_screener.screen_stocks({
            'relative_volume_min': min_relative_volume,
            'price_min': min_price,
            'sectors': sectors or []
        })
        
        # Sort by relative volume
        results.sort(key=lambda x: x.relative_volume or 0, reverse=True)
        results = results[:max_results or 50]
        
        if not results:
            return [TextContent(type="text", text=f"No stocks found with relative volume >= {min_relative_volume}x.")]
        
        # Format output
        output_lines = [
            f"High Relative Volume Stocks (>= {min_relative_volume}x):",
            "=" * 60,
            ""
        ]
        
        # Header row
        output_lines.extend([
            f"{'Ticker':<8} {'Company':<25} {'Price':<8} {'Change%':<8} {'Volume':<12} {'Rel Vol':<8}",
            "-" * 70
        ])
        
        # Data rows
        for stock in results:
            company_short = (stock.company_name[:22] + "...") if stock.company_name and len(stock.company_name) > 25 else (stock.company_name or "N/A")
            
            output_lines.append(
                f"{stock.ticker:<8} "
                f"{company_short:<25} "
                f"${stock.price:<7.2f} " if stock.price else f"{'N/A':<8} "
                f"{stock.price_change:>7.2f}% " if stock.price_change else f"{'N/A':<8} "
                f"{stock.volume:>11,} " if stock.volume else f"{'N/A':<12} "
                f"{stock.relative_volume:>7.2f}x" if stock.relative_volume else f"{'N/A':<8}"
            )
        
        output_lines.extend([
            "",
            f"Found {len(results)} stocks with unusual volume activity."
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in get_relative_volume_stocks: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def technical_analysis_screener(
    rsi_min: Optional[Union[int, float, str]] = None,
    rsi_max: Optional[Union[int, float, str]] = None,
    price_vs_sma20: Optional[str] = None,
    price_vs_sma50: Optional[str] = None,
    price_vs_sma200: Optional[str] = None,
    min_price: Optional[Union[int, float, str]] = None,
    min_volume: Optional[Union[int, float]] = None,
    sectors: Optional[List[str]] = None,
    max_results: int = 50
) -> List[TextContent]:
    """
    Technical analysis-based screening
    
    Args:
        rsi_min: Minimum RSI value
        rsi_max: Maximum RSI value
        price_vs_sma20: Relationship with 20-day moving average (above, below)
        price_vs_sma50: Relationship with 50-day moving average (above, below)
        price_vs_sma200: Relationship with 200-day moving average (above, below)
        min_price: Minimum stock price
        min_volume: Minimum volume
        sectors: Target sectors
        max_results: Maximum number of results
    """
    try:
        # Build screening parameters
        filters = {}
        
        if rsi_min is not None:
            filters['rsi_min'] = rsi_min
        if rsi_max is not None:
            filters['rsi_max'] = rsi_max
        if price_vs_sma20 == "above":
            filters['sma20_above'] = True
        elif price_vs_sma20 == "below":
            filters['sma20_below'] = True
        if price_vs_sma50 == "above":
            filters['sma50_above'] = True
        elif price_vs_sma50 == "below":
            filters['sma50_below'] = True
        if price_vs_sma200 == "above":
            filters['sma200_above'] = True
        elif price_vs_sma200 == "below":
            filters['sma200_below'] = True
        if min_price is not None:
            filters['price_min'] = min_price
        if min_volume is not None:
            filters['volume_min'] = min_volume
        if sectors:
            filters['sectors'] = sectors
        
        results = finviz_screener.screen_stocks(filters)
        results = results[:max_results or 50]
        
        if not results:
            return [TextContent(type="text", text="No stocks found matching technical criteria.")]
        
        # Format output
        criteria_text = []
        if rsi_min is not None and rsi_max is not None:
            criteria_text.append(f"RSI: {rsi_min}-{rsi_max}")
        elif rsi_min is not None:
            criteria_text.append(f"RSI >= {rsi_min}")
        elif rsi_max is not None:
            criteria_text.append(f"RSI <= {rsi_max}")
        
        if price_vs_sma20:
            criteria_text.append(f"Price {price_vs_sma20} SMA20")
        if price_vs_sma50:
            criteria_text.append(f"Price {price_vs_sma50} SMA50")
        if price_vs_sma200:
            criteria_text.append(f"Price {price_vs_sma200} SMA200")
        
        output_lines = [
            f"Technical Analysis Screening Results:",
            f"Criteria: {', '.join(criteria_text) if criteria_text else 'All stocks'}",
            "=" * 60,
            ""
        ]
        
        for stock in results:
            output_lines.extend([
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A",
                f"RSI: {stock.rsi:.2f}" if stock.rsi else "RSI: N/A",
                f"SMA 20: ${stock.sma_20:.2f}" if stock.sma_20 else "SMA 20: N/A",
                f"SMA 50: ${stock.sma_50:.2f}" if stock.sma_50 else "SMA 50: N/A",
                f"SMA 200: ${stock.sma_200:.2f}" if stock.sma_200 else "SMA 200: N/A",
                f"Volume: {stock.volume:,}" if stock.volume else "Volume: N/A",
                "-" * 40,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in technical_analysis_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

def cli_main():
    """CLI entry point - supports stdio (default) and sse transport for Docker"""
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport in ("sse", "streamable-http"):
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))
        logger.info(f"Starting MCP server with {transport} transport on {host}:{port}")
        server.run(transport=transport, host=host, port=port)
    else:
        server.run()

@server.tool()
def earnings_winners_screener(
    earnings_period: Optional[str] = "this_week",
    market_cap: Optional[str] = "smallover",
    min_price: Optional[Union[int, float, str]] = 10.0,
    min_avg_volume: Optional[str] = "o500",
    min_eps_growth_qoq: Optional[float] = 10.0,
    min_eps_revision: Optional[float] = 5.0,
    min_sales_growth_qoq: Optional[float] = 5.0,
    min_weekly_performance: Optional[str] = "5to-1w",
    sma200_filter: Optional[bool] = True,
    target_sectors: Optional[List[str]] = None,
    max_results: int = 50,
    sort_by: Optional[str] = "performance_1w",
    sort_order: Optional[str] = "desc"
) -> List[TextContent]:
    """
    Screen earnings winner stocks - detailed list including weekly performance, EPS surprise, and revenue surprise
    
    Search for stocks that rose after earnings using the same conditions as Finviz URL and display detailed data in table format.
    Retrieved data includes:
    - Weekly performance (Performance Week)
    - EPS surprise (EPS Surprise)
    - Revenue surprise (Revenue Surprise)
    - EPS QoQ growth rate (EPS QoQ Growth)
    - Sales QoQ growth rate (Sales QoQ Growth)
    - Basic stock price and volume data
    
    Args:
        earnings_period: Earnings period ('this_week', 'yesterday', 'today', 'custom')
        market_cap: Market cap filter ('small', 'mid', 'large', 'mega', 'smallover')
        min_price: Minimum stock price (default: $10)
        min_avg_volume: Minimum average volume (numeric or string format, default: "o500" = 500,000+)
        min_eps_growth_qoq: Minimum EPS QoQ growth rate (%) (default: 10%)
        min_eps_revision: Minimum EPS revision rate (%) (default: 5%)
        min_sales_growth_qoq: Minimum sales QoQ growth rate (%) (default: 5%)
        min_weekly_performance: Weekly performance filter (default: 5to-1w)
        sma200_filter: Filter for above 200-day moving average (default: True)
        target_sectors: Target sectors (default: top 6 sectors)
        max_results: Maximum number of results (default: 50)
        sort_by: Sort criteria ('performance_1w', 'eps_growth_qoq', 'eps_surprise', 'price_change', 'volume')
        sort_order: Sort order ('asc', 'desc')
    
    Returns:
        Detailed list of earnings winner stocks (table format + analysis data + Finviz URL)
        - Main table: Ticker | Company | Sector | Price | Weekly Perf | EPS Surprise | Rev Surprise | Earnings Date
        - Detailed analysis of top 5 stocks
        - EPS surprise statistics
        - Sector performance analysis
        - Source data Finviz URL (CSV export format)
    """
    try:
        # Prepare parameters
        params = {
            'earnings_period': earnings_period,
            'market_cap': market_cap,
            'min_price': min_price,
            'min_avg_volume': min_avg_volume,
            'min_eps_growth_qoq': min_eps_growth_qoq,
            'min_eps_revision': min_eps_revision,
            'min_sales_growth_qoq': min_sales_growth_qoq,
            'min_weekly_performance': min_weekly_performance,
            'sma200_filter': sma200_filter,
            'max_results': max_results,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        
        # Sector settings
        if target_sectors:
            params['target_sectors'] = target_sectors
        else:
            params['target_sectors'] = [
                "Technology", "Industrials", "Healthcare", 
                "Communication Services", "Consumer Cyclical", "Financial Services"
            ]
        
        # Set earnings_date parameter
        if earnings_period == 'this_week':
            params['earnings_date'] = 'thisweek'
        elif earnings_period == 'yesterday':
            params['earnings_date'] = 'yesterday'
        elif earnings_period == 'today':
            params['earnings_date'] = 'today'
        else:
            params['earnings_date'] = 'thisweek'  # Default
        
        logger.info(f"Executing earnings winners screening with params: {params}")
        
        # Run screening
        try:
            results = finviz_screener.earnings_winners_screener(**params)
        except Exception as e:
            logger.warning(f"earnings_winners_screener failed, trying earnings_screener: {e}")
            # Fallback: use earnings_screener method
            fallback_params = {
                'earnings_date': params.get('earnings_date', 'thisweek'),
                'market_cap': params.get('market_cap', 'smallover'),
                'min_price': params.get('min_price'),
                'sectors': params.get('target_sectors')
            }
            fallback_params = {k: v for k, v in fallback_params.items() if v is not None}
            results = finviz_screener.earnings_screener(**fallback_params)
        
        if not results:
            return [TextContent(type="text", text="No earnings winners found matching the criteria.")]
        
        # Display results
        output_lines = _format_earnings_winners_list(results, params)
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in earnings_winners_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def upcoming_earnings_screener(
    earnings_period: Optional[str] = "next_week",
    market_cap: Optional[str] = "smallover",
    min_price: Optional[Union[int, float, str]] = 10,
    min_avg_volume: Optional[str] = "o500",  # Support both numeric and string values - converts internally
    target_sectors: Optional[List[str]] = None,
    pre_earnings_analysis: Optional[Dict[str, Any]] = None,
    risk_assessment: Optional[Dict[str, Any]] = None,
    data_fields: Optional[List[str]] = None,
    max_results: int = 100,
    sort_by: Optional[str] = "earnings_date",
    sort_order: Optional[str] = "asc",
    include_chart_view: Optional[bool] = True,
    earnings_calendar_format: Optional[bool] = False,
    custom_date_range: Optional[str] = None,  # New feature: custom date range (e.g. "06-30-2025x07-04-2025")
    start_date: Optional[str] = None,  # New feature: start date (YYYY-MM-DD format)
    end_date: Optional[str] = None     # New feature: end date (YYYY-MM-DD format)
) -> List[TextContent]:
    """
    Screen next week's earnings stocks (for earnings trade preparation)
    
    Args:
        earnings_period: Earnings period ('next_week', 'next_2_weeks', 'next_month', 'custom_range')
        market_cap: Market cap filter ('small', 'mid', 'large', 'mega', 'smallover')
        min_price: Minimum stock price
        min_avg_volume: Minimum average volume
        target_sectors: Target sectors (8 sectors)
        pre_earnings_analysis: Pre-earnings analysis settings
        risk_assessment: Risk assessment settings
        data_fields: Data fields to retrieve
        max_results: Maximum number of results
        sort_by: Sort criteria ('earnings_date', 'market_cap', 'target_price_upside', 'volatility', 'earnings_potential_score')
        sort_order: Sort order ('asc', 'desc')
        include_chart_view: Include weekly chart view
        earnings_calendar_format: Output in earnings calendar format
        custom_date_range: Custom date range (Finviz format: "MM-DD-YYYYxMM-DD-YYYY")
        start_date: Start date (YYYY-MM-DD format, used in combination with end_date)
        end_date: End date (YYYY-MM-DD format, used in combination with start_date)
    
    Returns:
        Upcoming Earnings Screener Results
    """
    try:
        # Prepare and normalize parameters
        params = {
            'earnings_period': earnings_period,
            'market_cap': market_cap,
            'min_price': min_price,
            'max_results': max_results,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        
        # Normalize volume parameter - support both numeric and string
        if min_avg_volume is not None:
            if isinstance(min_avg_volume, (int, float)):
                # Use numeric value as-is
                params['avg_volume_min'] = min_avg_volume
            elif isinstance(min_avg_volume, str):
                # Use string as filter value
                params['average_volume'] = min_avg_volume
        
        # Normalize sector - align with parameter names used by upcoming_earnings_screen
        if target_sectors:
            params['target_sectors'] = target_sectors
        else:
            params['target_sectors'] = [
                "Technology", "Industrials", "Healthcare", "Communication Services",
                "Consumer Cyclical", "Financial Services", "Consumer Defensive", "Basic Materials"
            ]
        
        # Set pre-earnings analysis items
        if pre_earnings_analysis:
            params.update(pre_earnings_analysis)
        
        # Set risk assessment items
        if risk_assessment:
            params.update(risk_assessment)
        
        # Ignore data field settings (not needed in new implementation)
        
        # Set earnings_date parameter (by priority order)
        # 1. If custom date range is specified
        if custom_date_range:
            params['earnings_date'] = custom_date_range
        # 2. If both start date and end date are specified
        elif start_date and end_date:
            params['earnings_date'] = {'start': start_date, 'end': end_date}
        # 3. Conventional period specification
        elif earnings_period == 'next_week':
            params['earnings_date'] = 'nextweek'
        elif earnings_period == 'next_2_weeks':
            params['earnings_date'] = 'nextdays5'
        elif earnings_period == 'next_month':
            params['earnings_date'] = 'thismonth'
        else:
            params['earnings_date'] = 'nextweek'  # Default
        
        # Run screening - use new advanced_screen method
        logger.info(f"Executing upcoming earnings screening with params: {params}")
        logger.info(f"Final earnings_date parameter: {params.get('earnings_date')}")
        # Use upcoming_earnings_screen method
        try:
            results = finviz_screener.upcoming_earnings_screener(**params)
        except Exception as e:
            logger.warning(f"upcoming_earnings_screen failed, trying earnings_screen: {e}")
            # Fallback: use earnings_screen method
            fallback_params = {
                'earnings_date': params.get('earnings_date', 'nextweek'),
                'market_cap': params.get('market_cap', 'smallover'),
                'min_price': params.get('min_price'),
                'sectors': params.get('target_sectors')
            }
            # Remove None values
            fallback_params = {k: v for k, v in fallback_params.items() if v is not None}
            results = finviz_screener.earnings_screener(**fallback_params)
        
        if not results:
            return [TextContent(type="text", text="No upcoming earnings stocks found.")]
        
        # Display results
        if earnings_calendar_format:
            output_lines = _format_earnings_calendar(results, include_chart_view)
        else:
            output_lines = _format_upcoming_earnings_list(results, include_chart_view)
        
        # Add note about Finviz CSV limitations
        output_lines.extend([
            "",
            "📋 Note: Finviz CSV export does not include earnings date information in the response,",
            "    even when filtering by earnings date. The stocks above match your earnings date",
            f"    criteria ({earnings_period}) but specific dates are not shown in the CSV data.",
            "    For exact earnings dates, please check the Finviz website directly.",
            "",
            f"🔗 Finviz URL with your filters:",
            f"    {_generate_finviz_url(market_cap, params.get('earnings_date', 'nextweek'))}"
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except Exception as e:
        logger.error(f"Error in upcoming_earnings_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

def _format_earnings_winners_list(results: List, params: Dict[str, Any]) -> List[str]:
    """Format post-earnings rising stocks as a list."""
    
    # Helper function to safely retrieve numeric values
    def safe_float(value, default=0.0):
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def safe_int(value, default=0):
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    # Safely retrieve parameters
    min_price = safe_float(params.get('min_price', 10))
    min_eps_growth = safe_float(params.get('min_eps_growth_qoq', 10))
    min_eps_revision = safe_float(params.get('min_eps_revision', 5))
    min_sales_growth = safe_float(params.get('min_sales_growth_qoq', 5))
    
    output_lines = [
        f"📈 Earnings Winner Stocks List - Weekly Performance and EPS Surprise",
        "",
        f"🎯 Screening Conditions:",
        f"- Earnings announcement period: {params.get('earnings_period', 'this_week')}",
        f"- Market cap: {params.get('market_cap', 'smallover')} ($300M+)", 
        f"- Min stock price: ${min_price:.1f}",
        f"- Min avg volume: {params.get('min_avg_volume', 'o500')}",
        f"- Min EPS QoQ growth: {min_eps_growth:.1f}%+",
        f"- Min EPS estimate revision: {min_eps_revision:.1f}%+",
        f"- Min sales QoQ growth: {min_sales_growth:.1f}%+",
        f"- Above SMA200: {params.get('sma200_filter', True)}",
        "",
        "=" * 120,
        ""
    ]
    
    # Table header
    output_lines.extend([
        "| Ticker | Company                             | Sector          | Price   | Weekly Perf       | EPS Surprise  | Rev Surprise   | Earnings    |",
        "|---------|-------------------------------------|-----------------|---------|-------------------|---------------|---------------|-------------|"
    ])
    
    for stock in results:
        # Organize data
        ticker = stock.ticker or "N/A"
        company = (stock.company_name or "N/A")[:35]  # Limit to 35 chars
        sector = (stock.sector or "N/A")[:15]  # Limit to 15 chars
        price = f"${stock.price:.2f}" if stock.price else "N/A"
        
        # Weekly performance
        weekly_perf = f"+{safe_float(stock.performance_1w):.1f}%" if stock.performance_1w else "N/A"
        
        # EPS surprise
        eps_surprise = f"+{safe_float(stock.eps_surprise):.1f}%" if stock.eps_surprise else "N/A"
        
        # Revenue surprise
        revenue_surprise = f"+{safe_float(stock.revenue_surprise):.1f}%" if stock.revenue_surprise else "N/A"
        
        # Earnings date
        earnings_date = stock.earnings_date or "N/A"
        
        # Create table rows
        row = f"| {ticker:<7} | {company:<35} | {sector:<15} | {price:<7} | {weekly_perf:>17} | {eps_surprise:>13} | {revenue_surprise:>13} | {earnings_date:<11} |"
        output_lines.append(row)
    
    output_lines.extend([
        "",
        "=" * 120,
        "",
        "🎯 Performance Analysis:",
        ""
    ])
    
    # Detailed analysis of top performers
    if results:
        top_performers = sorted([s for s in results if s.performance_1w], 
                               key=lambda x: x.performance_1w, reverse=True)[:5]
        
        output_lines.append("📈 Top 5 Stocks - Weekly Performance:")
        for i, stock in enumerate(top_performers, 1):
            output_lines.extend([
                f"",
                f"🏆 #{i} **{stock.ticker}** - {stock.company_name}",
                f"   📊 Weekly Performance: **+{safe_float(stock.performance_1w):.1f}%**",
                f"   💰 Price: ${safe_float(stock.price):.2f}" if stock.price else "   💰 Price: N/A",
                f"   🎯 EPS Surprise: {safe_float(stock.eps_surprise):.1f}%" if stock.eps_surprise else "   🎯 EPS Surprise: N/A",
                f"   📈 Revenue Surprise: {safe_float(stock.revenue_surprise):.1f}%" if stock.revenue_surprise else "   📈 Revenue Surprise: N/A",
                f"   🏢 Sector: {stock.sector}",
                f"   📅 Earnings Date: {stock.earnings_date}" if stock.earnings_date else "   📅 Earnings Date: N/A"
            ])
            
            # Additional metrics
            metrics = []
            if stock.eps_qoq_growth or stock.eps_growth_qtr:
                eps_growth = safe_float(stock.eps_qoq_growth or stock.eps_growth_qtr)
                metrics.append(f"EPS QoQ: {eps_growth:.1f}%")
            if stock.sales_qoq_growth or stock.sales_growth_qtr:
                sales_growth = safe_float(stock.sales_qoq_growth or stock.sales_growth_qtr)
                metrics.append(f"Sales QoQ: {sales_growth:.1f}%")
            if stock.volume and stock.avg_volume and safe_float(stock.avg_volume) > 0:
                rel_vol = safe_float(stock.volume) / safe_float(stock.avg_volume)
                metrics.append(f"Relative Vol: {rel_vol:.1f}x")
            if stock.pe_ratio:
                metrics.append(f"PER: {safe_float(stock.pe_ratio):.1f}")
                
            if metrics:
                output_lines.append(f"   📋 Financials: {' | '.join(metrics)}")
    
    # Surprise analysis
    surprise_stocks = [s for s in results if s.eps_surprise and safe_float(s.eps_surprise) > 0]
    if surprise_stocks:
        avg_eps_surprise = sum(safe_float(s.eps_surprise) for s in surprise_stocks) / len(surprise_stocks)
        max_eps_surprise = max(safe_float(s.eps_surprise) for s in surprise_stocks)
        
        output_lines.extend([
            "",
            "🎯 EPS Surprise Analysis:",
            f"   • Avg EPS Surprise: {avg_eps_surprise:.1f}%",
            f"   • Max EPS Surprise: {max_eps_surprise:.1f}%",
            f"   • Positive surprise stocks: {len(surprise_stocks)}"
        ])
    
    # Sector analysis
    sector_performance = {}
    for stock in results:
        if stock.sector and stock.performance_1w:
            perf_value = safe_float(stock.performance_1w)
            if perf_value != 0:  # Add only valid values
                if stock.sector not in sector_performance:
                    sector_performance[stock.sector] = []
                sector_performance[stock.sector].append(perf_value)
    
    if sector_performance:
        output_lines.extend([
            "",
            "🏢 Sector Performance:",
        ])
        
        for sector, performances in sector_performance.items():
            avg_perf = sum(performances) / len(performances)
            count = len(performances)
            output_lines.append(f"   • {sector}: avg {avg_perf:.1f}% ({count} stocks)")
    
    # Add Finviz URL
    earnings_date_param = params.get('earnings_date', 'thisweek')
    market_cap_param = params.get('market_cap', 'smallover')
    
    # Get API key from environment variable
    import os
    api_key = os.getenv('FINVIZ_API_KEY', 'YOUR_API_KEY_HERE')
    
    finviz_url = f"https://elite.finviz.com/export.ashx?v=151&f=cap_{market_cap_param},earningsdate_{earnings_date_param},fa_epsqoq_o{safe_int(params.get('min_eps_growth_qoq', 10))},fa_epsrev_eo{safe_int(params.get('min_eps_revision', 5))},fa_salesqoq_o{safe_int(params.get('min_sales_growth_qoq', 5))},sec_technology|industrials|healthcare|communicationservices|consumercyclical|financial,sh_avgvol_{params.get('min_avg_volume', 'o500')},sh_price_o{safe_int(params.get('min_price', 10))},ta_perf_{params.get('min_weekly_performance', '5to-1w')},ta_sma200_pa&ft=4&o=ticker&ar={safe_int(params.get('max_results', 50))}&c=0,1,2,79,3,4,5,6,7,8,9,10,11,12,13,73,74,75,14,15,16,77,17,18,19,20,21,23,22,82,78,127,128,24,25,85,26,27,28,29,30,31,84,32,33,34,35,36,37,38,39,40,41,90,91,92,93,94,95,96,97,98,99,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,80,83,76,60,61,62,63,64,67,89,69,81,86,87,88,65,66,71,72,103,100,101,104,102,106,107,108,109,110,125,126,59,68,70,111,112,113,114,115,116,117,118,119,120,121,122,123,124,105&auth={api_key}"
    
    output_lines.extend([
        "",
        "🔗 Verify same results on Finviz:",
        f"   {finviz_url}",
        "",
        "💡 These stocks recently reported earnings and show strong performance and favorable fundamental indicators.",
        "   Consider for momentum trading or as a target for detailed analysis."
    ])
    
    return output_lines

def _generate_finviz_url(market_cap: str, earnings_date) -> str:
    """Generate Finviz URL."""
    base_url = "https://elite.finviz.com/screener.ashx?v=311&f="
    
    # Market cap filter
    cap_filter = f"cap_{market_cap or 'smallover'}"
    
    # Earnings date filter
    if isinstance(earnings_date, dict):
        # Dictionary format (start/end)
        from .finviz_client.base import FinvizClient
        client = FinvizClient()
        start_formatted = client._format_date_for_finviz(earnings_date['start'])
        end_formatted = client._format_date_for_finviz(earnings_date['end'])
        earnings_filter = f"earningsdate_{start_formatted}x{end_formatted}"
    elif isinstance(earnings_date, str) and 'x' in earnings_date:
        # Date range string case
        earnings_filter = f"earningsdate_{earnings_date}"
    else:
        # For fixed period
        earnings_filter = f"earningsdate_{earnings_date}"
    
    return f"{base_url}{cap_filter},{earnings_filter}"

def _format_upcoming_earnings_list(results: List, include_chart_view: bool = True) -> List[str]:
    """Format next week earnings stocks as a list."""
    output_lines = [
        f"Upcoming Earnings Screening Results ({len(results)} stocks found):",
        "=" * 70,
        ""
    ]
    
    for stock in results:
        output_lines.extend([
            f"📈 {stock.ticker} - {stock.company_name}",
            f"   Sector: {stock.sector} | Industry: {stock.industry}",
            f"   Earnings Date: {stock.earnings_date or 'Not available in CSV'} | Timing: {stock.earnings_timing or 'N/A'}",
            f"   Current Price: ${stock.current_price:.2f}" if stock.current_price else "   Current Price: N/A",
            f"   Market Cap: {format_large_number(stock.market_cap * 1e6)}" if stock.market_cap else "   Market Cap: N/A",
            f"   PE Ratio: {stock.pe_ratio:.2f}" if stock.pe_ratio else "   PE Ratio: N/A",
            f"   Target Price: ${stock.target_price:.2f}" if stock.target_price else "   Target Price: N/A",
            f"   Target Upside: {stock.target_price_upside:.1f}%" if stock.target_price_upside else "   Target Upside: N/A",
            f"   Analyst Recommendation: {stock.analyst_recommendation}" if stock.analyst_recommendation else "   Analyst Recommendation: N/A",
            f"   Volatility: {stock.volatility:.2f}" if stock.volatility else "   Volatility: N/A",
            f"   Short Interest: {stock.short_interest:.1f}%" if stock.short_interest else "   Short Interest: N/A",
            f"   Avg Volume: {format_large_number(stock.avg_volume)}" if stock.avg_volume else "   Avg Volume: N/A",
            ""
        ])
        
        # Additional metrics (if available)
        additional_metrics = []
        if stock.performance_1w is not None:
            additional_metrics.append(f"   • 1W Performance: {stock.performance_1w:.1f}%")
        if stock.performance_1m is not None:
            additional_metrics.append(f"   • 1M Performance: {stock.performance_1m:.1f}%")
        if stock.rsi is not None:
            additional_metrics.append(f"   • RSI: {stock.rsi:.1f}")
        
        if additional_metrics:
            output_lines.extend([
                "   📊 Additional Metrics:",
                *additional_metrics,
                ""
            ])
        
        output_lines.append("-" * 70)
        output_lines.append("")
    
    return output_lines

def _format_earnings_calendar(results: List, include_chart_view: bool = True) -> List[str]:
    """Format next week earnings stocks as a calendar."""
    output_lines = [
        f"📅 Upcoming Earnings Calendar ({len(results)} stocks)",
        "=" * 70,
        ""
    ]
    
    # Group by date
    by_date = {}
    for stock in results:
        date = stock.earnings_date or "Unknown"
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(stock)
    
    # Sort by date
    for date in sorted(by_date.keys()):
        stocks = by_date[date]
        output_lines.extend([
            f"📅 {date}",
            "-" * 30,
            ""
        ])
        
        for stock in stocks:
            upside_str = f"(+{stock.target_price_upside:.1f}%)" if stock.target_price_upside and stock.target_price_upside > 0 else ""
            output_lines.extend([
                f"  • {stock.ticker} - {stock.company_name}",
                f"    ${stock.current_price:.2f} → ${stock.target_price:.2f} {upside_str}" if stock.current_price and stock.target_price else f"    Current: ${stock.current_price:.2f}" if stock.current_price else "    Price: N/A",
                f"    {stock.sector} | PE: {stock.pe_ratio:.1f}" if stock.pe_ratio else f"    {stock.sector}",
                ""
            ])
        
        output_lines.append("")
    
    return output_lines

def _format_earnings_premarket_list(results: List, params: Dict[str, Any]) -> List[str]:
    """Format details for pre-market earnings winner stocks."""
    def format_large_number(num):
        if not num:
            return "N/A"
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:.0f}"
    
    output_lines = [
        "🔍 Premarket Earnings Screening Results",
        f"📊 Stocks Detected: {len(results)}",
        "=" * 100,
        "",
        "📋 Applied Screening Criteria:",
        f"   • Market Cap: {params.get('market_cap', 'smallover')} (Small+)",
        f"   • Earnings Timing: {params.get('earnings_timing', 'today_before')} (Today Premarket)",
        f"   • Min Price: ${params.get('min_price', 10):.2f}",
        f"   • Min Avg Volume: {format_large_number(params.get('min_avg_volume', 100000))}",
        f"   • Min Price Change: {params.get('min_price_change', 2.0):.1f}%",
        f"   • Sort: {params.get('sort_by', 'price_change')} ({params.get('sort_order', 'desc')})",
        "",
        "=" * 100,
        ""
    ]
    
    # Detailed stock list
    output_lines.extend([
        "📈 Detailed Data:",
        "",
        "| Ticker | Company | Sector | Price | Change | PreMkt | EPS Surprise | Revenue Surprise | Perf 1W | Volume |",
        "|--------|---------|--------|-------|--------|--------|--------------|------------------|---------|--------|"
    ])
    
    for i, stock in enumerate(results[:10]):  # Top 10 stocks
        price_str = f"${stock.price:.2f}" if stock.price else "N/A"
        change_str = f"{stock.price_change:.2f}%" if stock.price_change else "N/A"
        premarket_str = f"{stock.premarket_change_percent:.2f}%" if stock.premarket_change_percent else "N/A"
        eps_surprise_str = f"{stock.eps_surprise:.2f}%" if stock.eps_surprise else "N/A"
        revenue_surprise_str = f"{stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "N/A"
        perf_1w_str = f"{stock.performance_1w:.2f}%" if stock.performance_1w else "N/A"
        volume_str = format_large_number(stock.volume) if stock.volume else "N/A"
        
        ticker_display = stock.ticker or "N/A"
        company_display = (stock.company_name[:15] + "...") if stock.company_name and len(stock.company_name) > 15 else (stock.company_name or "N/A")
        sector_display = (stock.sector[:12] + "...") if stock.sector and len(stock.sector) > 12 else (stock.sector or "N/A")
        
        output_lines.append(f"| {ticker_display:<6} | {company_display:<15} | {sector_display:<12} | {price_str:<7} | {change_str:<8} | {premarket_str:<8} | {eps_surprise_str:<12} | {revenue_surprise_str:<16} | {perf_1w_str:<7} | {volume_str:<6} |")
    
    output_lines.extend([
        "",
        "=" * 100,
        "",
        "🏆 Top 5 Stocks Detailed Analysis:",
        ""
    ])
    
    # Top 5 stocks detailed info
    for i, stock in enumerate(results[:5], 1):
        output_lines.extend([
            f"#{i} 📊 {stock.ticker} - {stock.company_name}",
            f"   📈 Price: ${stock.price:.2f} | Change: {stock.price_change:.2f}%" if stock.price and stock.price_change else f"   📈 Price: {stock.price:.2f} | Change: N/A" if stock.price else "   📈 Price: N/A | Change: N/A",
            f"   🔔 Premarket: {stock.premarket_change_percent:.2f}%" if stock.premarket_change_percent else "   🔔 Premarket: N/A",
            f"   💼 Sector: {stock.sector} | Volume: {format_large_number(stock.volume)}" if stock.sector and stock.volume else f"   💼 Sector: {stock.sector or 'N/A'} | Volume: {format_large_number(stock.volume) if stock.volume else 'N/A'}",
            f"   📊 EPS Surprise: {stock.eps_surprise:.2f}%" if stock.eps_surprise else "   📊 EPS Surprise: N/A",
            f"   💰 Revenue Surprise: {stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "   💰 Revenue Surprise: N/A",
            f"   📈 Performance 1W: {stock.performance_1w:.2f}%" if stock.performance_1w else "   📈 Performance 1W: N/A",
            ""
        ])
    
    # Statistics
    eps_surprises = [s.eps_surprise for s in results if s.eps_surprise is not None]
    revenue_surprises = [s.revenue_surprise for s in results if s.revenue_surprise is not None]
    
    if eps_surprises:
        avg_eps = sum(eps_surprises) / len(eps_surprises)
        max_eps = max(eps_surprises)
        output_lines.extend([
            "📊 EPS Surprise Statistics:",
            f"   • Avg: {avg_eps:.2f}%",
            f"   • Max: {max_eps:.2f}%",
            f"   • Samples: {len(eps_surprises)}",
            ""
        ])
    
    # Sector analysis
    sector_counts = {}
    for stock in results:
        if stock.sector:
            sector_counts[stock.sector] = sector_counts.get(stock.sector, 0) + 1
    
    if sector_counts:
        output_lines.extend([
            "🏢 Sector Analysis:",
            *[f"   • {sector}: {count} stocks" for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:5]],
            ""
        ])
    
    return output_lines

def _format_earnings_afterhours_list(results: List, params: Dict[str, Any]) -> List[str]:
    """Format details for after-hours earnings winner stocks."""
    def format_large_number(num):
        if not num:
            return "N/A"
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:.0f}"
    
    output_lines = [
        "🌙 After-Hours Earnings Screening Results",
        f"📊 Stocks Detected: {len(results)}",
        "=" * 100,
        "",
        "📋 Applied Screening Criteria:",
        f"   • Market Cap: {params.get('market_cap', 'smallover')} (Small+)",
        f"   • Earnings Timing: {params.get('earnings_timing', 'today_after')} (Today After Hours)",
        f"   • Min Price: ${params.get('min_price', 10):.2f}",
        f"   • Min Avg Volume: {format_large_number(params.get('min_avg_volume', 100000))}",
        f"   • Min After-Hours Change: {params.get('min_afterhours_change', 2.0):.1f}%",
        f"   • Sort: {params.get('sort_by', 'afterhours_change')} ({params.get('sort_order', 'desc')})",
        "",
        "=" * 100,
        ""
    ]
    
    # Detailed stock list
    output_lines.extend([
        "📈 Detailed Data:",
        "",
        "| Ticker | Company | Sector | Price | Change | AftHrs | EPS Surprise | Revenue Surprise | Perf 1W | Volume |",
        "|--------|---------|--------|-------|--------|--------|--------------|------------------|---------|--------|"
    ])
    
    for i, stock in enumerate(results[:10]):  # Top 10 stocks
        price_str = f"${stock.price:.2f}" if stock.price else "N/A"
        change_str = f"{stock.price_change:.2f}%" if stock.price_change else "N/A"
        afterhours_str = f"{stock.afterhours_change_percent:.2f}%" if stock.afterhours_change_percent else "N/A"
        eps_surprise_str = f"{stock.eps_surprise:.2f}%" if stock.eps_surprise else "N/A"
        revenue_surprise_str = f"{stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "N/A"
        perf_1w_str = f"{stock.performance_1w:.2f}%" if stock.performance_1w else "N/A"
        volume_str = format_large_number(stock.volume) if stock.volume else "N/A"
        
        ticker_display = stock.ticker or "N/A"
        company_display = (stock.company_name[:15] + "...") if stock.company_name and len(stock.company_name) > 15 else (stock.company_name or "N/A")
        sector_display = (stock.sector[:12] + "...") if stock.sector and len(stock.sector) > 12 else (stock.sector or "N/A")
        
        output_lines.append(f"| {ticker_display:<6} | {company_display:<15} | {sector_display:<12} | {price_str:<7} | {change_str:<8} | {afterhours_str:<8} | {eps_surprise_str:<12} | {revenue_surprise_str:<16} | {perf_1w_str:<7} | {volume_str:<6} |")
    
    output_lines.extend([
        "",
        "=" * 100,
        "",
        "🏆 Top 5 Stocks Detailed Analysis:",
        ""
    ])
    
    # Top 5 stocks detailed info
    for i, stock in enumerate(results[:5], 1):
        output_lines.extend([
            f"#{i} 📊 {stock.ticker} - {stock.company_name}",
            f"   📈 Price: ${stock.price:.2f} | Change: {stock.price_change:.2f}%" if stock.price and stock.price_change else f"   📈 Price: {stock.price:.2f} | Change: N/A" if stock.price else "   📈 Price: N/A | Change: N/A",
            f"   🌙 After Hours: {stock.afterhours_change_percent:.2f}%" if stock.afterhours_change_percent else "   🌙 After Hours: N/A",
            f"   💼 Sector: {stock.sector} | Volume: {format_large_number(stock.volume)}" if stock.sector and stock.volume else f"   💼 Sector: {stock.sector or 'N/A'} | Volume: {format_large_number(stock.volume) if stock.volume else 'N/A'}",
            f"   📊 EPS Surprise: {stock.eps_surprise:.2f}%" if stock.eps_surprise else "   📊 EPS Surprise: N/A",
            f"   💰 Revenue Surprise: {stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "   💰 Revenue Surprise: N/A",
            f"   📈 Performance 1W: {stock.performance_1w:.2f}%" if stock.performance_1w else "   📈 Performance 1W: N/A",
            ""
        ])
    
    # Statistics
    eps_surprises = [s.eps_surprise for s in results if s.eps_surprise is not None]
    revenue_surprises = [s.revenue_surprise for s in results if s.revenue_surprise is not None]
    
    if eps_surprises:
        avg_eps = sum(eps_surprises) / len(eps_surprises)
        max_eps = max(eps_surprises)
        output_lines.extend([
            "📊 EPS Surprise Statistics:",
            f"   • Avg: {avg_eps:.2f}%",
            f"   • Max: {max_eps:.2f}%",
            f"   • Samples: {len(eps_surprises)}",
            ""
        ])
    
    # Sector analysis
    sector_counts = {}
    for stock in results:
        if stock.sector:
            sector_counts[stock.sector] = sector_counts.get(stock.sector, 0) + 1
    
    if sector_counts:
        output_lines.extend([
            "🏢 Sector Analysis:",
            *[f"   • {sector}: {count} stocks" for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:5]],
            ""
        ])
    
    return output_lines

def _format_earnings_trading_list(results: List, params: Dict[str, Any]) -> List[str]:
    """Format details for earnings trade target stocks."""
    def format_large_number(num):
        if not num:
            return "N/A"
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:.0f}"
    
    output_lines = [
        "🎯 Earnings Trade Target Stocks Screening Results",
        f"📊 Detected stocks: {len(results)}",
        "=" * 100,
        "",
        "📋 Applied screening conditions:",
        f"   • Market Cap: {params.get('market_cap', 'smallover')} (small or above)",
        f"   • Earnings period: {params.get('earnings_window', 'yesterday_after_today_before')} (yesterday after close - today before open)",
        f"   • Min price: ${params.get('min_price', 10):.2f}",
        f"   • Min avg volume: {format_large_number(params.get('min_avg_volume', 200000))}",
        f"   • Earnings estimate revision: {params.get('earnings_revision', 'eps_revenue_positive')} (EPS/revenue upward revision)",
        f"   • Price trend: {params.get('price_trend', 'positive_change')} (positive)",
        f"   • 4-week performance: {params.get('performance_4w_range', '0_to_negative_4w')} (recovery candidate)",
        f"   • Min volatility: {params.get('min_volatility', 1.0):.1f}x",
        f"   • Sort: {params.get('sort_by', 'eps_surprise')} ({params.get('sort_order', 'desc')})",
        "",
        "=" * 100,
        ""
    ]
    
    # Detailed stock list
    output_lines.extend([
        "📈 Detailed Data:",
        "",
        "| Ticker | Company | Sector | Price | Change | EPS Surprise | Revenue Surprise | Perf 1W | Volatility | Volume |",
        "|--------|---------|--------|-------|--------|--------------|------------------|---------|------------|--------|"
    ])
    
    for i, stock in enumerate(results[:10]):  # Top 10 stocks
        price_str = f"${stock.price:.2f}" if stock.price else "N/A"
        change_str = f"{stock.price_change:.2f}%" if stock.price_change else "N/A"
        eps_surprise_str = f"{stock.eps_surprise:.2f}%" if stock.eps_surprise else "N/A"
        revenue_surprise_str = f"{stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "N/A"
        perf_1w_str = f"{stock.performance_1w:.2f}%" if stock.performance_1w else "N/A"
        volatility_str = f"{stock.volatility:.2f}" if stock.volatility else "N/A"
        volume_str = format_large_number(stock.volume) if stock.volume else "N/A"
        
        ticker_display = stock.ticker or "N/A"
        company_display = (stock.company_name[:15] + "...") if stock.company_name and len(stock.company_name) > 15 else (stock.company_name or "N/A")
        sector_display = (stock.sector[:12] + "...") if stock.sector and len(stock.sector) > 12 else (stock.sector or "N/A")
        
        output_lines.append(f"| {ticker_display:<6} | {company_display:<15} | {sector_display:<12} | {price_str:<7} | {change_str:<8} | {eps_surprise_str:<12} | {revenue_surprise_str:<16} | {perf_1w_str:<7} | {volatility_str:<10} | {volume_str:<6} |")
    
    output_lines.extend([
        "",
        "=" * 100,
        "",
        "🏆 Top 5 Stocks Detailed Analysis:",
        ""
    ])
    
    # Top 5 stocks detailed info
    for i, stock in enumerate(results[:5], 1):
        output_lines.extend([
            f"#{i} 📊 {stock.ticker} - {stock.company_name}",
            f"   📈 Price: ${stock.price:.2f} | Change: {stock.price_change:.2f}%" if stock.price and stock.price_change else f"   📈 Price: {stock.price:.2f} | Change: N/A" if stock.price else "   📈 Price: N/A | Change: N/A",
            f"   💼 Sector: {stock.sector} | Volume: {format_large_number(stock.volume)}" if stock.sector and stock.volume else f"   💼 Sector: {stock.sector or 'N/A'} | Volume: {format_large_number(stock.volume) if stock.volume else 'N/A'}",
            f"   📊 EPS Surprise: {stock.eps_surprise:.2f}%" if stock.eps_surprise else "   📊 EPS Surprise: N/A",
            f"   💰 Revenue Surprise: {stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "   💰 Revenue Surprise: N/A",
            f"   📈 Performance 1W: {stock.performance_1w:.2f}%" if stock.performance_1w else "   📈 Performance 1W: N/A",
            f"   📊 Volatility: {stock.volatility:.2f}" if stock.volatility else "   📊 Volatility: N/A",
            f"   📈 Performance 1M: {stock.performance_1m:.2f}%" if stock.performance_1m else "   📈 Performance 1M: N/A",
            ""
        ])
    
    # Statistics
    eps_surprises = [s.eps_surprise for s in results if s.eps_surprise is not None]
    revenue_surprises = [s.revenue_surprise for s in results if s.revenue_surprise is not None]
    volatilities = [s.volatility for s in results if s.volatility is not None]
    
    if eps_surprises:
        avg_eps = sum(eps_surprises) / len(eps_surprises)
        max_eps = max(eps_surprises)
        output_lines.extend([
            "📊 EPS Surprise Statistics:",
            f"   • Avg: {avg_eps:.2f}%",
            f"   • Max: {max_eps:.2f}%",
            f"   • Samples: {len(eps_surprises)}",
            ""
        ])
    
    if volatilities:
        avg_volatility = sum(volatilities) / len(volatilities)
        max_volatility = max(volatilities)
        output_lines.extend([
            "📊 Volatility Statistics:",
            f"   • Avg: {avg_volatility:.2f}",
            f"   • Max: {max_volatility:.2f}",
            f"   • Samples: {len(volatilities)}",
            ""
        ])
    
    # Sector analysis
    sector_counts = {}
    for stock in results:
        if stock.sector:
            sector_counts[stock.sector] = sector_counts.get(stock.sector, 0) + 1
    
    if sector_counts:
        output_lines.extend([
            "🏢 Sector Analysis:",
            *[f"   • {sector}: {count} stocks" for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:5]],
            ""
        ])
    
    return output_lines

@server.tool()
def get_sec_filings(
    ticker: str,
    form_types: Optional[List[str]] = None,
    days_back: int = 30,
    max_results: int = 50,
    sort_by: str = "filing_date",
    sort_order: str = "desc"
) -> List[TextContent]:
    """
    Get SEC filing data for the specified stocks
    
    Args:
        ticker: Stock ticker
        form_types: Form type filter (e.g. ["10-K", "10-Q", "8-K"])
        days_back: Number of days back for filings (default: 30 days)
        max_results: Maximum number of results (default: 50)
        sort_by: Sort criteria ("filing_date", "report_date", "form")
        sort_order: Sort order ("asc", "desc")
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        # Get SEC filings data
        filings = finviz_sec.get_sec_filings(
            ticker=ticker,
            form_types=form_types,
            days_back=days_back,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        if not filings:
            return [TextContent(type="text", text=f"No SEC filings found for {ticker} in the last {days_back} days.")]
        
        # Format output
        form_filter_text = f" (Forms: {', '.join(form_types)})" if form_types else ""
        output_lines = [
            f"📄 SEC Filings for {ticker}{form_filter_text}:",
            f"📅 Period: Last {days_back} days | Results: {len(filings)} filings",
            "=" * 80,
            ""
        ]
        
        for filing in filings:
            output_lines.extend([
                f"📅 Filing Date: {filing.filing_date} | Report Date: {filing.report_date}",
                f"📋 Form: {filing.form}",
                f"📝 Description: {filing.description}",
                f"🔗 Filing URL: {filing.filing_url}",
                f"📄 Document URL: {filing.document_url}",
                "-" * 60,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_sec_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_sec_filings: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_major_sec_filings(
    ticker: str,
    days_back: int = 90
) -> List[TextContent]:
    """
    Get major SEC filings (10-K, 10-Q, 8-K, etc.)
    
    Args:
        ticker: Stock ticker
        days_back: Number of days back for filings (default: 90 days)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        # Get major filings
        filings = finviz_sec.get_major_filings(ticker, days_back)
        
        if not filings:
            return [TextContent(type="text", text=f"No major SEC filings found for {ticker} in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"📊 Major SEC Filings for {ticker}:",
            f"📅 Period: Last {days_back} days | Results: {len(filings)} filings",
            "=" * 80,
            "",
            "📋 Form Types: 10-K (Annual), 10-Q (Quarterly), 8-K (Current), DEF 14A (Proxy), SC 13G/D (Ownership)",
            "",
            "=" * 80,
            ""
        ]
        
        # Group by form type for better organization
        forms_dict = {}
        for filing in filings:
            form_type = filing.form
            if form_type not in forms_dict:
                forms_dict[form_type] = []
            forms_dict[form_type].append(filing)
        
        for form_type, form_filings in forms_dict.items():
            output_lines.extend([
                f"📋 Form {form_type} ({len(form_filings)} filings):",
                "-" * 40,
                ""
            ])
            
            for filing in form_filings:
                output_lines.extend([
                    f"  📅 {filing.filing_date} | Report: {filing.report_date}",
                    f"  📝 {filing.description}",
                    f"  🔗 Filing: {filing.filing_url}",
                    f"  📄 Document: {filing.document_url}",
                    ""
                ])
            
            output_lines.append("")
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_major_sec_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_major_sec_filings: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_insider_sec_filings(
    ticker: str,
    days_back: int = 30
) -> List[TextContent]:
    """
    Get insider trading related SEC filings (Form 3, 4, 5, etc.)
    
    Args:
        ticker: Stock ticker
        days_back: Number of days back for filings (default: 30 days)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        # Get insider filings
        filings = finviz_sec.get_insider_filings(ticker, days_back)
        
        if not filings:
            return [TextContent(type="text", text=f"No insider SEC filings found for {ticker} in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"👥 Insider SEC Filings for {ticker}:",
            f"📅 Period: Last {days_back} days | Results: {len(filings)} filings",
            "=" * 80,
            "",
            "📋 Form Types:",
            "  • Form 3: Initial ownership statement",
            "  • Form 4: Statement of changes in beneficial ownership",
            "  • Form 5: Annual statement of changes in beneficial ownership",
            "  • 11-K: Annual reports of employee stock purchase plans",
            "",
            "=" * 80,
            ""
        ]
        
        for filing in filings:
            # Determine filing type explanation
            form_explanation = {
                "3": "Initial ownership statement",
                "4": "Changes in beneficial ownership",
                "5": "Annual ownership changes",
                "11-K": "Employee stock purchase plan report"
            }.get(filing.form, "Insider-related filing")
            
            output_lines.extend([
                f"📋 Form {filing.form} - {form_explanation}",
                f"📅 Filing: {filing.filing_date} | Report: {filing.report_date}",
                f"📝 {filing.description}",
                f"🔗 Filing: {filing.filing_url}",
                f"📄 Document: {filing.document_url}",
                "-" * 60,
                ""
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_insider_sec_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_insider_sec_filings: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_sec_filing_summary(
    ticker: str,
    days_back: int = 90
) -> List[TextContent]:
    """
    Get SEC filings summary and overview for the specified period
    
    Args:
        ticker: Stock ticker
        days_back: Number of days back for overview (default: 90 days)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        # Get filing summary
        summary = finviz_sec.get_filing_summary(ticker, days_back)
        
        if "error" in summary:
            return [TextContent(type="text", text=f"Error getting filing summary for {ticker}: {summary['error']}")]
        
        if summary.get("total_filings", 0) == 0:
            return [TextContent(type="text", text=f"No SEC filings found for {ticker} in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"📊 SEC Filing Summary for {ticker}:",
            f"📅 Period: Last {summary['period_days']} days",
            f"📄 Total Filings: {summary['total_filings']}",
            f"📅 Latest Filing: {summary.get('latest_filing_date', 'N/A')} ({summary.get('latest_filing_form', 'N/A')})",
            "=" * 60,
            "",
            "📋 Filing Breakdown by Form Type:",
            "-" * 40
        ]
        
        # Sort forms by count (descending)
        forms = summary.get("forms", {})
        sorted_forms = sorted(forms.items(), key=lambda x: x[1], reverse=True)
        
        for form_type, count in sorted_forms:
            percentage = (count / summary['total_filings'] * 100) if summary['total_filings'] > 0 else 0
            output_lines.append(f"  📋 {form_type}: {count} filings ({percentage:.1f}%)")
        
        output_lines.extend([
            "",
            "📝 Common Form Types:",
            "  • 10-K: Annual report (comprehensive overview)",
            "  • 10-Q: Quarterly report (financial updates)",
            "  • 8-K: Current report (material events)",
            "  • DEF 14A: Proxy statement (shareholder meetings)",
            "  • 4: Insider trading activities",
            "  • SC 13G/D: Beneficial ownership (>5% ownership changes)"
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_sec_filing_summary: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_sec_filing_summary: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_edgar_filing_content(
    ticker: str,
    accession_number: str,
    primary_document: str,
    max_length: int = 50000
) -> List[TextContent]:
    """
    Get SEC filing document content via EDGAR API
    
    Args:
        ticker: Stock ticker
        accession_number: SEC accession number (with dashes)
        primary_document: Primary document filename
        max_length: Maximum content length (default: 50,000 chars)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        logger.info(f"Fetching EDGAR document content for {ticker}: {accession_number}/{primary_document}")
        
        # Get document content via EDGAR API
        content_data = edgar_client.get_filing_document_content(
            ticker=ticker,
            accession_number=accession_number,
            primary_document=primary_document,
            max_length=max_length
        )
        
        if content_data.get('status') == 'error':
            return [TextContent(type="text", text=f"Error: {content_data.get('error', 'Unknown error')}")]
        
        # Format output
        metadata = content_data.get('metadata', {})
        content = content_data.get('content', '')
        
        output_lines = [
            f"📄 SEC Filing Document Content for {ticker}:",
            f"🔗 Document: {accession_number}/{primary_document}",
            f"📅 Retrieved: {metadata.get('retrieved_at', 'N/A')}",
            f"📊 Content Length: {metadata.get('content_length', 0):,} characters",
            "=" * 80,
            "",
            content[:max_length] if len(content) > max_length else content
        ]
        
        if len(content) > max_length:
            output_lines.extend([
                "",
                "=" * 80,
                f"[Content truncated - showing first {max_length:,} characters]"
            ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_filing_content: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_filing_content: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_multiple_edgar_filing_contents(
    ticker: str,
    filings_data: List[Dict[str, str]],
    max_length: int = 20000
) -> List[TextContent]:
    """
    Bulk fetch multiple SEC filing document contents via EDGAR API
    
    Args:
        ticker: Stock ticker
        filings_data: List of filing data [{"accession_number": "...", "primary_document": "..."}]
        max_length: Maximum content length per document (default: 20,000 chars)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        if not filings_data:
            return [TextContent(type="text", text="No filing data provided.")]
        
        logger.info(f"Fetching {len(filings_data)} EDGAR document contents for {ticker}")
        
        # Prepare filing data with ticker
        filings_with_ticker = []
        for filing in filings_data:
            filing_copy = filing.copy()
            filing_copy['ticker'] = ticker
            filings_with_ticker.append(filing_copy)
        
        # Get multiple document contents via EDGAR API
        results = edgar_client.get_multiple_filing_contents(
            filings_data=filings_with_ticker,
            max_length=max_length
        )
        
        if not results:
            return [TextContent(type="text", text=f"No document contents retrieved for {ticker}.")]
        
        # Format output
        output_lines = [
            f"📄 Multiple SEC Filing Document Contents for {ticker}:",
            f"📊 Retrieved: {len(results)} documents",
            "=" * 80,
            ""
        ]
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')
            status = result.get('status', 'unknown')
            
            output_lines.extend([
                f"📋 Document {i}/{len(results)}:",
                f"   📄 File: {metadata.get('accession_number', 'N/A')}/{metadata.get('primary_document', 'N/A')}",
                f"   📅 Retrieved: {metadata.get('retrieved_at', 'N/A')}",
                f"   📊 Length: {metadata.get('content_length', 0):,} characters",
                f"   ✅ Status: {status}",
                ""
            ])
            
            if status == 'error':
                error_msg = result.get('error', 'Unknown error')
                output_lines.extend([
                    f"   ❌ Error: {error_msg}",
                    ""
                ])
            else:
                # Show first 500 characters of content
                preview_length = min(500, len(content))
                preview = content[:preview_length]
                output_lines.extend([
                    f"   📝 Content Preview ({preview_length} chars):",
                    f"   {preview}",
                    ""
                ])
                
                if len(content) > preview_length:
                    output_lines.append(f"   [... {len(content) - preview_length:,} more characters]")
                    output_lines.append("")
            
            output_lines.extend(["-" * 60, ""])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_multiple_edgar_filing_contents: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_multiple_edgar_filing_contents: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_edgar_company_filings(
    ticker: str,
    form_types: Optional[List[str]] = None,
    max_count: int = 50,
    days_back: int = 365
) -> List[TextContent]:
    """
    Get company filing list via EDGAR API
    
    Args:
        ticker: Stock ticker
        form_types: Form type filter (e.g. ["10-K", "10-Q", "8-K"])
        max_count: Maximum number of results (default: 50)
        days_back: Number of days back (default: 365 days)
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        logger.info(f"Fetching EDGAR filings for {ticker} via EDGAR API")
        
        # Calculate date range
        from datetime import datetime, timedelta
        date_to = datetime.now().strftime('%Y-%m-%d')
        date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Get company filings via EDGAR API
        filings = edgar_client.get_company_filings(
            ticker=ticker,
            form_types=form_types,
            date_from=date_from,
            date_to=date_to,
            max_count=max_count
        )
        
        if not filings:
            form_filter_text = f" (forms: {', '.join(form_types)})" if form_types else ""
            return [TextContent(type="text", text=f"No EDGAR filings found for {ticker}{form_filter_text} in the last {days_back} days.")]
        
        # Format output
        output_lines = [
            f"📊 EDGAR Company Filings for {ticker}:",
            f"📅 Period: {date_from} to {date_to} ({days_back} days)",
            f"📄 Results: {len(filings)} filings",
        ]
        
        if form_types:
            output_lines.append(f"📋 Form Filter: {', '.join(form_types)}")
        
        output_lines.extend([
            "=" * 80,
            "",
            "📋 Available Form Types:",
            "  • 10-K: Annual report",
            "  • 10-Q: Quarterly report", 
            "  • 8-K: Current report (material events)",
            "  • DEF 14A: Proxy statement",
            "  • 4: Statement of changes in beneficial ownership",
            "",
            "=" * 80,
            ""
        ])
        
        for filing in filings:
            output_lines.extend([
                f"📋 Form {filing['form']} - {filing.get('description', 'N/A')}",
                f"📅 Filing: {filing['filing_date']} | Report: {filing['report_date']}",
                f"📄 Document: {filing['accession_number']}/{filing['primary_document']}",
                f"🔗 Filing URL: {filing['filing_url']}",
                f"📄 Document URL: {filing['document_url']}",
                "-" * 60,
                ""
            ])
        
        output_lines.extend([
            "",
            "💡 To get document content, use get_edgar_filing_content with:",
            "   ticker, accession_number, and primary_document from above"
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_company_filings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_company_filings: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_edgar_company_facts(
    ticker: str
) -> List[TextContent]:
    """
    Get company basic information and fact data via EDGAR API
    
    Args:
        ticker: Stock ticker
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        logger.info(f"Fetching EDGAR company facts for {ticker}")
        
        # Get CIK from ticker first
        cik = edgar_client._get_cik_from_ticker(ticker)
        if not cik:
            return [TextContent(type="text", text=f"Could not find CIK for ticker {ticker}. Please verify the ticker symbol.")]
        
        # Get company facts via EDGAR API
        try:
            company_facts = edgar_client.client.get_company_facts(cik)
        except Exception as e:
            return [TextContent(type="text", text=f"Error fetching company facts for {ticker}: {str(e)}")]
        
        if not company_facts:
            return [TextContent(type="text", text=f"No company facts found for {ticker}.")]
        
        # Extract basic information
        cik = company_facts.get('cik', 'N/A')
        entity_name = company_facts.get('entityName', 'N/A')
        
        # Format output
        output_lines = [
            f"🏢 EDGAR Company Facts for {ticker}:",
            f"📊 Entity Name: {entity_name}",
            f"🔢 CIK: {cik}",
            "=" * 60,
            ""
        ]
        
        # Show available facts/concepts
        facts = company_facts.get('facts', {})
        if facts:
            output_lines.extend([
                "📋 Available Financial Concepts:",
                ""
            ])
            
            # Group by taxonomy
            for taxonomy, concepts in facts.items():
                if concepts:
                    output_lines.extend([
                        f"📊 {taxonomy.upper()} Taxonomy:",
                        f"   📈 Available concepts: {len(concepts)}",
                        ""
                    ])
                    
                    # Show first few concepts as examples
                    concept_names = list(concepts.keys())[:5]
                    for concept in concept_names:
                        concept_data = concepts[concept]
                        description = concept_data.get('description', concept)
                        output_lines.append(f"   • {concept}: {description}")
                    
                    if len(concepts) > 5:
                        output_lines.append(f"   ... and {len(concepts) - 5} more concepts")
                    
                    output_lines.append("")
        
        output_lines.extend([
            "💡 To get specific concept data, use get_edgar_company_concept with:",
            f"   ticker='{ticker}', concept='Assets', taxonomy='us-gaap'"
        ])
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_company_facts: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_company_facts: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.tool()
def get_edgar_company_concept(
    ticker: str,
    concept: str,
    taxonomy: str = "us-gaap"
) -> List[TextContent]:
    """
    Get specific financial concept data for a company via EDGAR API
    
    Args:
        ticker: Stock ticker
        concept: XBRL concept (e.g. 'Assets', 'Revenues', 'NetIncomeLoss')
        taxonomy: Taxonomy ('us-gaap', 'dei', 'invest')
    """
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        
        logger.info(f"Fetching EDGAR concept {concept} for {ticker}")
        
        # Get company concept via EDGAR API
        concept_data = edgar_client.get_company_concept(
            ticker=ticker,
            concept=concept,
            taxonomy=taxonomy
        )
        
        if 'error' in concept_data:
            return [TextContent(type="text", text=f"Error: {concept_data['error']}")]
        
        # Extract basic information
        cik = concept_data.get('cik', 'N/A')
        entity_name = concept_data.get('entityName', 'N/A')
        concept_label = concept_data.get('label', concept)
        description = concept_data.get('description', 'N/A')
        
        # Format output
        output_lines = [
            f"📊 EDGAR Company Concept: {ticker} - {concept}",
            f"🏢 Entity: {entity_name} (CIK: {cik})",
            f"📋 Concept: {concept_label}",
            f"📝 Description: {description}",
            f"🏷️ Taxonomy: {taxonomy}",
            "=" * 80,
            ""
        ]
        
        # Show units and values
        units = concept_data.get('units', {})
        if units:
            output_lines.append("📊 Available Data Units:")
            output_lines.append("")
            
            for unit_type, unit_data in units.items():
                output_lines.extend([
                    f"💰 Unit: {unit_type}",
                    f"   📈 Data points: {len(unit_data)}",
                    ""
                ])
                
                # Show recent values
                if unit_data:
                    output_lines.append("   📅 Recent Values:")
                    # Sort by end date (most recent first)
                    sorted_data = sorted(unit_data, key=lambda x: x.get('end', ''), reverse=True)
                    
                    for i, entry in enumerate(sorted_data[:10]):  # Show last 10 entries
                        end_date = entry.get('end', 'N/A')
                        value = entry.get('val', 'N/A')
                        form = entry.get('form', 'N/A')
                        filed = entry.get('filed', 'N/A')
                        
                        # Format large numbers
                        if isinstance(value, (int, float)):
                            if value >= 1_000_000_000:
                                formatted_value = f"${value/1_000_000_000:.2f}B"
                            elif value >= 1_000_000:
                                formatted_value = f"${value/1_000_000:.2f}M"
                            elif value >= 1_000:
                                formatted_value = f"${value/1_000:.2f}K"
                            else:
                                formatted_value = f"${value:,.2f}"
                        else:
                            formatted_value = str(value)
                        
                        output_lines.append(f"   • {end_date}: {formatted_value} ({form} filed: {filed})")
                    
                    if len(sorted_data) > 10:
                        output_lines.append(f"   ... and {len(sorted_data) - 10} more entries")
                
                output_lines.append("")
        else:
            output_lines.append("⚠️ No unit data available for this concept.")
        
        return [TextContent(type="text", text="\n".join(output_lines))]
        
    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in get_edgar_company_concept: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_edgar_company_concept: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# Register Field Discovery Tools
logger.info("Registering Field Discovery tools...")
register_field_discovery_tools(server)
logger.info("Field Discovery tools registered successfully")

# ---------------------------------------------------------------------------
# Moving Average Position Tool
# ---------------------------------------------------------------------------


@server.tool()
def get_moving_average_position(ticker: str) -> List[TextContent]:
    """Return current price and its percentage distance to 20-, 50-, and 200-day SMAs.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").

    Returns:
        Single TextContent with formatted analysis.
    """

    # Validate ticker first
    if not validate_ticker(ticker):
        raise ValueError(f"Invalid ticker: {ticker}")

    # Retrieve fundamentals (full set)
    fundamentals = finviz_client.get_stock_fundamentals(ticker.upper())
    if fundamentals is None:
        return [TextContent(type="text", text=f"No data found for ticker: {ticker.upper()}")]

    # ------------------ Helper: value retrieval and float conversion ------------------------
    def _to_float(val):
        """Convert Finviz numeric string to float.

        Handles:
        • Commas in thousands ("1,234")
        • Percentage signs ("12.3%")
        • Leading/trailing whitespace
        • Literal dash "-" as missing value
        """
        if val in ("-", "", None):
            return None
        try:
            if isinstance(val, (int, float)):
                return float(val)
            str_val = str(val).strip().replace(",", "")
            if str_val.endswith("%"):
                str_val = str_val.rstrip("%")
            return float(str_val)
        except (TypeError, ValueError):
            return None

    def _get_ma(period: int):
        """Return tuple (sma_price, diff_percent) if Finviz provides either.

        Finviz's SMA columns give *percentage distance* of price vs SMA.
        Example: "-3.37%" means price is 3.37 % below the SMA.
        If % is present, convert to absolute SMA value using current price.
        Otherwise assume column already contains SMA price.
        """
        candidate_keys = [
            f"{period}_day_simple_moving_average",
            f"{period}_day_moving_average",
            f"sma_{period}",
            f"sma{period}",
        ]

        raw_value = None
        found_key = None
        for key in candidate_keys:
            if key in fundamentals:
                raw_value = fundamentals.get(key)
                found_key = key
                break
        if raw_value is None:
            # Fallback pattern search
            for key in fundamentals.keys():
                if f"sma{period}" in key.replace("_", ""):
                    raw_value = fundamentals.get(key)
                    found_key = key
                    break

        if raw_value is None:
            return None, None  # not available

        # If the string ends with %, treat as percentage difference
        if isinstance(raw_value, str) and raw_value.strip().endswith('%'):
            diff_percent = _to_float(raw_value)  # after cleaning % we get float
            price_val_local = _to_float(fundamentals.get("price"))  # captured from outer scope – may be None
            if diff_percent is None or price_val_local is None:
                return None, diff_percent
            # Price = SMA * (1 + diff/100)  →  SMA = Price / (1 + diff/100)
            try:
                sma_val = price_val_local / (1 + diff_percent / 100)
            except ZeroDivisionError:
                sma_val = None
            return sma_val, diff_percent

        # Otherwise interpret as absolute SMA price
        sma_val = _to_float(raw_value)
        return sma_val, None

    price_val = _to_float(fundamentals.get("price"))
    ma20_val, diff20 = _get_ma(20)
    ma50_val, diff50 = _get_ma(50)
    ma200_val, diff200 = _get_ma(200)

    def _diff_str(price: Optional[float], ma: Optional[float]):
        if price is None or ma is None or ma == 0:
            return "N/A"
        diff = (price - ma) / ma * 100
        sign = "+" if diff >= 0 else ""
        return f"{sign}{diff:.2f}% {'above' if diff >= 0 else 'below'}"

    # Pre-compute diff text to avoid nested f-strings (Py3.8 compatible)
    def _format_diff(diff_val, price_val_local, ma_val_local):
        if diff_val is None:
            return _diff_str(price_val_local, ma_val_local)
        return f"{diff_val:+.2f}% {'above' if diff_val > 0 else 'below'}"

    diff20_text = _format_diff(diff20, price_val, ma20_val)
    diff50_text = _format_diff(diff50, price_val, ma50_val)
    diff200_text = _format_diff(diff200, price_val, ma200_val)

    lines = [
        f"📐 Moving Average Position for {ticker.upper()}",
        "=" * 60,
        "",
        f"Current Price         : {f'${price_val:.2f}' if price_val is not None else 'N/A'}",
        "-" * 60,
        f"20-Day SMA            : {f'${ma20_val:.2f}' if ma20_val is not None else 'N/A'}",
        f"   → {diff20_text} compared to price",
        "",
        f"50-Day SMA            : {f'${ma50_val:.2f}' if ma50_val is not None else 'N/A'}",
        f"   → {diff50_text} compared to price",
        "",
        f"200-Day SMA           : {f'${ma200_val:.2f}' if ma200_val is not None else 'N/A'}",
        f"   → {diff200_text} compared to price",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


# ---------------------------------------------------------------------------
# Custom Screener Tool
# ---------------------------------------------------------------------------


@server.tool()
def custom_screener(
    filters: str,
    signal: Optional[str] = None,
    order: Optional[str] = None,
    max_results: int = 50,
) -> List[TextContent]:
    """Screen stocks using raw FinViz filter codes for maximum flexibility.

    Unlike the preset screener tools, this accepts raw FinViz filter tokens
    directly so you can combine any filters that FinViz supports.

    Args:
        filters: Comma-separated raw FinViz filter codes.
            Examples:
              "cap_large,fa_div_o3"              - Large cap, dividend > 3%
              "cap_small,fa_pe_u20"              - Small cap, P/E < 20
              "cap_mega,fa_roe_o20,fa_pb_u3"     - Mega cap, ROE > 20%, P/B < 3
              "sec_technology,fa_salesqoq_o25"    - Tech sector, quarterly sales growth > 25%
              "earningsdate_yesterdayafter|todaybefore" - Earnings yesterday after-close through today before-open
            Common filter prefixes:
              cap_  : Market cap (nano/micro/small/mid/large/mega)
              fa_   : Fundamental analysis (pe, div, roe, eps, etc.)
              ta_   : Technical analysis (sma, rsi, pattern, etc.)
              sec_  : Sector
              ind_  : Industry
              geo_  : Country
              sh_   : Share data (price, avgvol, float, etc.)
        signal: Optional FinViz signal identifier (e.g. "ta_topgainers",
            "ta_mostactive", "ta_unusualvolume", "ta_oversold").
        order: Optional sort order. Use a column name for ascending or prefix
            with '-' for descending (e.g. "-marketcap", "change", "-volume").
        max_results: Maximum number of results to return (1-500, default 50).

    Returns:
        List of TextContent with formatted screening results.
    """
    try:
        # --- Validate filters ---
        filter_errors, normalized_filters = validate_and_normalize_raw_filters(filters)
        if filter_errors:
            return [TextContent(type="text", text=f"Filter validation error: {'; '.join(filter_errors)}")]

        # --- Validate optional signal ---
        if signal is not None:
            signal_errors = validate_signal(signal)
            if signal_errors:
                return [TextContent(type="text", text=f"Signal validation error: {'; '.join(signal_errors)}")]

        # --- Validate optional order ---
        if order is not None:
            order_errors = validate_raw_sort_order(order)
            if order_errors:
                return [TextContent(type="text", text=f"Order validation error: {'; '.join(order_errors)}")]

        # --- Validate max_results ---
        if not isinstance(max_results, int) or max_results < 1 or max_results > 500:
            return [TextContent(type="text", text=f"Invalid max_results: {max_results} (must be an integer between 1 and 500)")]

        # --- Execute screening ---
        stocks = finviz_client.screen_stocks_raw(
            filters=normalized_filters,
            signal=signal,
            order=order,
            max_results=max_results,
        )

        if not stocks:
            return [TextContent(type="text", text=f"No stocks found matching filters: {normalized_filters}")]

        # --- Format output ---
        lines = []
        lines.append(f"Custom Screener Results ({len(stocks)} stocks)")
        lines.append("=" * 60)
        lines.append(f"Filters: {normalized_filters}")
        if signal:
            lines.append(f"Signal : {signal}")
        if order:
            lines.append(f"Order  : {order}")
        lines.append("")

        for stock in stocks:
            ticker = getattr(stock, 'ticker', 'N/A')
            company = getattr(stock, 'company_name', 'N/A')
            sector = getattr(stock, 'sector', 'N/A')
            industry = getattr(stock, 'industry', 'N/A')
            price = getattr(stock, 'price', None)
            change = getattr(stock, 'price_change', None)
            volume = getattr(stock, 'volume', None)
            market_cap = getattr(stock, 'market_cap', None)
            pe = getattr(stock, 'pe_ratio', None)
            rel_volume = getattr(stock, 'relative_volume', None)
            dividend_yield = getattr(stock, 'dividend_yield', None)
            eps_surprise = getattr(stock, 'eps_surprise', None)

            price_str = f"${price:.2f}" if price is not None else "N/A"
            change_str = f"{change:+.2f}%" if change is not None else "N/A"
            vol_str = format_large_number(volume) if volume is not None else "N/A"
            mcap_str = format_large_number(market_cap * 1e6) if market_cap is not None else "N/A"
            pe_str = f"{pe:.1f}" if pe is not None else "N/A"
            rv_str = f"{rel_volume:.2f}" if rel_volume is not None else "N/A"

            lines.append(f"{ticker} | {company}")
            lines.append(f"  Sector: {sector} | Industry: {industry}")
            lines.append(f"  Price: {price_str} | Change: {change_str} | Volume: {vol_str}")
            lines.append(f"  Market Cap: {mcap_str} | P/E: {pe_str} | Rel Volume: {rv_str}")

            extras = []
            if dividend_yield is not None:
                extras.append(f"Div Yield: {dividend_yield:.2f}%")
            if eps_surprise is not None:
                extras.append(f"EPS Surprise: {eps_surprise:+.2f}%")
            if extras:
                lines.append(f"  {' | '.join(extras)}")

            lines.append("")

        return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:
        logger.error(f"Error in custom_screener: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
