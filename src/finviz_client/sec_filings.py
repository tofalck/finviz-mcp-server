import pandas as pd
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import requests

from .base import FinvizClient
from ..models import SECFilingData

logger = logging.getLogger(__name__)

class FinvizSECFilingsClient(FinvizClient):
    """Finviz SEC filings data client."""
    
    SEC_FILINGS_EXPORT_URL = f"{FinvizClient.BASE_URL}/export/latest-filings"
    
    def get_sec_filings(
        self,
        ticker: str,
        form_types: Optional[List[str]] = None,
        days_back: int = 30,
        max_results: int = 50,
        sort_by: str = "filing_date",
        sort_order: str = "desc"
    ) -> List[SECFilingData]:
        """
        Fetch SEC filings data for the specified stock.
        
        Args:
            ticker: Stock ticker
            form_types: Form type filter (e.g. ["10-K", "10-Q", "8-K"])
            days_back: Number of days back to fetch filings
            max_results: Maximum number of results
            sort_by: Sort criteria ("filing_date", "report_date", "form")
            sort_order: Sort order ("asc", "desc")
            
        Returns:
            SECFList of SECFilingData objects
        """
        try:
            # Build parameters
            # Convert sort_by to Finviz parameter name when filing_date
            finviz_sort_param = "filingDate" if sort_by == "filing_date" else sort_by
            params = {
                't': ticker,
                'o': f"-{finviz_sort_param}" if sort_order == "desc" else finviz_sort_param
            }
            
            # Add API key (use test key as default)
            if self.api_key:
                params['auth'] = self.api_key
            else:
                # Get API key from environment variable
                import os
                env_api_key = os.getenv('FINVIZ_API_KEY')
                if env_api_key:
                    params['auth'] = env_api_key
                else:
                    logger.error("No Finviz API key provided. Please set FINVIZ_API_KEY environment variable.")
                    raise ValueError("Finviz API key is required")
            
            # Fetch CSV data
            response = self._make_request(self.SEC_FILINGS_EXPORT_URL, params)
            
            # Parse CSV data
            filings_data = self._parse_sec_filings_csv(response.text, ticker)
            
            # Filtering
            if form_types:
                filings_data = [f for f in filings_data if f.form in form_types]
            
            # Date filtering
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filings_data = [
                f for f in filings_data 
                if self._parse_date(f.filing_date) >= cutoff_date
            ]
            
            # Max result limit
            if max_results and max_results > 0:
                filings_data = filings_data[:max_results]
            
            logger.info(f"Retrieved {len(filings_data)} SEC filings for {ticker}")
            return filings_data
            
        except Exception as e:
            logger.error(f"Error retrieving SEC filings for {ticker}: {e}")
            return []
    
    def get_recent_filings_by_form(
        self,
        ticker: str,
        form_type: str,
        limit: int = 10
    ) -> List[SECFilingData]:
        """
        Fetch latest filings for specific form type.
        
        Args:
            ticker: Stock ticker
            form_type: Form type (e.g. "10-K", "10-Q", "8-K")
            limit: Maximum number of items to retrieve
            
        Returns:
            SECFList of SECFilingData objects
        """
        return self.get_sec_filings(
            ticker=ticker,
            form_types=[form_type],
            days_back=365,  # 1 year
            max_results=limit,
            sort_by="filing_date",
            sort_order="desc"
        )
    
    def get_major_filings(
        self,
        ticker: str,
        days_back: int = 90
    ) -> List[SECFilingData]:
        """
        Fetch major form (10-K, 10-Q, 8-K) filings.
        
        Args:
            ticker: Stock ticker
            days_back: Number of days back
            
        Returns:
            SECFList of SECFilingData objects
        """
        major_forms = ["10-K", "10-Q", "8-K", "DEF 14A", "SC 13G", "SC 13D"]
        return self.get_sec_filings(
            ticker=ticker,
            form_types=major_forms,
            days_back=days_back,
            max_results=50,
            sort_by="filing_date",
            sort_order="desc"
        )
    
    def get_insider_filings(
        self,
        ticker: str,
        days_back: int = 30
    ) -> List[SECFilingData]:
        """
        Fetch insider trading filings (Form 4, etc.).
        
        Args:
            ticker: Stock ticker
            days_back: Number of days back
            
        Returns:
            SECFList of SECFilingData objects
        """
        insider_forms = ["3", "4", "5", "11-K"]
        return self.get_sec_filings(
            ticker=ticker,
            form_types=insider_forms,
            days_back=days_back,
            max_results=30,
            sort_by="filing_date",
            sort_order="desc"
        )
    
    def _parse_sec_filings_csv(self, csv_text: str, ticker: str) -> List[SECFilingData]:
        """
        CSVParse CSV format SEC filings data into a list of SECFilingData objects.
        
        Args:
            csv_text: CSV format text
            ticker: Stock ticker
            
        Returns:
            SECFList of SECFilingData objects
        """
        try:
            # Convert CSV text to DataFrame (enhanced error handling)
            from io import StringIO
            
            # Adjust CSV parameters to avoid errors
            df = pd.read_csv(
                StringIO(csv_text),
                on_bad_lines='skip',  # Skip malformed rows
                dtype=str,  # Read all as strings
                na_filter=False  # Disable NA filter
            )
            
            logger.info(f"Successfully parsed CSV with {len(df)} rows")
            
            filings = []
            for idx, row in df.iterrows():
                try:
                    # Safely fetch data (set default values)
                    filing_date = str(row.get('Filing Date', '')).strip()
                    report_date = str(row.get('Report Date', '')).strip()
                    form = str(row.get('Form', '')).strip()
                    description = str(row.get('Description', '')).strip()
                    filing_url = str(row.get('Filing', '')).strip()
                    document_url = str(row.get('Document', '')).strip()
                    
                    # Validate required fields
                    if not filing_date or not form:
                        logger.warning(f"Skipping row {idx}: missing required fields")
                        continue
                    
                    filing = SECFilingData(
                        ticker=ticker,
                        filing_date=filing_date,
                        report_date=report_date if report_date else filing_date,
                        form=form,
                        description=description if description else f"{form} filing",
                        filing_url=filing_url,
                        document_url=document_url
                    )
                    filings.append(filing)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse filing row {idx}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(filings)} filings for {ticker}")
            return filings
            
        except Exception as e:
            logger.error(f"Error parsing SEC filings CSV: {e}")
            # Log CSV text preview for debugging
            csv_preview = csv_text[:500] if csv_text else "Empty CSV"
            logger.debug(f"CSV preview: {csv_preview}")
            return []
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Convert date string to datetime object.
        
        Args:
            date_str: Date string
            
        Returns:
            datetime object
        """
        try:
            # Assume MM/DD/YY format
            return datetime.strptime(date_str, '%m/%d/%y')
        except ValueError:
            try:
                # Also try YYYY-MM-DD format
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                # Return current datetime if unparseable
                logger.warning(f"Could not parse date: {date_str}")
                return datetime.now()
    
    def get_filing_summary(
        self,
        ticker: str,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Get filings summary for the specified period.
        
        Args:
            ticker: Stock ticker
            days_back: Number of days back
            
        Returns:
            Filing summary dictionary
        """
        try:
            filings = self.get_sec_filings(
                ticker, 
                days_back=days_back, 
                max_results=100,
                sort_by="filing_date",
                sort_order="desc"
            )
            
            if not filings:
                return {"ticker": ticker, "total_filings": 0, "forms": {}}
            
            # Aggregate by form type
            form_counts = {}
            for filing in filings:
                form_type = filing.form
                if form_type not in form_counts:
                    form_counts[form_type] = 0
                form_counts[form_type] += 1
            
            # Latest filing date
            latest_filing = max(filings, key=lambda x: self._parse_date(x.filing_date))
            
            summary = {
                "ticker": ticker,
                "total_filings": len(filings),
                "forms": form_counts,
                "latest_filing_date": latest_filing.filing_date,
                "latest_filing_form": latest_filing.form,
                "period_days": days_back
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating filing summary for {ticker}: {e}")
            return {"ticker": ticker, "error": str(e)}
