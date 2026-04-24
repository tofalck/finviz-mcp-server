#!/usr/bin/env python3
"""
Finviz Elite filter analysis script

Finviz Elitelogin、
filtervaluedetailsanalysis。

Requirements:
- requests
- beautifulsoup4
- selenium ()
- pandas (results)

Usage:
    python finviz_elite_analyzer.py
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import logging

# log settings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FilterOption:
    """filter"""
    value: str
    label: str
    group: Optional[str] = None

@dataclass
class FilterParameter:
    """filterparameter"""
    name: str
    id: str
    data_filter: str
    options: List[FilterOption]
    selected_value: Optional[str] = None
    category: Optional[str] = None

class FinvizEliteAnalyzer:
    """Finviz Elite filteranalysis"""
    
    def __init__(self):
        self.base_url = "https://elite.finviz.com"
        self.screener_url = f"{self.base_url}/screener.ashx"
        self.login_url = f"{self.base_url}/login.ashx"
        self.session = requests.Session()
        self.driver = None
        self.filters = []
        
        # excludefilter( items)
        self.excluded_filters = {
            'screenerpresetsselect',     # 
            'screenerpresets',           # 
            'fs_screenerpresetsselect',  # ID
            'fs_screenerpresets',        # ID
        }
        
        # 
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        logger.info(f"excludefilter: {', '.join(self.excluded_filters)}")
    
    def setup_selenium_driver(self, headless: bool = True):
        """Selenium"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # ChromeDriver(webdriver-manager)
            # service = Service(ChromeDriverManager().install())
            
            # ChromeDriver
            service = Service()  # PATHchromedriver
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Selenium")
            return True
            
        except Exception as e:
            logger.error(f"Seleniumfailed: {e}")
            return False
    
    def login_with_selenium(self, username: str, password: str) -> bool:
        """SeleniumFinviz Elitelogin"""
        try:
            if not self.driver:
                if not self.setup_selenium_driver():
                    return False
            
            logger.info("Finviz Elitelogin...")
            self.driver.get(self.login_url)
            
            # login
            wait = WebDriverWait(self.driver, 10)
            
            # usernamepassword
            username_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            
            # login
            login_button = self.driver.find_element(By.XPATH, "//input[@type='submit' and @value='Login']")
            login_button.click()
            
            # loginsuccesscheck(URLcheck)
            time.sleep(3)
            
            if "screener.ashx" in self.driver.current_url or self.driver.current_url == f"{self.base_url}/":
                logger.info("loginsuccess")
                return True
            else:
                logger.error("loginfailed")
                return False
                
        except Exception as e:
            logger.error(f"loginerror: {e}")
            return False
    
    def navigate_to_screener(self):
        """"""
        try:
            self.driver.get(self.screener_url)
            time.sleep(2)
            logger.info("")
            return True
        except Exception as e:
            logger.error(f"error: {e}")
            return False
    
    def extract_filter_parameters(self) -> List[FilterParameter]:
        """filterparameterextract"""
        try:
            # HTMLfetch
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            filters = []
            
            # selectfilter
            select_elements = soup.find_all('select', class_=re.compile(r'screener-combo|fv-select'))
            
            for select in select_elements:
                try:
                    filter_param = self._parse_select_element(select)
                    if filter_param:
                        filters.append(filter_param)
                except Exception as e:
                    logger.warning(f"selectanalysiserror: {e}")
                    continue
            
            logger.info(f"{len(filters)} itemsfilterparameterdetect")
            return filters
            
        except Exception as e:
            logger.error(f"filterparameterextracterror: {e}")
            return []
    
    def _parse_select_element(self, select) -> Optional[FilterParameter]:
        """selectanalysisFilterParameterobject"""
        try:
            # attributefetch
            select_id = select.get('id', '')
            data_filter = select.get('data-filter', '')
            
            if not data_filter:
                return None
            
            # excludefilter
            if (select_id.lower() in self.excluded_filters or 
                data_filter.lower() in self.excluded_filters):
                logger.debug(f"filterexclude: {select_id} (data-filter: {data_filter})")
                return None
            
            # analysis
            options = []
            current_group = None
            
            for element in select.find_all(['option', 'optgroup']):
                if element.name == 'optgroup':
                    current_group = element.get('label', '')
                elif element.name == 'option':
                    value = element.get('value', '')
                    label = element.get_text(strip=True)
                    
                    option = FilterOption(
                        value=value,
                        label=label,
                        group=current_group
                    )
                    options.append(option)
            
            # valuefetch
            selected_option = select.find('option', selected=True)
            selected_value = selected_option.get('value', '') if selected_option else None
            
            return FilterParameter(
                name=self._get_filter_name_from_id(select_id),
                id=select_id,
                data_filter=data_filter,
                options=options,
                selected_value=selected_value
            )
            
        except Exception as e:
            logger.warning(f"selectanalysiserror: {e}")
            return None
    
    def _get_filter_name_from_id(self, element_id: str) -> str:
        """element IDfilter"""
        # ID → 
        id_to_name = {
            'fs_exch': 'Exchange',
            'fs_idx': 'Index',
            'fs_sec': 'Sector',
            'fs_ind': 'Industry',
            'fs_geo': 'Country',
            'fs_cap': 'Market Cap',
            'fs_sh_price': 'Price',
            'fs_fa_div': 'Dividend Yield',
            'fs_fa_epsrev': 'EPS/Revenue Revision',
            'fs_sh_short': 'Short Float',
            'fs_an_recom': 'Analyst Recommendation',
            'fs_earningsdate': 'Earnings Date',
            'fs_ipodate': 'IPO Date',
            'fs_sh_avgvol': 'Average Volume',
            'fs_sh_relvol': 'Relative Volume',
            'fs_sh_curvol': 'Current Volume',
            'fs_sh_outstanding': 'Shares Outstanding',
            'fs_sh_float': 'Float',
            'fs_ta_perf2': 'Performance 2',
            'fs_targetprice': 'Target Price',
            # 
        }
        
        return id_to_name.get(element_id, element_id)
    
    def categorize_filters(self, filters: List[FilterParameter]) -> Dict[str, List[FilterParameter]]:
        """filtercategory"""
        categories = {
            'basic information': [],
            'stock pricemarket cap': [],
            'dividend': [],
            'analystrecommendation': [],
            'date': [],
            'volume': [],
            'share issuance': [],
            'technical analysis': [],
            'other': []
        }
        
        category_mapping = {
            'Exchange': 'basic information',
            'Index': 'basic information',
            'Sector': 'basic information',
            'Industry': 'basic information',
            'Country': 'basic information',
            'Market Cap': 'stock pricemarket cap',
            'Price': 'stock pricemarket cap',
            'Target Price': 'stock pricemarket cap',
            'Dividend Yield': 'dividend',
            'EPS/Revenue Revision': 'dividend',
            'Short Float': 'dividend',
            'Analyst Recommendation': 'analystrecommendation',
            'Earnings Date': 'date',
            'IPO Date': 'date',
            'Average Volume': 'volume',
            'Relative Volume': 'volume',
            'Current Volume': 'volume',
            'Shares Outstanding': 'share issuance',
            'Float': 'share issuance',
            'Performance 2': 'technical analysis',
        }
        
        for filter_param in filters:
            category = category_mapping.get(filter_param.name, 'other')
            categories[category].append(filter_param)
        
        return categories
    
    def export_to_markdown(self, filters: List[FilterParameter], output_file: str = 'finviz_elite_filters.md'):
        """filterinformationMarkdownexport as format"""
        try:
            categorized_filters = self.categorize_filters(filters)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Finviz Elite filterparameterdetailslist\n\n")
                f.write("Elitedetailsfilterparameterlist。\n\n")
                
                for category, category_filters in categorized_filters.items():
                    if not category_filters:
                        continue
                        
                    f.write(f"## {category}\n\n")
                    
                    for filter_param in category_filters:
                        f.write(f"### {filter_param.name} - `{filter_param.data_filter}`\n\n")
                        
                        if filter_param.options:
                            f.write("| value | description |  |\n")
                            f.write("|---|---|---|\n")
                            
                            for option in filter_param.options:
                                group = option.group or "-"
                                f.write(f"| `{option.value}` | {option.label} | {group} |\n")
                            
                            f.write("\n")
                        
                        f.write("\n")
            
            logger.info(f"filterinformation {output_file} output")
            
        except Exception as e:
            logger.error(f"Markdownoutputerror: {e}")
    
    def export_to_json(self, filters: List[FilterParameter], output_file: str = 'finviz_elite_filters.json'):
        """filterinformationJSONexport as format"""
        try:
            filter_data = []
            
            for filter_param in filters:
                options_data = []
                for option in filter_param.options:
                    options_data.append({
                        'value': option.value,
                        'label': option.label,
                        'group': option.group
                    })
                
                filter_data.append({
                    'name': filter_param.name,
                    'id': filter_param.id,
                    'data_filter': filter_param.data_filter,
                    'selected_value': filter_param.selected_value,
                    'options': options_data
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(filter_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"filterinformation {output_file} output")
            
        except Exception as e:
            logger.error(f"JSONoutputerror: {e}")
    
    def analyze_specific_filter(self, data_filter: str) -> Optional[FilterParameter]:
        """filterdetailsanalysis"""
        try:
            filters = self.extract_filter_parameters()
            
            for filter_param in filters:
                if filter_param.data_filter == data_filter:
                    logger.info(f"filter '{data_filter}' details:")
                    logger.info(f"  : {filter_param.name}")
                    logger.info(f"  ID: {filter_param.id}")
                    logger.info(f"  value: {filter_param.selected_value}")
                    logger.info(f"  : {len(filter_param.options)}")
                    
                    return filter_param
            
            logger.warning(f"filter '{data_filter}' ")
            return None
            
        except Exception as e:
            logger.error(f"filteranalysiserror: {e}")
            return None
    
    def run_full_analysis(self, username: str, password: str, export_format: str = 'both'):
        """completefilteranalysisrun"""
        try:
            # Selenium
            if not self.setup_selenium_driver():
                return False
            
            # login
            if not self.login_with_selenium(username, password):
                return False
            
            # 
            if not self.navigate_to_screener():
                return False
            
            # filteranalysis
            filters = self.extract_filter_parameters()
            
            if not filters:
                logger.error("filterdetect")
                return False
            
            # resultsoutput
            if export_format in ['markdown', 'both']:
                self.export_to_markdown(filters)
            
            if export_format in ['json', 'both']:
                self.export_to_json(filters)
            
            # statistics
            categorized = self.categorize_filters(filters)
            logger.info("=== analysisresultsstatistics ===")
            for category, category_filters in categorized.items():
                if category_filters:
                    logger.info(f"{category}: {len(category_filters)} itemsfilter")
            
            return True
            
        except Exception as e:
            logger.error(f"completeanalysisrunerror: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """mainrunfunction"""
    import getpass
    
    print("=== Finviz Elite filteranalysistool ===")
    print()
    
    # logininformation
    username = input("Finviz Elite username: ")
    password = getpass.getpass("Finviz Elite password: ")
    
    # analysisrun
    analyzer = FinvizEliteAnalyzer()
    
    print("\nfilteranalysisstart...")
    success = analyzer.run_full_analysis(username, password, export_format='both')
    
    if success:
        print("\n✅ analysiscompleted")
        print("📄 finviz_elite_filters.md - Markdownformatdetails")
        print("📊 finviz_elite_filters.json - JSONformat")
    else:
        print("\n❌ analysisfailed。informationcheck。")

if __name__ == "__main__":
    main() 