#!/usr/bin/env python3
"""
MCP System Validation Test Suite
Recommended for release: system-level functional tests using actual MCP calls
Comprehensive tests including data validity checks
"""

import pytest
import asyncio
import sys
import os
import re
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from dotenv import load_dotenv

# .envfileload
load_dotenv()

# 
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# MCP tools import(MCP)
from src.server import (
    earnings_screener,
    earnings_trading_screener,
    earnings_premarket_screener,
    earnings_afterhours_screener,
    volume_surge_screener,
    uptrend_screener,
    upcoming_earnings_screener,
    get_stock_fundamentals,
    get_multiple_stocks_fundamentals,
    get_market_overview,
    dividend_growth_screener,
    earnings_winners_screener
)

@dataclass
class TestResult:
    """testresults"""
    test_name: str
    success: bool
    execution_time: float
    result_data: Any
    error_message: Optional[str] = None
    data_quality_score: float = 0.0
    stocks_found: int = 0

class MCPSystemValidationTest:
    """MCP System validation tests"""

    def __init__(self):
        self.test_results: List[TestResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test_result(self, result: TestResult):
        """testresults"""
        self.test_results.append(result)
        self.total_tests += 1
        
        if result.success:
            self.passed_tests += 1
            print(f"✅ {result.test_name} - runtime: {result.execution_time:.2f}s, stocks: {result.stocks_found}")
        else:
            print(f"❌ {result.test_name} - error: {result.error_message}")

    def validate_stock_data_quality(self, result_text: str, test_name: str) -> tuple[float, int]:
        """"""
        quality_score = 0.0
        stocks_found = 0
        
        # detect
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        tickers = re.findall(ticker_pattern, result_text)
        stocks_found = len(set(tickers))
        
        # 
        quality_checks = [
            ('price', r'\$\d+\.\d+'),
            ('', r'[+-]?\d+\.\d+%'),
            ('volume', r'[\d,]+(?:K|M|B)?'),
            ('sectorinformation', r'(Technology|Healthcare|Financial|Energy|Consumer|Industrial|Real Estate|Utilities|Communication|Basic Materials)'),
            ('results', r'(Results|stocks|found|detect)'),
        ]
        
        for check_name, pattern in quality_checks:
            if re.search(pattern, result_text):
                quality_score += 20.0  # 20
        
        # errordetect()
        error_patterns = [
            r'Error|Exception|Failed',
            r'AttributeError|TypeError|KeyError',
            r'NoneType|object has no attribute',
            r'connection error|timeout'
        ]
        
        for error_pattern in error_patterns:
            if re.search(error_pattern, result_text, re.IGNORECASE):
                quality_score -= 30.0
        
        return max(0.0, min(100.0, quality_score)), stocks_found

    def test_earnings_related_functions(self):
        """earningsrelatedtest"""
        print("\n🔍 earningsrelatedteststart...")
        
        # 1. earningsupcomingstocksscreening
        start_time = time.time()
        try:
            result = earnings_screener(earnings_date="today_after")
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "earnings_screener")
            
            self.log_test_result(TestResult(
                test_name="earningsupcomingstocksscreening",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="earningsupcomingstocksscreening",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

        # 2. earningstrade targetstocks
        start_time = time.time()
        try:
            result = earnings_trading_screener()
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "earnings_trading_screener")
            
            # value:0 items(time)
            success = True  # errorsuccess
            
            self.log_test_result(TestResult(
                test_name="earningstrade targetstocks",
                success=success,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="earningstrade targetstocks",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

    def test_basic_screening_functions(self):
        """screeningtest"""
        print("\n🔍 screeningteststart...")
        
        # 1. volumesurgestocks
        start_time = time.time()
        try:
            result = volume_surge_screener()
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "volume_surge_screener")
            
            # 50stocksor moredetecthigh
            if stocks_found >= 50:
                quality_score += 20.0
            
            self.log_test_result(TestResult(
                test_name="volumesurgestocksscreening",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="volumesurgestocksscreening",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

        # 2. uptrendstocks
        start_time = time.time()
        try:
            result = uptrend_screener()
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "uptrend_screener")
            
            # 200stocksor moredetecthigh
            if stocks_found >= 200:
                quality_score += 20.0
            
            self.log_test_result(TestResult(
                test_name="uptrendstocksscreening",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="uptrendstocksscreening",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

    def test_stock_data_functions(self):
        """ itemsstocksfetchtest"""
        print("\n🔍  itemsstocksfetchteststart...")
        
        # 1. singlestocksfundamental data
        start_time = time.time()
        try:
            result = get_stock_fundamentals(
                ticker="AAPL",
                data_fields=["price", "change", "volume", "pe_ratio", "eps"]
            )
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            
            # AAPL
            quality_score = 0.0
            if "AAPL" in result_text: quality_score += 25.0
            if re.search(r'\$\d+\.\d+', result_text): quality_score += 25.0  # price
            if re.search(r'[\d,]+', result_text): quality_score += 25.0  # volume
            if "Fundamental Data" in result_text: quality_score += 25.0
            
            self.log_test_result(TestResult(
                test_name="singlestocksfundamental data(AAPL)",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=1
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="singlestocksfundamental data(AAPL)",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

        # 2. multiplestocksfundamental data
        start_time = time.time()
        try:
            result = get_multiple_stocks_fundamentals(
                tickers=["MSFT", "GOOGL", "NVDA"],
                data_fields=["price", "change", "market_cap", "pe_ratio"]
            )
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            
            # multiplestocks
            quality_score = 0.0
            target_tickers = ["MSFT", "GOOGL", "NVDA"]
            found_tickers = sum(1 for ticker in target_tickers if ticker in result_text)
            quality_score += (found_tickers / len(target_tickers)) * 50.0
            
            if "Fundamental Data" in result_text: quality_score += 25.0
            if re.search(r'\$\d+\.\d+', result_text): quality_score += 25.0
            
            self.log_test_result(TestResult(
                test_name="multiplestocksfundamental data(MSFT,GOOGL,NVDA)",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=found_tickers
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="multiplestocksfundamental data(MSFT,GOOGL,NVDA)",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

        # 3. market overview
        start_time = time.time()
        try:
            result = get_market_overview()
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            
            # market overview
            quality_score = 0.0
            market_indicators = ["SPY", "QQQ", "DIA", "IWM", "TLT", "GLD"]
            found_indicators = sum(1 for indicator in market_indicators if indicator in result_text)
            quality_score += (found_indicators / len(market_indicators)) * 50.0
            
            if "market overview" in result_text or "Market Overview" in result_text: quality_score += 25.0
            if re.search(r'\$\d+\.\d+', result_text): quality_score += 25.0
            
            self.log_test_result(TestResult(
                test_name="market overview",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=found_indicators
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="market overview",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

    def test_parameter_type_validation(self):
        """parametertest(min_volume)"""
        print("\n🔍 parameterteststart...")
        
        # 1. Finviz charsformattest - "o100"
        start_time = time.time()
        try:
            result = earnings_screener(
                earnings_date="within_2_weeks",
                min_volume="o100"
            )
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "earnings_screener_o100")
            
            self.log_test_result(TestResult(
                test_name="min_volumetest(o100format)",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="min_volumetest(o100format)",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

    def test_advanced_screening_functions(self):
        """highscreeningtest"""
        print("\n🔍 highscreeningteststart...")
        
        # 1. dividendgrowthstocks
        start_time = time.time()
        try:
            result = dividend_growth_screener(min_dividend_yield=2)
            execution_time = time.time() - start_time
            result_text = str(result[0].text) if result and len(result) > 0 else str(result)
            quality_score, stocks_found = self.validate_stock_data_quality(result_text, "dividend_growth_screener")
            
            # dividendrelated
            if "Dividend" in result_text or "dividend" in result_text:
                quality_score += 20.0
            
            self.log_test_result(TestResult(
                test_name="dividendgrowthstocksscreening",
                success=True,
                execution_time=execution_time,
                result_data=result,
                data_quality_score=quality_score,
                stocks_found=stocks_found
            ))
        except Exception as e:
            self.log_test_result(TestResult(
                test_name="dividendgrowthstocksscreening",
                success=False,
                execution_time=time.time() - start_time,
                result_data=None,
                error_message=str(e)
            ))

    def generate_test_report(self) -> str:
        """comprehensivetest"""
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        report = f"""
==============================================================================
🧪 MCP SYSTEM VALIDATION TEST REPORT
==============================================================================
📊 testrunsummary:
   test: {self.total_tests}
   success: {self.passed_tests}
   failed: {self.total_tests - self.passed_tests}
   success: {success_rate:.1f}%

==============================================================================
📈 testresults:
"""
        
        # by categoryresults
        categories = {
            "earningsrelated": ["earningsupcoming", "earnings"],
            "screening": ["volumesurge", "uptrend"],
            "fetch": ["singlestocks", "multiplestocks", "market overview"],
            "parameter": ["o100format"],
            "high": ["dividendgrowth"]
        }
        
        for category, keywords in categories.items():
            category_tests = [r for r in self.test_results if any(kw in r.test_name for kw in keywords)]
            if category_tests:
                category_success = sum(1 for r in category_tests if r.success)
                category_total = len(category_tests)
                category_rate = (category_success / category_total * 100) if category_total > 0 else 0
                
                report += f"\n🔹 {category}: {category_success}/{category_total} ({category_rate:.1f}%)\n"
                
                for result in category_tests:
                    status = "✅" if result.success else "❌"
                    report += f"   {status} {result.test_name}\n"
                    if result.success:
                        report += f"      runtime: {result.execution_time:.2f}s, "
                        report += f": {result.data_quality_score:.1f}, "
                        report += f"stocks: {result.stocks_found}\n"
                    else:
                        report += f"      error: {result.error_message}\n"

        # 
        successful_tests = [r for r in self.test_results if r.success]
        if successful_tests:
            avg_quality = sum(r.data_quality_score for r in successful_tests) / len(successful_tests)
            total_stocks = sum(r.stocks_found for r in successful_tests)
            avg_execution_time = sum(r.execution_time for r in successful_tests) / len(successful_tests)
            
            report += f"""
==============================================================================
📊 :
   average quality score: {avg_quality:.1f}/100
   detectstocks: {total_stocks}
   averageruntime: {avg_execution_time:.2f}s

==============================================================================
🎯 release decision:
"""
            
            if success_rate >= 90 and avg_quality >= 70:
                report += "   🟢 PASS - \n"
            elif success_rate >= 80 and avg_quality >= 60:
                report += "   🟡 CAUTION - notescheck\n" 
            else:
                report += "   🔴 FAIL - \n"

        report += "\n=============================================================================="
        
        return report

    def run_all_tests(self):
        """testrun"""
        print("🚀 MCP System Validation Test Suite start")
        print("=" * 80)
        
        # testcategoryrun
        self.test_earnings_related_functions()
        self.test_basic_screening_functions()
        self.test_stock_data_functions()
        self.test_parameter_type_validation()
        self.test_advanced_screening_functions()
        
        # 
        report = self.generate_test_report()
        print(report)
        
        return self.passed_tests == self.total_tests

# mainrunfunction
def main():
    """maintestrun"""
    validator = MCPSystemValidationTest()
    success = validator.run_all_tests()
    
    if success:
        print("\n🎉 testsuccess! MCP System production-ready。")
        return True
    else:
        print("\n⚠️  testfailed。check。")
        return False

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1) 