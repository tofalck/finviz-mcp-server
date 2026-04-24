#!/usr/bin/env python3
"""
Comprehensive E2E tests using actual MCP calls
Tests to detect type errors and column-name errors
"""

import pytest
import asyncio
import sys
import os
import logging
from typing import List, Dict, Any, Optional
from unittest.mock import patch, Mock

# 
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.server import server
from src.models import StockData
from src.finviz_client.screener import FinvizScreener
from src.finviz_client.base import FinvizClient
from src.finviz_client.news import FinvizNewsClient
from src.finviz_client.sector_analysis import FinvizSectorAnalysisClient
from src.finviz_client.sec_filings import FinvizSECFilingsClient

# log settings
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestComprehensiveE2E:
    """Comprehensive E2E tests using actual MCP calls"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """test"""
        # testcompleteStockData
        self.sample_stock_data = StockData(
            ticker="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            price=180.50,
            price_change=2.35,
            price_change_percent=1.32,
            volume=45000000,
            avg_volume=55000000,
            relative_volume=0.82,
            market_cap=2800000000000,
            pe_ratio=28.5,
            eps=6.12,
            eps_next_y=6.50,
            eps_surprise=0.12,
            revenue_surprise=0.08,
            dividend_yield=0.48,
            beta=1.23,
            volatility=0.25,
            performance_1w=1.8,
            performance_1m=4.5,
            performance_3m=8.2,
            performance_6m=12.7,
            performance_ytd=18.9,
            performance_1y=22.1,
            sma_20=175.80,
            sma_50=170.20,
            sma_200=165.10,
            rsi=58.5,
            eps_qoq_growth=15.2,
            sales_qoq_growth=8.7,
            target_price=195.0,
            debt_to_equity=1.45,
            current_ratio=1.05,
            roe=28.5,
            roa=15.2,
            gross_margin=0.38,
            operating_margin=0.30,
            profit_margin=0.25,
            insider_ownership=0.07,
            institutional_ownership=0.59,
            shares_outstanding=15500000000,
            shares_float=15400000000,
            earnings_date="2024-01-25",
            week_52_high=195.89,
            week_52_low=124.17
        )

        # multiplestocks
        self.sample_stocks_list = [
            self.sample_stock_data,
            StockData(
                ticker="MSFT",
                company_name="Microsoft Corporation",
                sector="Technology",
                industry="Software—Infrastructure",
                price=420.75,
                price_change=8.25,
                price_change_percent=2.00,
                volume=25000000,
                market_cap=3100000000000,
                pe_ratio=32.1,
                eps=12.05
            )
        ]

    # ===========================================
    # earningsrelatedtest
    # ===========================================

    @pytest.mark.asyncio
    async def test_earnings_screener_real_call(self):
        """earningsupcomingstocksscreeningtest"""
        with patch.object(FinvizScreener, "earnings_screener") as mock_screener:
            mock_screener.return_value = self.sample_stocks_list

            result = await server.call_tool("earnings_screener", {
                "earnings_date": "this_week"
            })

            assert result is not None
            assert len(result) > 0
            result_text = str(result[0].text)
            assert "AAPL" in result_text
            mock_screener.assert_called_once()

    @pytest.mark.asyncio
    async def test_volume_surge_screener_real_call(self):
        """volumesurgetest"""
        with patch.object(FinvizScreener, "volume_surge_screener") as mock_screener:
            mock_screener.return_value = self.sample_stocks_list

            result = await server.call_tool("volume_surge_screener", {
                "random_string": "test"
            })

            assert result is not None
            result_text = str(result[0].text)
            assert "fixed filter conditions" in result_text
            mock_screener.assert_called_once()

    @pytest.mark.asyncio
    async def test_earnings_trading_screener_real_call(self):
        """earningstrade targetstockstest"""
        with patch.object(FinvizScreener, "earnings_trading_screener") as mock_screener:
            mock_screener.return_value = self.sample_stocks_list

            result = await server.call_tool("earnings_trading_screener", {
                "random_string": "test"
            })

            assert result is not None
            result_text = str(result[0].text)
            assert "EPS Surprise" in result_text or "Revenue Surprise" in result_text
            mock_screener.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stock_fundamentals_real_call(self):
        """singlestocksfundamental datafetchtest"""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.return_value = self.sample_stock_data

            result = await server.call_tool("get_stock_fundamentals", {
                "ticker": "AAPL"
            })

            assert result is not None
            result_text = str(result[0].text)
            assert "AAPL" in result_text
            assert "Apple Inc." in result_text
            mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_multiple_stocks_fundamentals_real_call(self):
        """multiplestocksfundamental datafetchtest"""
        with patch.object(FinvizClient, "get_multiple_stocks_fundamentals") as mock_client:
            mock_client.return_value = self.sample_stocks_list

            result = await server.call_tool("get_multiple_stocks_fundamentals", {
                "tickers": ["AAPL", "MSFT"]
            })

            assert result is not None
            result_text = str(result[0].text)
            assert "AAPL" in result_text
            assert "MSFT" in result_text
            mock_client.assert_called_once()

    # ===========================================
    # attributeaccesstest
    # ===========================================

    def test_stockdata_attribute_access_comprehensive(self):
        """StockDataattributeaccesscomprehensivetest"""
        stock = self.sample_stock_data

        # basic informationaccesstest
        basic_attrs = [
            'ticker', 'company_name', 'sector', 'industry',
            'price', 'price_change', 'price_change_percent'
        ]
        for attr in basic_attrs:
            try:
                value = getattr(stock, attr)
                assert value is not None, f"{attr} should not be None"
            except AttributeError as e:
                pytest.fail(f"Missing attribute: {attr}")

        # performanceattributeaccesstest
        performance_attrs = [
            'performance_1w', 'performance_1m', 'performance_3m',
            'performance_6m', 'performance_ytd', 'performance_1y'
        ]
        for attr in performance_attrs:
            try:
                value = getattr(stock, attr)
                assert value is None or isinstance(value, (int, float))
            except AttributeError as e:
                pytest.fail(f"Missing performance attribute: {attr}")

        # earningsrelatedattributeaccesstest
        earnings_attrs = [
            'eps_surprise', 'revenue_surprise', 'eps_qoq_growth',
            'sales_qoq_growth', 'earnings_date'
        ]
        for attr in earnings_attrs:
            try:
                value = getattr(stock, attr)
                assert value is None or isinstance(value, (int, float, str))
            except AttributeError as e:
                pytest.fail(f"Missing earnings attribute: {attr}")

    def test_stockdata_formatting_patterns(self):
        """StockDatatest"""
        stock = self.sample_stock_data

        # server.py
        try:
            # basic information
            basic_info = f"Ticker: {stock.ticker}"
            basic_info += f", Company: {stock.company_name}"
            basic_info += f", Sector: {stock.sector}"
            
            # priceinformation
            if stock.price:
                price_info = f"Price: ${stock.price:.2f}"
            if stock.price_change:
                price_info += f", Change: {stock.price_change:.2f}%"

            # performanceinformation
            if stock.performance_1w:
                perf_info = f"1W Performance: {stock.performance_1w:.2f}%"
            if stock.performance_1m:
                perf_info += f", 1M Performance: {stock.performance_1m:.2f}%"

            # earningsinformation
            if stock.eps_surprise:
                earnings_info = f"EPS Surprise: {stock.eps_surprise:.2f}%"
            if stock.revenue_surprise:
                earnings_info += f", Revenue Surprise: {stock.revenue_surprise:.2f}%"

            assert len(basic_info) > 0
            
        except Exception as e:
            pytest.fail(f"Formatting pattern failed: {e}")

    # ===========================================
    # errortest
    # ===========================================

    @pytest.mark.asyncio
    async def test_invalid_ticker_handling(self):
        """errortest"""
        with patch.object(FinvizClient, "get_stock_fundamentals") as mock_client:
            mock_client.side_effect = ValueError("Invalid ticker: INVALID")

            result = await server.call_tool("get_stock_fundamentals", {
                "ticker": "INVALID"
            })

            assert result is not None
            result_text = str(result[0].text)
            assert "Error" in result_text or "error" in result_text

    @pytest.mark.asyncio
    async def test_invalid_parameters_handling(self):
        """parametererrortest"""
        # earningstest
        result = await server.call_tool("earnings_screener", {
            "earnings_date": "invalid_date"
        })

        assert result is not None
        result_text = str(result[0].text)
        assert "Error" in result_text or "Invalid" in result_text

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 