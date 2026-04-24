#!/usr/bin/env python3
"""
Finviz HTML file analysis script

Finviz HTMLfileanalysis、
filtervaluedetailsanalysis。

Usage:
    python finviz_html_analyzer.py [html_file_path]
"""

from bs4 import BeautifulSoup
import json
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
import sys
import os
from pathlib import Path
import argparse
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
    data_url: Optional[str] = None
    data_url_selected: Optional[str] = None

class FinvizHTMLAnalyzer:
    """Finviz HTMLanalysis"""
    
    def __init__(self, html_file_path: str):
        self.html_file_path = Path(html_file_path)
        self.filters = []
        
        # excludefilter( items)
        self.excluded_filters = {
            'screenerpresetsselect',     # 
            'screenerpresets',           # 
            'fs_screenerpresetsselect',  # ID
            'fs_screenerpresets',        # ID
        }
        
        if not self.html_file_path.exists():
            raise FileNotFoundError(f"HTMLfile: {html_file_path}")
        
        logger.info(f"excludefilter: {', '.join(self.excluded_filters)}")
    
    def load_html(self) -> BeautifulSoup:
        """HTMLfileload"""
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            logger.info(f"HTMLfileload: {self.html_file_path}")
            return soup
            
        except UnicodeDecodeError:
            # UTF-8、
            try:
                with open(self.html_file_path, 'r', encoding='iso-8859-1') as f:
                    html_content = f.read()
                soup = BeautifulSoup(html_content, 'html.parser')
                logger.info(f"HTMLfileloadsuccess (iso-8859-1): {self.html_file_path}")
                return soup
            except Exception as e:
                logger.error(f"HTMLfileloaderror: {e}")
                raise
        except Exception as e:
            logger.error(f"HTMLfileloaderror: {e}")
            raise
    
    def extract_filter_parameters(self) -> List[FilterParameter]:
        """filterparameterextract"""
        try:
            soup = self.load_html()
            filters = []
            
            # selectfilter(multiple)
            select_patterns = [
                {'class': re.compile(r'screener-combo')},
                {'class': re.compile(r'fv-select')},
                {'class': re.compile(r'screener.*combo')},
                {'id': re.compile(r'^fs_')},  # IDfs_
            ]
            
            found_selects = set()  # 
            
            for pattern in select_patterns:
                selects = soup.find_all('select', pattern)
                for select in selects:
                    select_id = select.get('id', '')
                    if select_id and select_id not in found_selects:
                        found_selects.add(select_id)
                        try:
                            filter_param = self._parse_select_element(select)
                            if filter_param:
                                filters.append(filter_param)
                        except Exception as e:
                            logger.warning(f"selectanalysiserror ({select_id}): {e}")
                            continue
            
            # data-filterattributeselect
            data_filter_selects = soup.find_all('select', attrs={'data-filter': True})
            for select in data_filter_selects:
                select_id = select.get('id', '')
                if select_id and select_id not in found_selects:
                    found_selects.add(select_id)
                    try:
                        filter_param = self._parse_select_element(select)
                        if filter_param:
                            filters.append(filter_param)
                    except Exception as e:
                        logger.warning(f"data-filter selectanalysiserror ({select_id}): {e}")
                        continue
            
            logger.info(f"{len(filters)} itemsfilterparameterdetect")
            
            # filterdata-filter
            filters.sort(key=lambda x: x.data_filter)
            
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
            data_url = select.get('data-url', '')
            data_url_selected = select.get('data-url-selected', '')
            
            if not data_filter and not select_id:
                return None
            
            # data-filter、ID
            if not data_filter and select_id.startswith('fs_'):
                data_filter = select_id[3:]  # fs_
            
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
                    
                    # 
                    if not label:
                        continue
                    
                    option = FilterOption(
                        value=value,
                        label=label,
                        group=current_group
                    )
                    options.append(option)
            
            # valuefetch
            selected_option = select.find('option', selected=True)
            if not selected_option:
                # data-selectedattribute
                selected_value = select.get('data-selected', '')
            else:
                selected_value = selected_option.get('value', '')
            
            return FilterParameter(
                name=self._get_filter_name_from_id(select_id, data_filter),
                id=select_id,
                data_filter=data_filter,
                options=options,
                selected_value=selected_value,
                data_url=data_url,
                data_url_selected=data_url_selected
            )
            
        except Exception as e:
            logger.warning(f"selectanalysiserror: {e}")
            return None
    
    def _get_filter_name_from_id(self, element_id: str, data_filter: str = '') -> str:
        """element IDdata-filterfilter"""
        # ID → ()
        id_to_name = {
            'fs_exch': 'Exchange (exchange)',
            'fs_idx': 'Index (index)',
            'fs_sec': 'Sector (sector)',
            'fs_ind': 'Industry (industry)',
            'fs_geo': 'Country (country)',
            'fs_cap': 'Market Cap (market cap)',
            'fs_sh_price': 'Price (stock price)',
            'fs_fa_div': 'Dividend Yield (dividend yield)',
            'fs_fa_epsrev': 'EPS/Revenue Revision (EPS)',
            'fs_sh_short': 'Short Float (short)',
            'fs_an_recom': 'Analyst Recommendation (analystrecommendation)',
            'fs_sh_opt': 'Option/Short (/short)',
            'fs_earningsdate': 'Earnings Date (earnings)',
            'fs_ipodate': 'IPO Date (IPO)',
            'fs_sh_avgvol': 'Average Volume (averagevolume)',
            'fs_sh_relvol': 'Relative Volume (relativevolume)',
            'fs_sh_curvol': 'Current Volume (volume)',
            'fs_sh_trades': 'Trades (trade count)',
            'fs_sh_outstanding': 'Shares Outstanding (shares outstanding)',
            'fs_sh_float': 'Float (float shares)',
            'fs_ta_perf2': 'Performance 2 (performance 2)',
            'fs_ta_perf': 'Performance (performance)',
            'fs_targetprice': 'Target Price (stock price)',
            'fs_ta_highlow52w': '52W High/Low (52highvalue/value)',
            'fs_ta_sma20': 'SMA20 (20day movingaverage)',
            'fs_ta_sma50': 'SMA50 (50day movingaverage)',
            'fs_ta_sma200': 'SMA200 (200day movingaverage)',
            'fs_ta_change': 'Change ()',
            'fs_ta_volume': 'Volume (volume)',
            'fs_fa_pe': 'P/E Ratio (PER)',
            'fs_fa_peg': 'PEG Ratio (PEG)',
            'fs_fa_ps': 'P/S Ratio (PSR)',
            'fs_fa_pb': 'P/B Ratio (PBR)',
            'fs_fa_pc': 'P/C Ratio (PCR)',
            'fs_fa_pfcf': 'P/FCF Ratio (P/FCF)',
            'fs_fa_epsyoy': 'EPS Growth YoY (EPSgrowth)',
            'fs_fa_epsqoq': 'EPS Growth QoQ (EPSgrowth)',
            'fs_fa_salesyoy': 'Sales Growth YoY (growth)',
            'fs_fa_salesqoq': 'Sales Growth QoQ (growth)',
            'fs_fa_eps5y': 'EPS Growth 5Y (EPS5growth)',
            'fs_fa_sales5y': 'Sales Growth 5Y (5growth)',
            'fs_fa_roe': 'ROE',
            'fs_fa_roa': 'ROA',
            'fs_fa_roi': 'ROI',
            'fs_fa_curratio': 'Current Ratio ()',
            'fs_fa_quickratio': 'Quick Ratio ()',
            'fs_fa_ltdebt': 'LT Debt/Eq ()',
            'fs_fa_debt': 'Debt/Eq ()',
            'fs_fa_grossmargin': 'Gross Margin ()',
            'fs_fa_opermargin': 'Operating Margin ()',
            'fs_fa_profitmargin': 'Profit Margin ()',
            'fs_fa_payout': 'Payout Ratio (dividend)',
            'fs_fa_insiderown': 'Insider Own ()',
            'fs_fa_insidertrans': 'Insider Trans ()',
            'fs_fa_insthold': 'Inst Hold ()',
            'fs_fa_insttrans': 'Inst Trans ()',
        }
        
        # data-filter → 
        filter_to_name = {
            'exch': 'Exchange (exchange)',
            'idx': 'Index (index)',
            'sec': 'Sector (sector)',
            'ind': 'Industry (industry)',
            'geo': 'Country (country)',
            'cap': 'Market Cap (market cap)',
            'sh_price': 'Price (stock price)',
            'fa_div': 'Dividend Yield (dividend yield)',
            'fa_epsrev': 'EPS/Revenue Revision (EPS)',
            'sh_short': 'Short Float (short)',
            'an_recom': 'Analyst Recommendation (analystrecommendation)',
            'sh_opt': 'Option/Short (/short)',
            'earningsdate': 'Earnings Date (earnings)',
            'ipodate': 'IPO Date (IPO)',
            'sh_avgvol': 'Average Volume (averagevolume)',
            'sh_relvol': 'Relative Volume (relativevolume)',
            'sh_curvol': 'Current Volume (volume)',
            'sh_trades': 'Trades (trade count)',
            'sh_outstanding': 'Shares Outstanding (shares outstanding)',
            'sh_float': 'Float (float shares)',
            'ta_perf2': 'Performance 2 (performance 2)',
            'ta_perf': 'Performance (performance)',
            'targetprice': 'Target Price (stock price)',
        }
        
        # IDfetch
        if element_id in id_to_name:
            return id_to_name[element_id]
        
        # data-filterfetch
        if data_filter in filter_to_name:
            return filter_to_name[data_filter]
        
        # 
        if element_id:
            return element_id.replace('fs_', '').replace('_', ' ').title()
        elif data_filter:
            return data_filter.replace('_', ' ').title()
        else:
            return 'Unknown Filter'
    
    def categorize_filters(self, filters: List[FilterParameter]) -> Dict[str, List[FilterParameter]]:
        """filtercategory"""
        categories = {
            'basic informationtypeparameter': [],
            'stock pricemarket captypeparameter': [],
            'dividendtypeparameter': [],
            'analystrecommendationtypeparameter': [],
            'datetypeparameter': [],
            'volumetypeparameter': [],
            'share issuancetypeparameter': [],
            'technical analysistypeparameter': [],
            'otherparameter': []
        }
        
        category_keywords = {
            'basic informationtypeparameter': ['exchange', 'index', 'sector', 'industry', 'country', 'exch', 'idx', 'sec', 'ind', 'geo'],
            'stock pricemarket captypeparameter': ['market cap', 'price', 'target price', 'cap', 'sh_price', 'targetprice'],
            'dividendtypeparameter': ['dividend', 'eps', 'revenue', 'short', 'pe', 'pb', 'ps', 'roe', 'roa', 'margin', 'debt', 'fa_'],
            'analystrecommendationtypeparameter': ['analyst', 'recommendation', 'an_recom'],
            'datetypeparameter': ['earnings date', 'ipo date', 'earningsdate', 'ipodate'],
            'volumetypeparameter': ['volume', 'trades', 'sh_avgvol', 'sh_relvol', 'sh_curvol', 'sh_trades'],
            'share issuancetypeparameter': ['shares', 'float', 'outstanding', 'sh_outstanding', 'sh_float'],
            'technical analysistypeparameter': ['performance', 'sma', 'change', 'high', 'low', 'ta_'],
        }
        
        for filter_param in filters:
            assigned = False
            search_text = f"{filter_param.name.lower()} {filter_param.data_filter.lower()}"
            
            for category, keywords in category_keywords.items():
                if any(keyword in search_text for keyword in keywords):
                    categories[category].append(filter_param)
                    assigned = True
                    break
            
            if not assigned:
                categories['otherparameter'].append(filter_param)
        
        return categories
    
    def export_to_markdown(self, filters: List[FilterParameter], output_file: str = None):
        """filterinformationMarkdownexport as format"""
        if output_file is None:
            output_file = f"finviz_filters_analysis_{self.html_file_path.stem}.md"
        
        try:
            categorized_filters = self.categorize_filters(filters)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Finviz filterparameterdetailslist\n\n")
                f.write(f"HTMLfile: `{self.html_file_path.name}`\n")
                f.write(f"analysis: {os.path.getctime(self.html_file_path)}\n\n")
                f.write("、Finvizscreeningparameterfetchvaluedetails。\n\n")
                
                for category, category_filters in categorized_filters.items():
                    if not category_filters:
                        continue
                        
                    f.write(f"## {category}\n\n")
                    
                    for filter_param in category_filters:
                        f.write(f"### {filter_param.name} - `{filter_param.data_filter}`\n")
                        
                        if filter_param.selected_value:
                            f.write(f"**value**: `{filter_param.selected_value}`\n\n")
                        
                        if filter_param.options:
                            # 
                            has_groups = any(option.group for option in filter_param.options)
                            
                            if has_groups:
                                f.write("| value | description |  |\n")
                                f.write("|---|---|---|\n")
                                
                                for option in filter_param.options:
                                    group = option.group or "-"
                                    f.write(f"| `{option.value}` | {option.label} | {group} |\n")
                            else:
                                f.write("| value | description |\n")
                                f.write("|---|---|\n")
                                
                                for option in filter_param.options:
                                    f.write(f"| `{option.value}` | {option.label} |\n")
                            
                            f.write("\n")
                        
                        # data-urlinformation
                        if filter_param.data_url:
                            f.write(f"**Data URL**: `{filter_param.data_url}`\n\n")
                        
                        f.write("\n")
                
                # usage
                f.write("## usage\n\n")
                f.write("parameter、FinvizscreeningURLparameter。\n\n")
                f.write("### example:\n")
                f.write("```\n")
                f.write("https://finviz.com/screener.ashx?v=111&f=cap_large,sec_technology,ta_perf_1w_o5\n")
                f.write("```\n\n")
                f.write("### multiple items:\n")
                f.write("- parametermultiple\n")
                f.write("- categoryparameter AND  items\n")
                f.write("- categorymultiplevalue OR  items(example)\n\n")
            
            logger.info(f"filterinformation {output_file} output")
            
        except Exception as e:
            logger.error(f"Markdownoutputerror: {e}")
    
    def export_to_json(self, filters: List[FilterParameter], output_file: str = None):
        """filterinformationJSONexport as format"""
        if output_file is None:
            output_file = f"finviz_filters_analysis_{self.html_file_path.stem}.json"
        
        try:
            filter_data = {
                'source_file': str(self.html_file_path),
                'total_filters': len(filters),
                'filters': []
            }
            
            for filter_param in filters:
                options_data = []
                for option in filter_param.options:
                    options_data.append({
                        'value': option.value,
                        'label': option.label,
                        'group': option.group
                    })
                
                filter_info = {
                    'name': filter_param.name,
                    'id': filter_param.id,
                    'data_filter': filter_param.data_filter,
                    'selected_value': filter_param.selected_value,
                    'options_count': len(options_data),
                    'options': options_data
                }
                
                # data-urlinformation
                if filter_param.data_url:
                    filter_info['data_url'] = filter_param.data_url
                if filter_param.data_url_selected:
                    filter_info['data_url_selected'] = filter_param.data_url_selected
                
                filter_data['filters'].append(filter_info)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(filter_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"filterinformation {output_file} output")
            
        except Exception as e:
            logger.error(f"JSONoutputerror: {e}")
    
    def print_summary(self, filters: List[FilterParameter]):
        """analysisresultssummary"""
        print("\n" + "="*60)
        print("📊 Finviz filteranalysisresultssummary")
        print("="*60)
        
        categorized = self.categorize_filters(filters)
        
        print(f"📄 file: {self.html_file_path.name}")
        print(f"🔢 filter: {len(filters)}")
        print(f"📂 category: {len([c for c, f in categorized.items() if f])}")
        
        print("\n📋 categorystatistics:")
        for category, category_filters in categorized.items():
            if category_filters:
                print(f"  📊 {category}: {len(category_filters)} items")
        
        # Top 5 filter()
        top_filters = sorted(filters, key=lambda x: len(x.options), reverse=True)[:5]
        print(f"\n🔝 top5filter:")
        for i, filter_param in enumerate(top_filters, 1):
            print(f"  {i}. {filter_param.name}: {len(filter_param.options)} items")
        
        print("\n" + "="*60)
    
    def analyze(self, export_format: str = 'both'):
        """completeanalysisrun"""
        try:
            logger.info("filteranalysisstart...")
            
            # filterextract
            filters = self.extract_filter_parameters()
            
            if not filters:
                logger.error("filterdetect")
                return False
            
            # summary
            self.print_summary(filters)
            
            # resultsoutput
            if export_format in ['markdown', 'both']:
                self.export_to_markdown(filters)
            
            if export_format in ['json', 'both']:
                self.export_to_json(filters)
            
            return True
            
        except Exception as e:
            logger.error(f"analysisrunerror: {e}")
            return False

