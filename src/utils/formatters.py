from typing import List, Dict, Any, Optional
from ..models import StockData, SectorPerformance, NewsData

def format_stock_data_table(stocks: List[StockData], fields: Optional[List[str]] = None) -> str:
    """
    Format stock data as a table.
    
    Args:
        stocks: List of stock data
        fields: List of fields to display
        
    Returns:
        Formatted table string
    """
    if not stocks:
        return "No stocks found."
    
    # Default fields
    if fields is None:
        fields = ['ticker', 'company_name', 'sector', 'price', 'price_change', 
                 'volume', 'market_cap']
    
    # Header row
    header_mapping = {
        'ticker': 'Ticker',
        'company_name': 'Company',
        'sector': 'Sector',
        'industry': 'Industry',
        'price': 'Price',
        'price_change': 'Change%',
        'volume': 'Volume',
        'market_cap': 'Market Cap',
        'pe_ratio': 'P/E',
        'relative_volume': 'Rel Vol',
        'target_price': 'Target',
        'analyst_recommendation': 'Recom'
    }
    
    headers = [header_mapping.get(field, field.title()) for field in fields]
    
    # Data rows
    rows = []
    for stock in stocks:
        row = []
        for field in fields:
            value = getattr(stock, field, None)
            formatted_value = format_field_value(field, value)
            row.append(formatted_value)
        rows.append(row)
    
    # Create table
    return create_ascii_table(headers, rows)

def format_large_number(num: float) -> str:
    """
    Format a large number in a readable form.
    
    Args:
        num: Number
        
    Returns:
        Formatted string
    """
    if num >= 1e9:
        return f"{num/1e9:.2f}B"
    elif num >= 1e6:
        return f"{num/1e6:.2f}M"
    elif num >= 1e3:
        return f"{num/1e3:.2f}K"
    else:
        return f"{num:.0f}"

def format_field_value(field: str, value: Any) -> str:
    """
    Format a field value.
    
    Args:
        field: Field name
        value: Value
        
    Returns:
        Formatted string
    """
    if value is None:
        return "N/A"
    
    # Price fields
    if field in ['price', 'target_price', 'week_52_high', 'week_52_low']:
        return f"${value:.2f}" if isinstance(value, (int, float)) else str(value)
    
    # Percentage fields
    if field in ['price_change', 'dividend_yield', 'performance_1w', 'performance_1m', 
                'eps_surprise', 'revenue_surprise']:
        return f"{value:.2f}%" if isinstance(value, (int, float)) else str(value)
    
    # Volume fields
    if field in ['volume', 'avg_volume']:
        return format_large_number(value) if isinstance(value, (int, float)) else str(value)
    
    # Multiplier fields
    if field in ['relative_volume', 'pe_ratio', 'beta']:
        return f"{value:.2f}x" if isinstance(value, (int, float)) else str(value)
    
    # Display as-is
    return str(value)

def create_ascii_table(headers: List[str], rows: List[List[str]]) -> str:
    """
    Create an ASCII table.
    
    Args:
        headers: List of headers
        rows: List of data rows
        
    Returns:
        ASCII table string
    """
    if not headers or not rows:
        return ""
    
    # Calculate max width for each column
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(min(max_width, 20))  # Cap at 20 characters
    
    # Header row
    header_line = "| " + " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers)) + " |"
    separator_line = "+" + "+".join("-" * (col_widths[i] + 2) for i in range(len(headers))) + "+"
    
    # Data rows
    data_lines = []
    for row in rows:
        padded_row = []
        for i, cell in enumerate(row):
            if i < len(col_widths):
                cell_str = str(cell)[:col_widths[i]]  # Width limit
                padded_row.append(cell_str.ljust(col_widths[i]))
        data_line = "| " + " | ".join(padded_row) + " |"
        data_lines.append(data_line)
    
    # Assemble table
    table_lines = [
        separator_line,
        header_line,
        separator_line
    ]
    table_lines.extend(data_lines)
    table_lines.append(separator_line)
    
    return "\n".join(table_lines)

