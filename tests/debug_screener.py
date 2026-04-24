#!/usr/bin/env python3
"""
Debug script for Finviz screener issues
Script to debug Finviz screener issues
"""

import sys
import os
import logging

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from src.finviz_client.screener import FinvizScreener
from src.finviz_client.base import FinvizClient

def test_direct_url_construction():
    """URLbuildtest"""
    print("=== URLbuildtest ===")
    
    screener = FinvizScreener()
    
    # next weekearningsbuild
    filters = {
        'earnings_date': 'next_week',
        'market_cap': 'smallover',
        'price_min': 10,
        'avg_volume_min': 500,
        'sectors': ['Technology', 'Industrials', 'Healthcare', 
                   'Communication Services', 'Consumer Cyclical', 
                   'Financial Services', 'Consumer Defensive', 'Basic Materials']
    }
    
    # Finvizparameterconvert
    finviz_params = screener._convert_filters_to_finviz(filters)
    print(f"buildparameter: {finviz_params}")
    
    # URLbuild
    from urllib.parse import urlencode
    base_url = "https://finviz.com/screener.ashx"
    full_url = f"{base_url}?{urlencode(finviz_params)}"
    print(f"buildURL: {full_url}")
    
    # FinvizURL()
    expected_url = "https://elite.finviz.com/screener.ashx?v=311&p=w&f=cap_smallover,earningsdate_nextweek,sec_technology|industrials|healthcare|communicationservices|consumercyclical|financial|consumerdefensive|basicmaterials,sh_avgvol_o500,sh_price_o10&ft=4&o=ticker&ar=10"
    print(f"URL: {expected_url}")

def test_basic_request():
    """HTTPtest"""
    print("\n=== HTTPtest ===")
    
    client = FinvizClient()
    
    try:
        # access
        response = client._make_request("https://finviz.com/screener.ashx", {'v': '111'})
        print(f"response: {response.status_code}")
        print(f"response: {len(response.text)}  chars")
        
        # HTML
        if "screener" in response.text.lower():
            print("✓ ")
        else:
            print("✗ load")
            
    except Exception as e:
        print(f"✗ HTTPerror: {e}")

def test_csv_export():
    """CSVtest"""
    print("\n=== CSVtest ===")
    
    client = FinvizClient()
    
    try:
        # CSV
        params = {'v': '111'}
        response = client._make_request("https://finviz.com/export.ashx", params)
        print(f"CSVresponse: {response.status_code}")
        print(f"CSVresponse: {len(response.text)}  chars")
        print(f"CSVresponsefirst200 chars: {response.text[:200]}")
        
        if "ticker" in response.text.lower() or "symbol" in response.text.lower():
            print("✓ CSVfetch")
        else:
            print("✗ CSVfetch")
            
    except Exception as e:
        print(f"✗ CSVerror: {e}")

def test_html_parsing():
    """HTMLtest"""
    print("\n=== HTMLtest ===")
    
    client = FinvizClient()
    
    try:
        # HTMLfetch
        params = {'v': '111', 'f': 'cap_smallover'}
        response = client._make_request("https://finviz.com/screener.ashx", params)
        
        # HTML
        parsed_data = client._parse_finviz_table(response.text)
        print(f": {len(parsed_data)}")
        
        if parsed_data:
            print("✓ HTMLsuccess")
            print(f"first: {list(parsed_data[0].keys())}")
        else:
            print("✗ HTML0fetch")
            
    except Exception as e:
        print(f"✗ HTMLerror: {e}")

def main():
    """mainrunfunction"""
    print("🔍 Finviz  teststart")
    print("=" * 60)
    
    test_direct_url_construction()
    test_basic_request()
    test_csv_export()
    test_html_parsing()
    
    print("\n" + "=" * 60)
    print("📊 testcompleted")

if __name__ == "__main__":
    main() 