def main():
    """mainrunfunction"""
    parser = argparse.ArgumentParser(
        description='Finviz HTMLfileanalysistool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python finviz_html_analyzer.py finviz_screen_page.html
  python finviz_html_analyzer.py finviz_screen_page.html --format json
  python finviz_html_analyzer.py finviz_screen_page.html --format markdown
        """
    )
    
    parser.add_argument(
        'html_file',
        nargs='?',
        default='finviz_screen_page.html',
        help='analysisHTMLfile (default: finviz_screen_page.html)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'json', 'both'],
        default='both',
        help='outputformat (default: both)'
    )
    
    args = parser.parse_args()
    
    print("🔍 Finviz HTML filteranalysistool")
    print("="*50)
    
    try:
        # analysisinitialize
        analyzer = FinvizHTMLAnalyzer(args.html_file)
        
        # analysisrun
        success = analyzer.analyze(export_format=args.format)
        
        if success:
            print("\n✅ analysiscompleted")
            
            # outputfilecheck
            stem = Path(args.html_file).stem
            
            if args.format in ['markdown', 'both']:
                md_file = f"finviz_filters_analysis_{stem}.md"
                if os.path.exists(md_file):
                    size = os.path.getsize(md_file) / 1024
                    print(f"📄 {md_file} ({size:.1f} KB)")
            
            if args.format in ['json', 'both']:
                json_file = f"finviz_filters_analysis_{stem}.json"
                if os.path.exists(json_file):
                    size = os.path.getsize(json_file) / 1024
                    print(f"📊 {json_file} ({size:.1f} KB)")
        else:
            print("\n❌ analysisfailed")
            return 1
            
    except FileNotFoundError as e:
        print(f"❌ fileerror: {e}")
        return 1
    except Exception as e:
        print(f"❌ unexpectederror: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 