def format_earnings_summary(stocks: List[StockData]) -> str:
    """
    Format an earnings summary.
    
    Args:
        stocks: List of stock data
        
    Returns:
        Formatted summary
    """
    if not stocks:
        return "No earnings data found."
    
    summary_lines = [
        f"Earnings Summary ({len(stocks)} stocks):",
        "=" * 50,
        ""
    ]
    
    # Count by sector
    sector_counts = {}
    positive_surprises = 0
    negative_surprises = 0
    
    for stock in stocks:
        # Sector aggregation
        sector = stock.sector or "Unknown"
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        
        # Surprise aggregation
        if stock.eps_surprise:
            if stock.eps_surprise > 0:
                positive_surprises += 1
            else:
                negative_surprises += 1
    
    # Sector breakdown
    summary_lines.append("Sector Breakdown:")
    for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True):
        summary_lines.append(f"  {sector}: {count} stocks")
    
    summary_lines.extend([
        "",
        "Earnings Surprises:",
        f"  Positive: {positive_surprises} stocks",
        f"  Negative: {negative_surprises} stocks",
        ""
    ])
    
    return "\n".join(summary_lines)

def format_sector_performance(sectors: List[SectorPerformance]) -> str:
    """
    Format sector performance data.
    
    Args:
        sectors: List of sector performance data
        
    Returns:
        Formatted string
    """
    if not sectors:
        return "No sector performance data found."
    
    headers = ['Sector', '1D', '1W', '1M', '3M', '6M', '1Y', 'Stocks']
    rows = []
    
    for sector in sectors:
        row = [
            sector.sector,
            f"{sector.performance_1d:.2f}%",
            f"{sector.performance_1w:.2f}%",
            f"{sector.performance_1m:.2f}%",
            f"{sector.performance_3m:.2f}%",
            f"{sector.performance_6m:.2f}%",
            f"{sector.performance_1y:.2f}%",
            str(sector.stock_count)
        ]
        rows.append(row)
    
    return create_ascii_table(headers, rows)

def format_news_summary(news_list: List[NewsData]) -> str:
    """
    Format news data.
    
    Args:
        news_list: List of news data
        
    Returns:
        Formatted string
    """
    if not news_list:
        return "No news found."
    
    summary_lines = [
        f"News Summary ({len(news_list)} articles):",
        "=" * 50,
        ""
    ]
    
    for news in news_list[:10]:  # Show only latest 10 items
        summary_lines.extend([
            f"[{news.category}] {news.title}",
            f"Source: {news.source} | Date: {news.date.strftime('%Y-%m-%d %H:%M')}",
            f"URL: {news.url}",
            "-" * 40,
            ""
        ])
    
    return "\n".join(summary_lines)

def format_screening_result_summary(stocks: List[StockData], params: Dict[str, Any]) -> str:
    """
    Format a screening result summary.
    
    Args:
        stocks: List of stock data
        params: Screening parameters
        
    Returns:
        Formatted summary
    """
    summary_lines = [
        f"Screening Results Summary:",
        "=" * 40,
        f"Total stocks found: {len(stocks)}",
        ""
    ]
    
    # Display parameters
    summary_lines.append("Search Criteria:")
    for key, value in params.items():
        if value is not None:
            summary_lines.append(f"  {key}: {value}")
    
    summary_lines.append("")
    
    if stocks:
        # Statistics
        prices = [s.price for s in stocks if s.price is not None]
        changes = [s.price_change for s in stocks if s.price_change is not None]
        volumes = [s.volume for s in stocks if s.volume is not None]
        
        if prices:
            summary_lines.extend([
                "Statistics:",
                f"  Price range: ${min(prices):.2f} - ${max(prices):.2f}",
                f"  Average price: ${sum(prices)/len(prices):.2f}"
            ])
        
        if changes:
            summary_lines.extend([
                f"  Change range: {min(changes):.2f}% - {max(changes):.2f}%",
                f"  Average change: {sum(changes)/len(changes):.2f}%"
            ])
        
        if volumes:
            summary_lines.append(f"  Average volume: {format_large_number(sum(volumes)/len(volumes))}")
        
        summary_lines.append("")
    
    return "\n".join(summary_lines)