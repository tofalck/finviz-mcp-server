import logging
from typing import List, Optional, Union
from datetime import datetime, timedelta

import pandas as pd

from .base import FinvizClient
from ..models import NewsData

logger = logging.getLogger(__name__)

class FinvizNewsClient(FinvizClient):
    """Dedicated Finviz news client."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
    
    def get_stock_news(self, tickers: Union[str, List[str]], days_back: int = 7, 
                      news_type: str = "all") -> List[NewsData]:
        """
        Fetch news for specified tickers (using CSV export).
        
        Args:
            tickers: Ticker symbol(s) (single, comma-separated string, or list)
            days_back: Number of days back to retrieve news
            news_type: News type (all, earnings, analyst, insider, general)
            
        Returns:
            List of NewsData objects
        """
        try:
            from ..utils.validators import validate_tickers, parse_tickers
            
            # Validate tickers
            if not validate_tickers(tickers):
                raise ValueError(f"Invalid tickers: {tickers}")
            
            # Normalize tickers to a list
            ticker_list = parse_tickers(tickers)
            
            params = {
                'v': '3',  # Add version parameter
                't': ','.join(ticker_list)  # Specify multiple tickers as comma-separated
            }
            
            # News type filter
            if news_type != "all":
                type_mapping = {
                    'earnings': 'earnings',
                    'analyst': 'analyst',
                    'insider': 'insider',
                    'general': 'general'
                }
                if news_type in type_mapping:
                    params['filter'] = type_mapping[news_type]
            
            # Fetch news data from CSV
            df = self._fetch_csv_from_url(self.NEWS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning(f"No news data returned for {ticker_list}")
                return []
            
            # Convert CSV data to list of NewsData objects
            news_list = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for _, row in df.iterrows():
                try:
                    # Pass full list for multiple tickers
                    primary_ticker = ticker_list[0] if len(ticker_list) == 1 else ','.join(ticker_list)
                    news_data = self._parse_news_from_csv(row, primary_ticker, cutoff_date)
                    if news_data:
                        news_list.append(news_data)
                except Exception as e:
                    logger.warning(f"Failed to parse news data from CSV: {e}")
                    continue
            
            logger.info(f"Retrieved {len(news_list)} news items for {ticker_list}")
            return news_list
            
        except Exception as e:
            logger.error(f"Error retrieving news for {tickers}: {e}")
            return []
    
    def get_market_news(self, days_back: int = 3, max_items: int = 50) -> List[NewsData]:
        """
        Fetch market-wide news (using CSV export).
        
        Args:
            days_back: Number of days back to retrieve news
            max_items: Maximum number of items to retrieve
            
        Returns:
            List of NewsData objects
        """
        try:
            params = {
                'v': '3'  # Add version parameter
            }
            
            # Fetch market news data from CSV
            df = self._fetch_csv_from_url(self.NEWS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning("No market news data returned")
                return []
            
            # Convert CSV data to list of NewsData objects
            news_list = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for _, row in df.iterrows():
                try:
                    news_data = self._parse_news_from_csv(row, "MARKET", cutoff_date)
                    if news_data:
                        news_list.append(news_data)
                        if len(news_list) >= max_items:
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse market news data from CSV: {e}")
                    continue
            
            logger.info(f"Retrieved {len(news_list)} market news items")
            return news_list
            
        except Exception as e:
            logger.error(f"Error retrieving market news: {e}")
            return []
    
    def get_sector_news(self, sector: str, days_back: int = 5, 
                       max_items: int = 30) -> List[NewsData]:
        """
        Fetch news for a specific sector (using CSV export).
        
        Args:
            sector: Sector name
            days_back: Number of days back to retrieve news
            max_items: Maximum number of items to retrieve
            
        Returns:
            List of NewsData objects
        """
        try:
            params = {
                'v': '3',  # Add version parameter
                'sec': sector.lower().replace(' ', '_')
            }
            
            # Fetch sector news data from CSV
            df = self._fetch_csv_from_url(self.NEWS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning(f"No news data returned for {sector} sector")
                return []
            
            # Convert CSV data to list of NewsData objects
            news_list = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for _, row in df.iterrows():
                try:
                    news_data = self._parse_news_from_csv(row, f"SECTOR_{sector}", cutoff_date)
                    if news_data:
                        news_list.append(news_data)
                        if len(news_list) >= max_items:
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse sector news data from CSV: {e}")
                    continue
            
            logger.info(f"Retrieved {len(news_list)} news items for {sector} sector")
            return news_list
            
        except Exception as e:
            logger.error(f"Error retrieving news for {sector} sector: {e}")
            return []
    

    
    def _parse_news_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse news date string.
        
        Args:
            date_text: Date string
            
        Returns:
            datetime object or None
        """
        try:
            # Handle Finviz date format
            # "Dec-29-23 08:00AM" format
            date_text = date_text.strip()
            
            if not date_text:
                return None
            
            # Handle today/yesterday notation
            if 'Today' in date_text or 'today' in date_text:
                return datetime.now()
            elif 'Yesterday' in date_text or 'yesterday' in date_text:
                return datetime.now() - timedelta(days=1)
            
            # Time-only case (today's article)
            if ':' in date_text and len(date_text) < 10:
                return datetime.now()
            
            # Handle standard date format
            # "Dec-29-23" -> "2023-12-29"
            parts = date_text.split()
            if len(parts) >= 1:
                date_part = parts[0]
                if '-' in date_part:
                    try:
                        # "Dec-29-23" format
                        month_str, day_str, year_str = date_part.split('-')
                        
                        # Convert month name to number
                        month_mapping = {
                            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                            'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                        }
                        
                        month = month_mapping.get(month_str, 1)
                        day = int(day_str)
                        year = 2000 + int(year_str) if len(year_str) == 2 else int(year_str)
                        
                        return datetime(year, month, day)
                        
                    except ValueError:
                        pass
            
            # Other formats (default to current time)
            return datetime.now()
            
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_text}': {e}")
            return datetime.now()
    
    def _extract_news_source(self, element) -> str:
        """
        Extract news source
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            Source name
        """
        try:
            # Source search pattern
            source_span = element.find('span', {'class': 'news-source'})
            if source_span:
                return source_span.get_text(strip=True)
            
            # Source info inside parentheses
            text = element.get_text()
            if '(' in text and ')' in text:
                # Get the last parenthesized string as source
                parts = text.split('(')
                if len(parts) > 1:
                    source_part = parts[-1].split(')')[0]
                    return source_part.strip()
            
            return "Finviz"
            
        except Exception:
            return "Unknown"
    
    def _categorize_news(self, title: str) -> str:
        """
        Estimate category from news title.
        
        Args:
            title: News title
            
        Returns:
            Category name
        """
        title_lower = title.lower()
        
        # Keyword-based classification
        if any(word in title_lower for word in ['earnings', 'revenue', 'profit', 'eps', 'guidance']):
            return 'earnings'
        elif any(word in title_lower for word in ['upgrade', 'downgrade', 'rating', 'analyst', 'target']):
            return 'analyst'
        elif any(word in title_lower for word in ['insider', 'ceo', 'cfo', 'director', 'executive']):
            return 'insider'
        elif any(word in title_lower for word in ['merger', 'acquisition', 'deal', 'buyout']):
            return 'merger'
        elif any(word in title_lower for word in ['fda', 'approval', 'clinical', 'trial']):
            return 'regulatory'
        elif any(word in title_lower for word in ['dividend', 'split', 'buyback']):
            return 'corporate_action'
        else:
            return 'general'
    
    def _parse_news_from_csv(self, row: 'pd.Series', ticker: str, cutoff_date: datetime) -> Optional[NewsData]:
        """
        Create NewsData object from CSV row.
        
        Args:
            row: pandas Series (CSV row data)
            ticker: Target ticker
            cutoff_date: Cutoff datetime
            
        Returns:
            NewsData object or None
        """
        try:
            import pandas as pd
            
            # Extract required fields
            title = str(row.get('Title', ''))
            source = str(row.get('Source', ''))
            url = str(row.get('URL', ''))
            
            # Parse datetime
            date_str = str(row.get('Date', ''))
            news_date = self._parse_news_date_from_csv(date_str)
            
            if not news_date or news_date < cutoff_date:
                return None
            
            # Estimate category
            category = self._categorize_news(title)
            
            return NewsData(
                ticker=ticker,
                title=title,
                source=source,
                date=news_date,
                url=url,
                category=category
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse news data from CSV row: {e}")
            return None
    
    def _parse_news_date_from_csv(self, date_str: str) -> Optional[datetime]:
        """
        Convert CSV datetime string to datetime object.
        
        Args:
            date_str: Datetime string
            
        Returns:
            datetime object or None
        """
        if not date_str or date_str == '-':
            return None
        
        try:
            # Parse ISO format datetime
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Parse other formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date string: {date_str}")
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return None