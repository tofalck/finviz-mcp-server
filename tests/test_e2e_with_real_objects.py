#!/usr/bin/env python3
"""
E2E tests using real objects
Create real StockData (not mocks) to test server.py processing
"""

import pytest
import asyncio
from unittest.mock import patch
from src.server import server
from src.models import StockData
from src.finviz_client.screener import FinvizScreener

class TestE2EWithRealObjects:
    """E2E tests using real objects"""

    def setup_method(self):
        """completeStockDataobject"""
        self.real_stock_data = StockData(
            ticker="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            price=180.50,
            price_change=2.35,
            price_change_percent=1.32,
            volume=45000000,
            avg_volume=55000000,
            market_cap=2800000000000,
            pe_ratio=28.5,
            eps=6.12,
            eps_next_y=6.50,
            eps_surprise=0.12,
            revenue_surprise=0.08,
            dividend_yield=0.48,
            beta=1.23,
            volatility=0.25,
            # performanceattribute
            performance_1w=1.8,
            performance_1m=4.5,  # performance_4w 
            performance_3m=8.2,
            performance_6m=12.7,
            performance_ytd=18.9,
            performance_1y=22.1,
            # technical analysis
            sma_20=175.80,
            sma_50=170.20,
            sma_200=165.10,
            rsi=58.5,
            # growth
            eps_qoq_growth=15.2,
            sales_qoq_growth=8.7,
            target_price=195.0,
            # other
            debt_to_equity=1.45,
            current_ratio=1.05,
            roe=28.5,
            roa=15.2,
            gross_margin=0.38,
            operating_margin=0.30,
            profit_margin=0.25,
            # information
            insider_ownership=0.07,
            institutional_ownership=0.59,
            shares_outstanding=15500000000,
            shares_float=15400000000,
            # earningsrelated
            earnings_date="2024-01-25",
            # performance
            performance_1min=0.05,
            performance_5min=0.12,
            performance_30min=0.35,
            performance_1h=0.58,
            performance_4h=1.25
        )

        # multiplestockstest(server.pyformat)
        self.mock_results_with_real_objects = [self.real_stock_data]

    @pytest.mark.asyncio
    async def test_earnings_trading_screener_with_real_stockdata(self):
        """earnings_trading_screenerStockDatacheck"""
        
        with patch.object(FinvizScreener, "earnings_trading_screener") as mock_screener:
            mock_screener.return_value = self.mock_results_with_real_objects
            
            # server.py
            result = await server.call_tool("earnings_trading_screener", {
                "earnings_window": "yesterday_after_today_before",
                "market_cap": "large",
                "min_price": 10.0,
                "min_avg_volume": 1000000,
                "earnings_revision": "eps_revenue_positive",
                "price_trend": "positive_change"
            })
            
            # resultscheck
            assert result is not None
            # server.py charscheck
            assert "AAPL" in str(result)
            mock_screener.assert_called_once()

    @pytest.mark.asyncio 
    async def test_earnings_premarket_screener_real_data(self):
        """earnings_premarket_screenertest"""
        
        with patch.object(FinvizScreener, "earnings_premarket_screener") as mock_screener:
            mock_screener.return_value = self.mock_results_with_real_objects
            
            result = await server.call_tool("earnings_premarket_screener", {
                "earnings_timing": "today_before",
                "market_cap": "large",
                "min_price": 50.0,
                "min_price_change": 2.0
            })
            
            assert result is not None
            # StockDataattributeaccesssuccesscheck
            mock_screener.assert_called_once()

    @pytest.mark.asyncio
    async def test_volume_surge_screener_comprehensive_attributes(self):
        """volume_surge_screenercomprehensiveattributetest"""
        
        # attributetest
        enhanced_stock = StockData(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            sector="Technology",
            industry="Semiconductors",
            price=450.75,
            price_change=15.25,
            price_change_percent=3.50,
            volume=85000000,
            avg_volume=45000000,
            relative_volume=1.89,
            market_cap=1100000000000,
            pe_ratio=65.2,
            eps=12.45,
            performance_1w=8.5,
            performance_1m=12.8,
            performance_3m=25.7,
            volatility=0.45,
            rsi=72.3,
            sma_20=435.80,
            sma_50=420.15,
            sma_200=385.90
        )
        
        enhanced_results = [enhanced_stock]
        
        with patch.object(FinvizScreener, "volume_surge_screener") as mock_screener:
            mock_screener.return_value = enhanced_results
            
            result = await server.call_tool("volume_surge_screener", {
                "market_cap": "large",
                "min_price": 100.0,
                "min_relative_volume": 1.5,
                "min_price_change": 3.0,
                "sma_filter": "above_sma200"
            })
            
            assert result is not None
            # highattributeaccesstest
            assert enhanced_stock.relative_volume == 1.89
            assert enhanced_stock.sma_200 == 385.90
            mock_screener.assert_called_once()

    def test_stockdata_attribute_access_patterns(self):
        """server.pyattributeaccesstest"""
        
        stock = self.real_stock_data
        
        # server.py
        try:
            # basic information
            basic_info = [
                f"Ticker: {stock.ticker}",
                f"Company: {stock.company_name}",
                f"Sector: {stock.sector}",
                f"Price: ${stock.price:.2f}" if stock.price else "Price: N/A"
            ]
            
            # performanceinformation
            performance_info = [
                f"1W Performance: {stock.performance_1w:.2f}%" if stock.performance_1w else "1W Performance: N/A",
                f"1M Performance: {stock.performance_1m:.2f}%" if stock.performance_1m else "1M Performance: N/A",
                f"3M Performance: {stock.performance_3m:.2f}%" if stock.performance_3m else "3M Performance: N/A"
            ]
            
            # earningsrelatedinformation
            earnings_info = [
                f"EPS Surprise: {stock.eps_surprise:.2f}%" if stock.eps_surprise else "EPS Surprise: N/A",
                f"Revenue Surprise: {stock.revenue_surprise:.2f}%" if stock.revenue_surprise else "Revenue Surprise: N/A",
                f"EPS QoQ Growth: {stock.eps_qoq_growth:.2f}%" if stock.eps_qoq_growth else "EPS QoQ Growth: N/A"
            ]
            
            # information
            technical_info = [
                f"RSI: {stock.rsi:.1f}" if stock.rsi else "RSI: N/A",
                f"Volatility: {stock.volatility:.2f}" if stock.volatility else "Volatility: N/A",
                f"Beta: {stock.beta:.2f}" if stock.beta else "Beta: N/A"
            ]
            
            # informationcheck
            all_info = basic_info + performance_info + earnings_info + technical_info
            
            for info_line in all_info:
                assert isinstance(info_line, str)
                assert len(info_line) > 0
                assert "None" not in info_line  # None charscheck
                
        except AttributeError as e:
            pytest.fail(f"AttributeError in server.py simulation: {e}")

    def test_all_performance_attributes_exist(self):
        """performanceattributecheck"""
        
        stock = self.real_stock_data
        
        # server.pyperformanceattribute
        performance_attrs = [
            'performance_1min', 'performance_5min', 'performance_30min', 'performance_1h',
            'performance_4h', 'performance_1w', 'performance_1m', 'performance_3m',
            'performance_6m', 'performance_ytd', 'performance_1y'
        ]
        
        missing_attrs = []
        for attr in performance_attrs:
            if not hasattr(stock, attr):
                missing_attrs.append(attr)
        
        if missing_attrs:
            pytest.fail(f"Missing performance attributes: {missing_attrs}")
        
        # attributevaluecheck
        for attr in performance_attrs:
            value = getattr(stock, attr)
            if value is not None:
                assert isinstance(value, (int, float)), f"{attr} has invalid type: {type(value)}"

    def test_error_prone_attribute_combinations(self):
        """errorattributetest"""
        
        # attributeNonetest
        partial_stock = StockData(
            ticker="PARTIAL",
            company_name="Partial Data Corp",
            sector="Test",
            industry="Test",
            # attribute
            price=None,
            performance_1w=None,
            performance_1m=None,
            eps_surprise=None,
            revenue_surprise=None
        )
        
        # Noneattributeaccesstest
        try:
            price_text = f"Price: ${partial_stock.price:.2f}" if partial_stock.price else "Price: N/A"
            perf_1w_text = f"1W Performance: {partial_stock.performance_1w:.2f}%" if partial_stock.performance_1w else "1W Performance: N/A"
            perf_1m_text = f"1M Performance: {partial_stock.performance_1m:.2f}%" if partial_stock.performance_1m else "1M Performance: N/A"
            eps_text = f"EPS Surprise: {partial_stock.eps_surprise:.2f}%" if partial_stock.eps_surprise else "EPS Surprise: N/A"
            
            # "N/A"check
            assert price_text == "Price: N/A"
            assert perf_1w_text == "1W Performance: N/A"
            assert perf_1m_text == "1M Performance: N/A"
            assert eps_text == "EPS Surprise: N/A"
            
        except (AttributeError, TypeError) as e:
            pytest.fail(f"Error handling None attributes: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 