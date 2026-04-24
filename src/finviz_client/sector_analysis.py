import logging
from typing import List, Optional, Dict, Any
import pandas as pd
import os

from .base import FinvizClient
from ..models import SectorPerformance

logger = logging.getLogger(__name__)

class FinvizSectorAnalysisClient(FinvizClient):
    """Dedicated client for Finviz sector and industry analysis."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
    
    def get_sector_performance(self, timeframe: str = "1d", 
                             sectors: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Sector performance analysis (using CSV export).
        
        Args:
            timeframe: Analysis period (1d, 1w, 1m, 3m, 6m, 1y) - currently ignored
            sectors: Target sectors (None = all sectors)
            
        Returns:
            List of SectorPerformance objects
        """
        try:
            # Fetch basic sector data (adding v=152 parameter)
            params = {
                'g': 'sector',
                'v': '152'  # Correct view format
            }
            
            # API key (same handling as base.py)
            if self.api_key:
                params['auth'] = self.api_key
            else:
                # Get API key from environment variable
                env_api_key = os.getenv('FINVIZ_API_KEY')
                if env_api_key:
                    params['auth'] = env_api_key
                else:
                    logger.error("No Finviz API key provided. Please set FINVIZ_API_KEY environment variable.")
                    raise ValueError("Finviz API key is required")
            
            # Fetch sector performance data from CSV
            df = self._fetch_csv_from_url(self.GROUPS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning("No sector performance data returned")
                return []
            
            # Convert CSV data to list of SectorPerformance objects
            sector_data = []
            for _, row in df.iterrows():
                try:
                    sector_perf = self._parse_sector_performance_from_csv(row)
                    if sector_perf:
                        sector_data.append(sector_perf)
                except Exception as e:
                    logger.warning(f"Failed to parse sector performance from CSV: {e}")
                    continue
            
            # Sector filtering
            if sectors:
                sector_data = [s for s in sector_data if s.get('name') in sectors]
            
            logger.info(f"Retrieved performance data for {len(sector_data)} sectors")
            return sector_data
            
        except Exception as e:
            logger.error(f"Error retrieving sector performance: {e}")
            return []
    
    def get_industry_performance(self, industries: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Industry performance analysis (using CSV export).
        
        Args:
            industries: Target industries (None = all industries)
            
        Returns:
            List of industry performance data
        """
        try:
            params = {
                'g': 'industry',
                'v': '152',  # Fixed value
                'o': 'name',  # Sort order
                'c': '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26'  # All columns
            }
            
            # Fetch industry performance data from CSV
            df = self._fetch_csv_from_url(self.GROUPS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning("No industry performance data returned")
                return []
            
            # Convert CSV data to list of industry performance data
            industry_data = []
            for _, row in df.iterrows():
                try:
                    industry_perf = self._parse_industry_performance_from_csv(row)
                    if industry_perf:
                        industry_data.append(industry_perf)
                except Exception as e:
                    logger.warning(f"Failed to parse industry performance from CSV: {e}")
                    continue
                    
            # Industry filtering
            if industries:
                industry_data = [i for i in industry_data if i.get('industry') in industries]
            
            logger.info(f"Retrieved performance data for {len(industry_data)} industries")
            return industry_data
            
        except Exception as e:
            logger.error(f"Error retrieving industry performance: {e}")
            return []
    
    def get_country_performance(self, countries: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Country market performance analysis (using CSV export).
        
        Args:
            countries: Target countries (None = all)
            
        Returns:
            List of country performance data
        """
        try:
            params = {
                'g': 'country',
                'v': '152',  # Fixed value
                'o': 'name',  # Sort order
                'c': '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26'  # All columns
            }
            
            # Fetch country performance data from CSV
            df = self._fetch_csv_from_url(self.GROUPS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning("No country performance data returned")
                return []
            
            # Convert CSV data to list of country performance data
            country_data = []
            for _, row in df.iterrows():
                try:
                    country_perf = self._parse_country_performance_from_csv(row)
                    if country_perf:
                        country_data.append(country_perf)
                except Exception as e:
                    logger.warning(f"Failed to parse country performance from CSV: {e}")
                    continue
            
            # Country filtering
            if countries:
                country_data = [c for c in country_data if c.get('country') in countries]
            
            logger.info(f"Retrieved performance data for {len(country_data)} countries")
            return country_data
            
        except Exception as e:
            logger.error(f"Error retrieving country performance: {e}")
            return []
    
    def get_sector_specific_industry_performance(self, sector: str) -> List[Dict[str, Any]]:
        """
        Industry performance analysis within a specific sector.
        
        Args:
            sector: Sector name (basicmaterials, communicationservices, consumercyclical, etc.)
            
        Returns:
            List of industry performance data
        """
        try:
            # Normalize sector name
            sector_mapping = {
                'basicmaterials': 'basicmaterials',
                'basic_materials': 'basicmaterials',
                'communicationservices': 'communicationservices',
                'communication_services': 'communicationservices',
                'consumercyclical': 'consumercyclical',
                'consumer_cyclical': 'consumercyclical',
                'consumerdefensive': 'consumerdefensive',
                'consumer_defensive': 'consumerdefensive',
                'energy': 'energy',
                'financial': 'financial',
                'healthcare': 'healthcare',
                'industrials': 'industrials',
                'realestate': 'realestate',
                'real_estate': 'realestate',
                'technology': 'technology',
                'utilities': 'utilities'
            }
            
            sector_code = sector_mapping.get(sector.lower(), sector.lower())
            
            params = {
                'g': 'industry',
                'sg': sector_code,
                'v': '152',  # Fixed value
                'o': 'name',  # Sort order
                'c': '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26'  # All columns
            }
            
            # Fetch sector-specific industry performance data from CSV
            df = self._fetch_csv_from_url(self.GROUPS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning(f"No industry performance data returned for sector {sector}")
                return []
            
            # Convert CSV data to list of industry performance data
            industry_data = []
            for _, row in df.iterrows():
                try:
                    industry_perf = self._parse_industry_performance_from_csv(row)
                    if industry_perf:
                        # Add sector info
                        industry_perf['parent_sector'] = sector
                        industry_data.append(industry_perf)
                except Exception as e:
                    logger.warning(f"Failed to parse sector-specific industry performance from CSV: {e}")
                    continue
            
            logger.info(f"Retrieved performance data for {len(industry_data)} industries in {sector} sector")
            return industry_data
            
        except Exception as e:
            logger.error(f"Error retrieving sector-specific industry performance: {e}")
            return []

    def get_capitalization_performance(self) -> List[Dict[str, Any]]:
        """
        Market cap performance analysis.
        
        Returns:
            List of market cap performance data
        """
        try:
            params = {
                'g': 'capitalization',
                'v': '152',  # Fixed value
                'o': 'name',  # Sort order
                'c': '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26'  # All columns
            }
            
            # Fetch market cap performance data from CSV
            df = self._fetch_csv_from_url(self.GROUPS_EXPORT_URL, params)
            
            if df.empty:
                logger.warning("No capitalization performance data returned")
                return []
            
            # CSV data to list of market cap performance data
            cap_data = []
            for _, row in df.iterrows():
                try:
                    cap_perf = self._parse_capitalization_performance_from_csv(row)
                    if cap_perf:
                        cap_data.append(cap_perf)
                except Exception as e:
                    logger.warning(f"Failed to parse capitalization performance from CSV: {e}")
                    continue
            
            logger.info(f"Retrieved performance data for {len(cap_data)} capitalization categories")
            return cap_data
            
        except Exception as e:
            logger.error(f"Error retrieving capitalization performance: {e}")
            return []


    
    def _parse_sector_performance_from_csv(self, row: 'pd.Series') -> Optional[Dict[str, Any]]:
        """
        Create sector performance data from CSV row.
        
        Args:
            row: pandas Series (CSV row data)
            
        Returns:
            Sector performance data dict or None
        """
        try:
            import pandas as pd
            
            sector_name = str(row.get('Name', ''))
            if not sector_name:
                return None
            
            return {
                'name': sector_name,
                'market_cap': str(row.get('Market Cap', 'N/A')),
                'pe_ratio': str(row.get('P/E', 'N/A')),
                'dividend_yield': str(row.get('Dividend Yield', 'N/A')),
                'change': str(row.get('Change', 'N/A')),
                'stocks': str(row.get('Stocks', 'N/A'))
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse sector performance from CSV row: {e}")
            return None
    
    def _parse_industry_performance_from_csv(self, row: 'pd.Series') -> Optional[Dict[str, Any]]:
        """
        Create industry performance data from CSV row.
        
        Args:
            row: pandas Series (CSV row data)
            
        Returns:
            Industry performance data dict or None
        """
        try:
            import pandas as pd
            
            industry_name = str(row.get('Industry', ''))
            if not industry_name:
                return None
            
            return {
                'industry': industry_name,
                'performance_1d': self._safe_parse_percentage(row.get('1D %', 0)),
                'performance_1w': self._safe_parse_percentage(row.get('1W %', 0)),
                'performance_1m': self._safe_parse_percentage(row.get('1M %', 0)),
                'performance_3m': self._safe_parse_percentage(row.get('3M %', 0)),
                'performance_6m': self._safe_parse_percentage(row.get('6M %', 0)),
                'performance_1y': self._safe_parse_percentage(row.get('1Y %', 0)),
                'stock_count': self._safe_parse_number(row.get('Stocks', 0))
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse industry performance from CSV row: {e}")
            return None
    
    def _parse_country_performance_from_csv(self, row: 'pd.Series') -> Optional[Dict[str, Any]]:
        """
        Create country performance data from CSV row.
        
        Args:
            row: pandas Series (CSV row data)
            
        Returns:
            Country performance data dict or None
        """
        try:
            import pandas as pd
            
            country_name = str(row.get('Country', ''))
            if not country_name:
                return None
            
            return {
                'country': country_name,
                'performance_1d': self._safe_parse_percentage(row.get('1D %', 0)),
                'performance_1w': self._safe_parse_percentage(row.get('1W %', 0)),
                'performance_1m': self._safe_parse_percentage(row.get('1M %', 0)),
                'performance_3m': self._safe_parse_percentage(row.get('3M %', 0)),
                'performance_6m': self._safe_parse_percentage(row.get('6M %', 0)),
                'performance_1y': self._safe_parse_percentage(row.get('1Y %', 0)),
                'stock_count': self._safe_parse_number(row.get('Stocks', 0))
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse country performance from CSV row: {e}")
            return None
    
    def _safe_parse_percentage(self, value) -> float:
        """
        Safely parse a percentage value.
        
        Args:
            value: Percentage value
            
        Returns:
            float value
        """
        if value is None or str(value) in ['-', 'N/A', 'nan', '']:
            return 0.0
        
        try:
            if isinstance(value, str):
                # Remove percent sign and convert to number
                cleaned_value = value.replace('%', '').strip()
                return float(cleaned_value)
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_capitalization_performance_from_csv(self, row: 'pd.Series') -> Optional[Dict[str, Any]]:
        """
        CSCreate market cap performance data from CSV row.
        
        Args:
            row: pandas Series (CSV row data)
            
        Returns:
            Market cap performance data dict or None
        """
        try:
            import pandas as pd
            
            cap_name = str(row.get('Name', ''))
            if not cap_name:
                return None
            
            return {
                'capitalization': cap_name,
                'market_cap': str(row.get('Market Cap', 'N/A')),
                'pe_ratio': str(row.get('P/E', 'N/A')),
                'dividend_yield': str(row.get('Dividend Yield', 'N/A')),
                'change': str(row.get('Change', 'N/A')),
                'stocks': str(row.get('Stocks', 'N/A'))
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse capitalization performance from CSV row: {e}")
            return None

    def _safe_parse_number(self, value) -> int:
        """
        Safely parse a numeric value.
        
        Args:
            value: Numeric value
            
        Returns:
            int value
        """
        if value is None or str(value) in ['-', 'N/A', 'nan', '']:
            return 0
        
        try:
            if isinstance(value, str):
                # Remove commas and convert to number
                cleaned_value = value.replace(',', '').strip()
                return int(float(cleaned_value))
            return int(value)
        except (ValueError, TypeError):
            return 0