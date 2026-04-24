import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

from .base import FinvizClient
from ..models import StockData, ScreeningResult, UpcomingEarningsData, MARKET_CAP_FILTERS

logger = logging.getLogger(__name__)

class FinvizScreener(FinvizClient):
    """Dedicated Finviz screening client."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
    
    def earnings_screener(self, **kwargs) -> List[StockData]:
        """
        Screen for stocks with upcoming earnings dates.
        
        Args:
            earnings_date: Earnings date filter
            market_cap: Market cap filter
            min_price: Minimum price
            max_price: Maximum price
            min_volume: Minimum volume
            sectors: Target sectors
            premarket_price_change: Pre-market price change filter
            afterhours_price_change: After-hours price change filter
            
        Returns:
            List of StockData objects
        """
        filters = self._build_earnings_filters(**kwargs)
        return self.screen_stocks(filters)
    
    def volume_surge_screener(self) -> List[StockData]:
        """
        Screen for stocks with surging volume (fixed criteria).
        
        Fixed filter criteria (not configurable):
        f=cap_smallover,ind_stocksonly,sh_avgvol_o100,sh_price_o10,sh_relvol_o1.5,ta_change_u2,ta_sma200_pa&ft=4&o=-change&ar=10
        
        - Market cap: Small+ ($300M+)
        - Stocks only: No ETFs
        - Average volume: 100,000+
        - Price: $10+
        - Relative volume: 1.5x+
        - Price change: 2%+ up
        - Above 200-day moving average
        - Sorted by price change descending
        - Max results: 10
            
        Returns:
            List of StockData objects
        """
        filters = self._build_volume_surge_filters()
        results = self.screen_stocks(filters)
        
        # Fixed sort (price change descending)
        results.sort(key=lambda x: x.price_change or 0, reverse=True)
        
        # Return all results (no limit)
        return results
    
    def uptrend_screener(self) -> List[StockData]:
        """
        Screen for stocks in an uptrend (fixed criteria).
        
        Fixed filter criteria (not configurable):
        f=cap_microover,sh_avgvol_o100,sh_price_o10,ta_highlow52w_a30h,ta_perf2_4wup,ta_sma20_pa,ta_sma200_pa,ta_sma50_sa200&ft=4&o=-epsyoy1
        
        - Market cap: Micro+ ($50M+)
        - Average volume: 100K+
        - Price: $10+
        - Within 30% of 52-week high
        - 4-week performance up
        - Above 20-day moving average
        - Above 200-day moving average
        - 50-day MA above 200-day MA
        - Stocks only
        - Sorted by EPS growth (YoY) descending
            
        Returns:
            List of StockData objects
        """
        filters = self._build_uptrend_filters()
        results = self.screen_stocks(filters)
        
        # Already sorted by Finviz, return as-is
        return results
    
    def dividend_growth_screener(self, **kwargs) -> List[StockData]:
        """
        Screen for dividend growth stocks.
        
        Args:
            min_dividend_yield: Minimum dividend yield
            max_dividend_yield: Maximum dividend yield
            min_dividend_growth: Minimum dividend growth rate
            min_payout_ratio: Minimum payout ratio
            max_payout_ratio: Maximum payout ratio
            min_roe: Minimum ROE
            max_debt_equity: Maximum debt-to-equity ratio
            max_results: Maximum number of results
            
        Returns:
            List of StockData objects
        """
        filters = self._build_dividend_growth_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # Limit and sort results
        max_results = kwargs.get('max_results', 100)
        sort_by = kwargs.get('sort_by', 'dividend_yield')
        sort_order = kwargs.get('sort_order', 'desc')
        
        # Sort processing
        if sort_by == 'dividend_yield':
            results.sort(key=lambda x: x.dividend_yield or 0, reverse=(sort_order == 'desc'))
        elif sort_by == 'market_cap':
            results.sort(key=lambda x: x.market_cap or 0, reverse=(sort_order == 'desc'))
        
        return results[:max_results]
    
    def etf_screener(self, **kwargs) -> List[StockData]:
        """
        Screen ETFs by strategy.
        
        Args:
            strategy_type: Strategy type
            asset_class: Asset class
            min_aum: Minimum AUM
            max_expense_ratio: Maximum expense ratio
            max_results: Maximum number of results
            
        Returns:
            List of StockData objects
        """
        filters = self._build_etf_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # Limit and sort results
        max_results = kwargs.get('max_results', 50)
        sort_by = kwargs.get('sort_by', 'aum')
        sort_order = kwargs.get('sort_order', 'desc')
        
        # Sort processing
        if sort_by == 'aum':
            results.sort(key=lambda x: x.aum or 0, reverse=(sort_order == 'desc'))
        elif sort_by == 'expense_ratio':
            results.sort(key=lambda x: x.net_expense_ratio or 0, reverse=(sort_order == 'asc'))
        
        return results[:max_results]
    
    def earnings_premarket_screener(self) -> List[StockData]:
        """
        Screen for stocks rising on pre-market earnings (fixed criteria).
        
        Fixed filter criteria (not configurable):
        f=cap_smallover,earningsdate_todaybefore,sh_avgvol_o100,sh_price_o10,ta_change_u2&ft=4&o=-change
        
        Returns:
            List of StockData objects
        """
        filters = self._build_earnings_premarket_filters()
        results = self.screen_stocks(filters)
        
        # Fixed sort (price change descending)
        results.sort(key=lambda x: x.price_change or 0, reverse=True)
        
        return results
    
    def earnings_afterhours_screener(self) -> List[StockData]:
        """
        Screen for stocks rising in after-hours trading after earnings (fixed criteria).
        
        Fixed filter criteria (not configurable):
        f=ah_change_u2,cap_smallover,earningsdate_todayafter,sh_avgvol_o100,sh_price_o30&ft=4&o=-afterchange&ar=60
        
        Returns:
            List of StockData objects
        """
        filters = self._build_earnings_afterhours_filters()
        results = self.screen_stocks(filters)
        
        # Fixed sort (after-hours change descending)
        results.sort(key=lambda x: x.afterhours_change_percent or 0, reverse=True)
        
        # Fixed result count (60)
        return results[:60]
    
    def earnings_trading_screener(self) -> List[StockData]:
        """
        Screen for earnings trade candidates (fixed criteria).
        
        Fixed filters: f=cap_smallover,earningsdate_yesterdayafter|todaybefore,fa_epsrev_ep,sh_avgvol_o200,sh_price_o10,ta_change_u,ta_perf_0to-4w,ta_volatility_1tox&ft=4&o=-epssurprise&ar=60

        Returns:
            List of StockData objects
        """
        filters = self._build_earnings_trading_filters()
        results = self.screen_stocks(filters)
        
        # Sort by EPS surprise descending (fixed)
        results.sort(key=lambda x: x.eps_surprise or 0, reverse=True)
        
        # Max 60 results (fixed)
        return results[:60]
    
    def earnings_positive_surprise_screener(self, **kwargs) -> List[StockData]:
        """
        Screen for this-week earnings stocks with positive surprise and price gain.
        
        Returns:
            List of StockData objects
        """
        filters = self._build_earnings_positive_surprise_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # Sort and limit
        max_results = kwargs.get('max_results', 50)
        sort_by = kwargs.get('sort_by', 'eps_qoq_growth')
        
        if sort_by == 'eps_qoq_growth':
            results.sort(key=lambda x: x.eps_growth_qtr or 0, reverse=True)
        elif sort_by == 'performance_1w':
            results.sort(key=lambda x: x.performance_1w or 0, reverse=True)
        
        return results[:max_results]
    
    def trend_reversion_screener(self, **kwargs) -> List[StockData]:
        """
        Screen for trend reversion candidates.
        
        Args:
            market_cap: Market cap filter
            eps_growth_qoq: Minimum EPS growth QoQ
            revenue_growth_qoq: Minimum revenue growth QoQ
            rsi_max: Maximum RSI
            sectors: Target sectors
            exclude_sectors: Sectors to exclude
            max_results: Maximum number of results
            
        Returns:
            List of StockData objects
        """
        filters = self._build_trend_reversion_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # Limit and sort results
        max_results = kwargs.get('max_results', 50)
        sort_by = kwargs.get('sort_by', 'rsi')
        sort_order = kwargs.get('sort_order', 'asc')  # RSI ascending (lowest first)
        
        # Sort processing
        if sort_by == 'rsi':
            results.sort(key=lambda x: x.rsi or 0, reverse=(sort_order == 'desc'))
        elif sort_by == 'eps_growth_qoq':
            results.sort(key=lambda x: x.eps_growth_qtr or 0, reverse=(sort_order == 'desc'))
        
        return results[:max_results]
    
    def get_relative_volume_stocks(self, **kwargs) -> List[StockData]:
        """
        Detect stocks with unusual relative volume.
        
        Args:
            min_relative_volume: Minimum relative volume
            min_price: Minimum price
            sectors: Target sectors
            max_results: Maximum number of results
            
        Returns:
            List of StockData objects
        """
        filters = self._build_relative_volume_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # Sort by relative volume
        results.sort(key=lambda x: x.relative_volume or 0, reverse=True)
        
        max_results = kwargs.get('max_results', 50)
        return results[:max_results]
    
    def technical_analysis_screener(self, **kwargs) -> List[StockData]:
        """
        Technical analysis-based screening.
        
        Args:
            rsi_min: Minimum RSI
            rsi_max: Maximum RSI
            price_vs_sma20: Relationship to 20-day moving average
            price_vs_sma50: Relationship to 50-day moving average
            price_vs_sma200: Relationship to 200-day moving average
            min_price: Minimum price
            min_volume: Minimum volume
            sectors: Target sectors
            max_results: Maximum number of results
            
        Returns:
            List of StockData objects
        """
        filters = self._build_technical_analysis_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        max_results = kwargs.get('max_results', 50)
        return results[:max_results]
    
    def _build_earnings_filters(self, **kwargs) -> Dict[str, Any]:
        """Build filters for earnings screening."""
        filters = {}
        
        # Earnings date
        if 'earnings_date' in kwargs:
            filters['earnings_date'] = kwargs['earnings_date']
        
        # Market cap
        if 'market_cap' in kwargs:
            filters['market_cap'] = kwargs['market_cap']
        
        # Price range
        if 'min_price' in kwargs:
            filters['price_min'] = kwargs['min_price']
        if 'max_price' in kwargs:
            filters['price_max'] = kwargs['max_price']
        
        # Volume
        if 'min_volume' in kwargs:
            filters['volume_min'] = kwargs['min_volume']
        
        # Sector
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        return filters
    
    def _build_volume_surge_filters(self) -> Dict[str, Any]:
        """
        Build filters for volume surge screening (fixed criteria).
        
        Fixed filter criteria (not configurable):
        f=cap_smallover,ind_stocksonly,sh_avgvol_o100,sh_price_o10,sh_relvol_o1.5,ta_change_u2,ta_sma200_pa&ft=4&o=-change
        
        - Market cap: Small+ ($300M+)
        - Stocks only
        - Average volume: 100,000+
        - Price: $10+
        - Relative volume: 1.5x+
        - Price change: 2%+ up
        - Above 200-day moving average
        - Sorted by price change descending
        - No limit on results
        """
        filters = {}
        
        # Set fixed criteria
        # Market cap: Small+
        filters['market_cap'] = 'smallover'
        
        # Average volume: 100,000+
        filters['avg_volume_min'] = 100000
        
        # Price: $10+
        filters['price_min'] = 10.0
        
        # Relative volume: 1.5x+
        filters['relative_volume_min'] = 1.5
        
        # Price change: 2%+ up
        filters['price_change_min'] = 2.0
        
        # Above 200-day moving average
        filters['sma200_above'] = True
        
        # Sort condition (price change descending)
        filters['sort_by'] = 'price_change'
        filters['sort_order'] = 'desc'
        
        # Stocks only (no ETFs)
        filters['stocks_only'] = True
        
        # No result limit
        # filters['max_results'] = removed
        
        return filters
    
    def _build_uptrend_filters(self) -> Dict[str, Any]:
        """
        Build uptrend filters (fixed criteria).
        
        Fixed filter criteria (not configurable):
        f=cap_microover,sh_avgvol_o100,sh_price_o10,ta_highlow52w_a30h,ta_perf2_4wup,ta_sma20_pa,ta_sma200_pa,ta_sma50_sa200&ft=4&o=-epsyoy1
        
        - Market cap: Micro+ ($50M+)
        - Average volume: 100K+
        - Price: $10+
        - Within 30% of 52-week high
        - 4-week performance up
        - Above 20-day moving average
        - Above 200-day moving average
        - 50-day MA above 200-day MA
        - Stocks only
        - Sorted by EPS growth (YoY) descending
        """
        filters = {}
        
        # Set default criteria (aligned with Finviz recommendations)
        # Market cap: Micro+ (updated)
        filters['market_cap'] = 'microover'
        
        # Average volume: 100K+ (updated: 100000 → 100)
        filters['avg_volume_min'] = 100
        
        # Price: 10+ (remove decimal)
        filters['price_min'] = 10
        
        # Within 30% of 52-week high (remove decimal)
        filters['near_52w_high'] = 30
        
        # 4-week performance up (new)
        filters['performance_4w_positive'] = True
        
        # Moving average conditions
        filters['sma20_above'] = True
        filters['sma200_above'] = True
        filters['sma50_above_sma200'] = True
        
        # Sort condition (EPS YoY growth descending, corrected)
        filters['sort_by'] = 'eps_growth_yoy'
        filters['sort_order'] = 'desc'
        
        # Stocks only (no ETFs)
        filters['stocks_only'] = True
        
        return filters
    
    def _build_dividend_growth_filters(self, **kwargs) -> Dict[str, Any]:
        """
        Build dividend growth filters.
        
        Default criteria:
        - Market cap: Mid+ (cap_midover)
        - Dividend yield: 2%+ (fa_div_o2)
        - EPS 5-year growth: Positive (fa_eps5years_pos)
        - EPS QoQ growth: Positive (fa_epsqoq_pos)
        - EPS YoY growth: Positive (fa_epsyoy_pos)
        - P/B ratio: Under 5 (fa_pb_u5)
        - P/E ratio: Under 30 (fa_pe_u30)
        - Sales 5-year growth: Positive (fa_sales5years_pos)
        - Sales QoQ growth: Positive (fa_salesqoq_pos)
        - Region: USA (geo_usa)
        - Stocks only (ft=4)
        - Sorted by 200-day SMA (o=sma200)
        """
        filters = {}
        
        # Set default criteria
        # Market cap: Mid+
        filters['market_cap'] = kwargs.get('market_cap', 'midover')
        
        # Dividend yield: 2%+
        filters['dividend_yield_min'] = kwargs.get('min_dividend_yield', 2.0)
        
        # EPS growth criteria
        filters['eps_growth_5y_positive'] = kwargs.get('eps_growth_5y_positive', True)
        filters['eps_growth_qoq_positive'] = kwargs.get('eps_growth_qoq_positive', True)
        filters['eps_growth_yoy_positive'] = kwargs.get('eps_growth_yoy_positive', True)
        
        # Valuation criteria
        filters['pb_ratio_max'] = kwargs.get('max_pb_ratio', 5.0)
        filters['pe_ratio_max'] = kwargs.get('max_pe_ratio', 30.0)
        
        # Sales growth criteria
        filters['sales_growth_5y_positive'] = kwargs.get('sales_growth_5y_positive', True)
        filters['sales_growth_qoq_positive'] = kwargs.get('sales_growth_qoq_positive', True)
        
        # Region: USA
        filters['country'] = kwargs.get('country', 'USA')
        
        # Stocks only
        filters['stocks_only'] = kwargs.get('stocks_only', True)
        
        # Sort condition (200-day SMA)
        filters['sort_by'] = kwargs.get('sort_by', 'sma200')
        filters['sort_order'] = kwargs.get('sort_order', 'asc')
        
        # Additional criteria if provided
        if 'max_dividend_yield' in kwargs:
            filters['dividend_yield_max'] = kwargs['max_dividend_yield']
        
        if 'min_dividend_growth' in kwargs:
            filters['dividend_growth_min'] = kwargs['min_dividend_growth']
        
        if 'min_payout_ratio' in kwargs:
            filters['payout_ratio_min'] = kwargs['min_payout_ratio']
        
        if 'max_payout_ratio' in kwargs:
            filters['payout_ratio_max'] = kwargs['max_payout_ratio']
        
        if 'min_roe' in kwargs:
            filters['roe_min'] = kwargs['min_roe']
        
        if 'max_debt_equity' in kwargs:
            filters['debt_equity_max'] = kwargs['max_debt_equity']
        
        return filters
    
    def _build_etf_filters(self, **kwargs) -> Dict[str, Any]:
        """Build ETF filters."""
        filters = {}
        
        strategy_type = kwargs.get('strategy_type', 'long')
        asset_class = kwargs.get('asset_class', 'equity')
        
        filters['instrument_type'] = 'etf'
        
        if 'min_aum' in kwargs:
            filters['aum_min'] = kwargs['min_aum']
        if 'max_expense_ratio' in kwargs:
            filters['expense_ratio_max'] = kwargs['max_expense_ratio']
        
        return filters
    
    def _build_earnings_premarket_filters(self) -> Dict[str, Any]:
        """
        Build pre-market earnings filters.
        
        Default criteria:
        - Market cap: Small+ (cap_smallover)
        - Earnings date: Today before open (earningsdate_todaybefore)
        - Average volume: 100K+ (sh_avgvol_o100)
        - Price: $10+ (sh_price_o10)
        - Price change: 2%+ up (ta_change_u2)
        - Stocks only (ft=4)
        - Sort by price change descending (o=-change)
        - Max results: 60 (ar=60)
        """
        filters = {}
        
        # Set default criteria
        # Earnings timing: Today before open
        filters['earnings_date'] = 'today_before'
        
        # Market cap: Small+
        filters['market_cap'] = 'smallover'
        
        # Average volume: 100K+
        filters['avg_volume_min'] = 100000
        
        # Price: $10+
        filters['price_min'] = 10.0
        
        # Price change: 2%+ up
        filters['price_change_min'] = 2.0
        
        # Stocks only
        filters['stocks_only'] = True
        
        # Sort condition (price change descending)
        filters['sort_by'] = 'price_change'
        filters['sort_order'] = 'desc'
        
        # Max results
        filters['max_results'] = 60
        
        return filters
    
    def _build_earnings_afterhours_filters(self) -> Dict[str, Any]:
        """
        Build after-hours earnings filters.
        
        Default criteria:
        - After-hours change: 2%+ up (ah_change_u2)
        - Market cap: Small+ (cap_smallover)
        - Earnings date: Today after close (earningsdate_todayafter)
        - Average volume: 100K+ (sh_avgvol_o100)
        - Price: $10+ (sh_price_o10)
        - Stocks only (ft=4)
        - Sort by after-hours change descending (o=-afterchange)
        - Max results: 60 (ar=60)
        """
        filters = {}
        
        # Set default criteria
        # Earnings timing: Today after close
        filters['earnings_date'] = 'today_after'
        
        # Market cap: Small+
        filters['market_cap'] = 'smallover'
        
        # Average volume: 100K+
        filters['avg_volume_min'] = 100000
        
        # Price: $10+
        filters['price_min'] = 10.0
        
        # After-hours change: 2%+ up
        filters['afterhours_change_min'] = 2.0
        
        # Stocks only
        filters['stocks_only'] = True
        
        # Sort condition (after-hours change descending)
        filters['sort_by'] = 'afterhours_change'
        filters['sort_order'] = 'desc'
        
        # Max results
        filters['max_results'] = 60
        
        return filters
    
    def _build_earnings_trading_filters(self) -> Dict[str, Any]:
        """
        Build earnings trading filters (fixed criteria).
        
        Fixed filters: f=cap_midover,earningsdate_yesterdayafter|todaybefore,fa_epsrev_ep,fa_netmargin_3to,sh_avgvol_o200,sh_price_o30,ta_change_u,ta_perf_0to-4w&ft=4&o=-epssurprise&ar=60
        
        Fixed criteria:
        - Market cap: Mid+ (cap_midover)
        - Earnings date: Yesterday after close or today before open (earningsdate_yesterdayafter|todaybefore)
        - EPS estimate: Upward revision (fa_epsrev_ep)
        - Net margin: 3%+ (fa_netmargin_3to)
        - Average volume: 200K+ (sh_avgvol_o200)
        - Price: $30+ (sh_price_o30)
        - Price change: Up (ta_change_u)
        - 4-week performance: Month Above 0% (ta_perf_0to-4w)
        - Stocks only (ft=4)
        - Sorted by EPS surprise descending (o=-epssurprise)
        - Max results: 60 (ar=60)
        """
        # Set fixed criteria
        filters = {
            # Earnings period: Yesterday after close or today before open
            'earnings_recent': True,
            
            # Market cap: Mid+
            'market_cap': 'midover',
            
            # EPS estimate: Upward revision
            'earnings_revision_positive': True,
            
            # Net margin: 3%+
            'net_margin_min': 3.0,
            
            # Average volume: 200K+
            'avg_volume_min': 200000,
            
            # Price: $30+
            'price_min': 30.0,
            
            # Price change: Up
            'price_change_positive': True,
            
            # 4-week performance: Month Above 0%
            'performance_4w_range': '0_to_negative_4w',
            
            # Stocks only
            'stocks_only': True,
            
            # Sort condition (EPS surprise descending)
            'sort_by': 'eps_surprise',
            'sort_order': 'desc',
            
            # Max results
            'max_results': 60,
            
            # Identifier for earnings_trading_screener
            'screener_type': 'earnings_trading'
        }
        
        return filters
    
    def _build_earnings_positive_surprise_filters(self, **kwargs) -> Dict[str, Any]:
        """Build positive earnings surprise filters."""
        filters = {}
        
        filters['earnings_date'] = 'this_week'
        
        filters['market_cap'] = 'smallover'
        
        if 'min_price' in kwargs:
            filters['price_min'] = kwargs['min_price']
        
        # Growth filter
        growth_criteria = kwargs.get('growth_criteria', {})
        if growth_criteria.get('min_eps_qoq_growth'):
            filters['eps_growth_min'] = growth_criteria['min_eps_qoq_growth']
        
        # Performance filter
        performance_criteria = kwargs.get('performance_criteria', {})
        if performance_criteria.get('above_sma200'):
            filters['sma200_above'] = True
        
        return filters
    
    def upcoming_earnings_screener(self, **kwargs) -> List[UpcomingEarningsData]:
        """
        Screen for next-week earnings stocks.
        
        Args:
            earnings_period: Earnings period ('next_week', 'next_2_weeks', 'next_month')
            market_cap: Market cap filter
            min_price: Minimum price
            min_avg_volume: Minimum average volume
            target_sectors: Target sectors
            max_results: Maximum number of results
            sort_by: Sort field
            sort_order: Sort order
        
        Returns:
            List of UpcomingEarningsData objects
        """
        try:
            # Build filters
            filters = self._build_upcoming_earnings_filters(**kwargs)
            
            # Fetch data from Finviz
            raw_results = self.screen_stocks(filters)
            
            # Convert to UpcomingEarningsData
            results = []
            for stock in raw_results:
                upcoming_data = self._convert_to_upcoming_earnings_data(stock, **kwargs)
                if upcoming_data:
                    results.append(upcoming_data)
            
            # Sort
            sort_by = kwargs.get('sort_by', 'earnings_date')
            sort_order = kwargs.get('sort_order', 'asc')
            results = self._sort_upcoming_earnings_results(results, sort_by, sort_order)
            
            # Limit results
            max_results = kwargs.get('max_results', 100)
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error in upcoming_earnings_screen: {e}")
            return []
    
    def earnings_winners_screener(self, **kwargs) -> List[StockData]:
        """
        Screen for post-earnings winning stocks.
        
        Args:
            earnings_period: Earnings period
            market_cap: Market cap filter  
            min_price: Minimum price
            min_avg_volume: Minimum average volume
            min_eps_growth_qoq: Minimum EPS QoQ growth
            min_eps_revision: Minimum EPS estimate revision
            min_sales_growth_qoq: Minimum sales QoQ growth
            min_weekly_performance: Weekly performance filter
            sma200_filter: Filter for above 200-day moving average
            target_sectors: Target sectors
            max_results: Maximum number of results
            sort_by: Sort field
            sort_order: Sort order
        
        Returns:
            List of StockData objects
        """
        try:
            # Build filters
            filters = self._build_earnings_winners_filters(**kwargs)
            
            # Fetch data from Finviz
            results = self.screen_stocks(filters)
            
            # Sort
            sort_by = kwargs.get('sort_by', 'performance_1w')
            sort_order = kwargs.get('sort_order', 'desc')
            
            if sort_by == 'performance_1w':
                results.sort(key=lambda x: x.performance_1w or -999, reverse=(sort_order == 'desc'))
            elif sort_by == 'eps_growth_qoq':
                results.sort(key=lambda x: x.eps_growth_qtr or -999, reverse=(sort_order == 'desc'))
            elif sort_by == 'price_change':
                results.sort(key=lambda x: x.price_change or -999, reverse=(sort_order == 'desc'))
            elif sort_by == 'volume':
                results.sort(key=lambda x: x.volume or 0, reverse=(sort_order == 'desc'))
            
            # Limit results
            max_results = kwargs.get('max_results', 50)
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error in earnings_winners_screener: {e}")
            return []
    
    def _build_earnings_winners_filters(self, **kwargs) -> Dict[str, Any]:
        """Build filters for post-earnings winning stocks screener."""
        filters = {}
        
        # Earnings period (direct earnings_date takes priority)
        if 'earnings_date' in kwargs:
            filters['earnings_date'] = kwargs['earnings_date']
        else:
            earnings_period = kwargs.get('earnings_period', 'this_week')
            if earnings_period == 'this_week':
                filters['earnings_date'] = 'thisweek'
            elif earnings_period == 'yesterday':
                filters['earnings_date'] = 'yesterday'
            elif earnings_period == 'today':
                filters['earnings_date'] = 'today'
            else:
                filters['earnings_date'] = 'thisweek'
        
        # Market cap (default: small over)
        market_cap = kwargs.get('market_cap', 'smallover')
        if market_cap in MARKET_CAP_FILTERS:
            filters['market_cap'] = market_cap
        
        # Price (default: $10+)
        min_price = kwargs.get('min_price', 10.0)
        if min_price:
            filters['price_min'] = min_price
        
        # Average volume (default: 500K+)
        min_avg_volume = kwargs.get('min_avg_volume', 500000)
        if min_avg_volume:
            # Support both numbers and strings
            finviz_volume = self._convert_volume_to_finviz_format(min_avg_volume)
            filters['avg_volume_min'] = finviz_volume
        
        # EPS QoQ growth (default: 10%+)
        min_eps_growth_qoq = kwargs.get('min_eps_growth_qoq', 10.0)
        if min_eps_growth_qoq:
            filters['eps_growth_qoq_min'] = min_eps_growth_qoq
        
        # EPS estimate revision (default: 5%+)
        min_eps_revision = kwargs.get('min_eps_revision', 5.0)
        if min_eps_revision:
            filters['eps_revision_min'] = min_eps_revision
        
        # Sales QoQ growth (default: 5%+)
        min_sales_growth_qoq = kwargs.get('min_sales_growth_qoq', 5.0)
        if min_sales_growth_qoq:
            filters['sales_growth_qoq_min'] = min_sales_growth_qoq
        
        # Weekly performance (default: 5 days to 1 week)
        min_weekly_performance = kwargs.get('min_weekly_performance', '5to-1w')
        if min_weekly_performance:
            filters['weekly_performance'] = min_weekly_performance
        
        # Above 200-day moving average (default: True)
        sma200_filter = kwargs.get('sma200_filter', True)
        if sma200_filter:
            filters['sma200_above'] = True
        
        # Sectors (default: major sectors)
        target_sectors = kwargs.get('target_sectors', [
            'Technology', 'Industrials', 'Healthcare', 
            'Communication Services', 'Consumer Cyclical', 'Financial Services'
        ])
        if target_sectors:
            filters['sectors'] = target_sectors
        
        # Result count limit
        max_results = kwargs.get('max_results', 50)
        if max_results:
            filters['max_results'] = max_results
        
        return filters
    
    def _build_upcoming_earnings_filters(self, **kwargs) -> Dict[str, Any]:
        """Build filters for upcoming earnings screener."""
        filters = {}
        
        # Earnings period (direct earnings_date takes priority)
        if 'earnings_date' in kwargs:
            # Use directly specified earnings_date parameter
            filters['earnings_date'] = kwargs['earnings_date']
        else:
            # Convert earnings_period to earnings_date
            earnings_period = kwargs.get('earnings_period', 'next_week')
            if earnings_period == 'next_week':
                filters['earnings_date'] = 'next_week'
            elif earnings_period == 'next_2_weeks':
                filters['earnings_date'] = 'within_2_weeks'
            elif earnings_period == 'next_month':
                filters['earnings_date'] = 'next_month'
        
        # Market cap (default: small over)
        market_cap = kwargs.get('market_cap', 'smallover')
        if market_cap in MARKET_CAP_FILTERS:
            filters['market_cap'] = market_cap
        
        # Price (default: $10+)
        min_price = kwargs.get('min_price', 10)
        if min_price:
            filters['price_min'] = min_price
        
        # Average volume (default: 500K = o500)
        min_avg_volume = kwargs.get('min_avg_volume', 500000)
        if min_avg_volume:
            # Support both numbers and strings
            finviz_volume = self._convert_volume_to_finviz_format(min_avg_volume)
            filters['avg_volume_min'] = finviz_volume
        
        # Result count limit
        max_results = kwargs.get('max_results')
        if max_results:
            filters['max_results'] = max_results
        
        # Sectors (default: major sectors)
        target_sectors = kwargs.get('target_sectors', [
            'Technology', 'Industrials', 'Healthcare', 
            'Communication Services', 'Consumer Cyclical', 
            'Financial Services', 'Consumer Defensive', 'Basic Materials'
        ])
        if target_sectors:
            filters['sectors'] = target_sectors
        
        return filters
    
    def _convert_to_upcoming_earnings_data(self, stock: StockData, **kwargs) -> Optional[UpcomingEarningsData]:
        """Convert StockData to UpcomingEarningsData"""
        try:
            # Basic info
            upcoming_data = UpcomingEarningsData(
                ticker=stock.ticker,
                company_name=stock.company_name or "",
                sector=stock.sector or "",
                industry=stock.industry or "",
                earnings_date=stock.earnings_date or "",
                earnings_timing="unknown"  # Hard to determine from Finviz
            )
            
            # Basic stock price data
            upcoming_data.current_price = stock.price
            upcoming_data.market_cap = stock.market_cap
            upcoming_data.avg_volume = stock.avg_volume
            
            # Valuation & recommendation data
            upcoming_data.pe_ratio = stock.pe_ratio
            upcoming_data.target_price = stock.target_price
            upcoming_data.analyst_recommendation = stock.analyst_recommendation
            
            # Calculate upside to target price
            if stock.target_price and stock.price and stock.price > 0:
                upcoming_data.target_price_upside = ((stock.target_price - stock.price) / stock.price) * 100
            
            # Risk assessment metrics
            upcoming_data.volatility = stock.volatility
            upcoming_data.beta = stock.beta
            upcoming_data.short_interest = stock.short_interest
            upcoming_data.insider_ownership = stock.insider_ownership
            upcoming_data.institutional_ownership = stock.institutional_ownership
            
            # Performance & technical indicators
            upcoming_data.performance_1w = stock.performance_1w
            upcoming_data.performance_1m = stock.performance_1m
            upcoming_data.rsi = stock.rsi
            

            
            return upcoming_data
            
        except Exception as e:
            logger.warning(f"Failed to convert stock data to upcoming earnings data: {e}")
            return None
    

    

    
    def _sort_upcoming_earnings_results(self, results: List[UpcomingEarningsData], 
                                      sort_by: str, sort_order: str) -> List[UpcomingEarningsData]:
        """Sort upcoming earnings results."""
        reverse = sort_order.lower() == 'desc'
        
        if sort_by == 'earnings_date':
            results.sort(key=lambda x: x.earnings_date or '', reverse=reverse)
        elif sort_by == 'market_cap':
            results.sort(key=lambda x: x.market_cap or 0, reverse=reverse)
        elif sort_by == 'target_price_upside':
            results.sort(key=lambda x: x.target_price_upside or 0, reverse=reverse)
        elif sort_by == 'volatility':
            results.sort(key=lambda x: x.volatility or 0, reverse=reverse)

        elif sort_by == 'ticker':
            results.sort(key=lambda x: x.ticker, reverse=reverse)
        
        return results
    
    def _build_trend_reversion_filters(self, **kwargs) -> Dict[str, Any]:
        """Build trend reversion filters."""
        filters = {}
        
        market_cap = kwargs.get('market_cap', 'mid_large')
        filters['market_cap'] = market_cap
        
        if 'eps_growth_qoq' in kwargs:
            filters['eps_growth_qoq_min'] = kwargs['eps_growth_qoq']
        
        if 'revenue_growth_qoq' in kwargs:
            filters['revenue_growth_qoq_min'] = kwargs['revenue_growth_qoq']
        
        if 'rsi_max' in kwargs:
            filters['rsi_max'] = kwargs['rsi_max']
        
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        if 'exclude_sectors' in kwargs and kwargs['exclude_sectors']:
            filters['exclude_sectors'] = kwargs['exclude_sectors']
        
        return filters
    
    def _build_relative_volume_filters(self, **kwargs) -> Dict[str, Any]:
        """Build relative volume filters."""
        filters = {}
        
        # Required parameter
        filters['relative_volume_min'] = kwargs['min_relative_volume']
        
        if 'min_price' in kwargs:
            filters['price_min'] = kwargs['min_price']
        
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        return filters
    
    def _build_technical_analysis_filters(self, **kwargs) -> Dict[str, Any]:
        """Build technical analysis filters."""
        filters = {}
        
        if 'rsi_min' in kwargs:
            filters['rsi_min'] = kwargs['rsi_min']
        
        if 'rsi_max' in kwargs:
            filters['rsi_max'] = kwargs['rsi_max']
        
        if 'price_vs_sma20' in kwargs:
            if kwargs['price_vs_sma20'] == 'above':
                filters['sma20_above'] = True
            elif kwargs['price_vs_sma20'] == 'below':
                filters['sma20_below'] = True
        
        if 'price_vs_sma50' in kwargs:
            if kwargs['price_vs_sma50'] == 'above':
                filters['sma50_above'] = True
            elif kwargs['price_vs_sma50'] == 'below':
                filters['sma50_below'] = True
        
        if 'price_vs_sma200' in kwargs:
            if kwargs['price_vs_sma200'] == 'above':
                filters['sma200_above'] = True
            elif kwargs['price_vs_sma200'] == 'below':
                filters['sma200_below'] = True
        
        if 'min_price' in kwargs:
            filters['price_min'] = kwargs['min_price']
        
        if 'min_volume' in kwargs:
            filters['volume_min'] = kwargs['min_volume']
        
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        return filters