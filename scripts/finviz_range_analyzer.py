#!/usr/bin/env python3
"""
Finviz custom range analysis script

Finvizcustomrange(manual range input)URLanalysis。
filteranalysis、rangeURLextract。

Usage:
    python finviz_range_analyzer.py [html_file_path]
"""

from bs4 import BeautifulSoup
import json
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import sys
import os
from pathlib import Path
import argparse
import logging

# HTMLimport
try:
    from finviz_html_analyzer import FinvizHTMLAnalyzer, FilterParameter, FilterOption
except ImportError:
    print("❌ finviz_html_analyzer.py ")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class RangePattern:
    """customrange"""
    filter_name: str
    parameter_name: str
    range_type: str  # 'numeric', 'percentage', 'currency', 'volume', 'date'
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    unit: Optional[str] = None
    url_pattern: Optional[str] = None
    example_values: List[str] = None

@dataclass
class CustomInputField:
    """custom"""
    field_id: str
    field_type: str
    associated_filter: str
    placeholder: Optional[str] = None
    validation_pattern: Optional[str] = None

class FinvizRangeAnalyzer(FinvizHTMLAnalyzer):
    """Finviz customrangeanalysis(HTML)"""
    
    def __init__(self, html_file_path: str):
        super().__init__(html_file_path)
        self.range_patterns = []
        self.custom_inputs = []
        
        # rangeparameter
        self.known_range_patterns = {
            'sh_price': {
                'type': 'currency',
                'unit': 'USD',
                'examples': ['10to50', '5to20', '1to10', '20to100'],
                'format': 'Price: ${min} to ${max}'
            },
            'cap': {
                'type': 'currency',
                'unit': 'USD (Billions)',
                'examples': ['1to10', '10to50', '2to20'],
                'format': 'Market Cap: ${min}B to ${max}B'
            },
            'sh_avgvol': {
                'type': 'volume',
                'unit': 'K shares',
                'examples': ['100to500', '500to1000', '1000to5000'],
                'format': 'Volume: {min}K to {max}K'
            },
            'fa_pe': {
                'type': 'numeric',
                'unit': 'ratio',
                'examples': ['5to20', '10to30', '15to25'],
                'format': 'P/E: {min} to {max}'
            },
            'fa_div': {
                'type': 'percentage',
                'unit': '%',
                'examples': ['2to5', '5to10', '1to3'],
                'format': 'Dividend: {min}% to {max}%'
            },
            'sh_relvol': {
                'type': 'numeric',
                'unit': 'multiplier',
                'examples': ['1to3', '2to5', '0.5to2'],
                'format': 'Rel Volume: {min}x to {max}x'
            },
            'ta_perf': {
                'type': 'percentage',
                'unit': '%',
                'examples': ['5to20', '-10to10', '10to50'],
                'format': 'Performance: {min}% to {max}%'
            },
            'fa_pb': {
                'type': 'numeric',
                'unit': 'ratio',
                'examples': ['1to5', '0.5to3', '2to10'],
                'format': 'P/B: {min} to {max}'
            },
            'fa_ps': {
                'type': 'numeric',
                'unit': 'ratio',
                'examples': ['1to10', '0.5to5', '2to20'],
                'format': 'P/S: {min} to {max}'
            },
            'fa_roe': {
                'type': 'percentage',
                'unit': '%',
                'examples': ['10to30', '15to50', '5to25'],
                'format': 'ROE: {min}% to {max}%'
            },
            'fa_roa': {
                'type': 'percentage',
                'unit': '%',
                'examples': ['5to20', '10to30', '2to15'],
                'format': 'ROA: {min}% to {max}%'
            },
            'fa_roi': {
                'type': 'percentage',
                'unit': '%',
                'examples': ['10to30', '15to40', '5to25'],
                'format': 'ROI: {min}% to {max}%'
            },
            'fa_curratio': {
                'type': 'numeric',
                'unit': 'ratio',
                'examples': ['1to5', '2to10', '0.5to3'],
                'format': 'Current Ratio: {min} to {max}'
            },
            'fa_quickratio': {
                'type': 'numeric',
                'unit': 'ratio',
                'examples': ['0.5to3', '1to5', '0.2to2'],
                'format': 'Quick Ratio: {min} to {max}'
            },
            'fa_debteq': {
                'type': 'numeric',
                'unit': 'ratio',
                'examples': ['0to1', '0.5to2', '1to5'],
                'format': 'Debt/Eq: {min} to {max}'
            },
            'fa_ltdebteq': {
                'type': 'numeric',
                'unit': 'ratio',
                'examples': ['0to0.5', '0.5to2', '1to3'],
                'format': 'LT Debt/Eq: {min} to {max}'
            },
            'fa_grossmargin': {
                'type': 'percentage',
                'unit': '%',
                'examples': ['20to60', '30to80', '10to40'],
                'format': 'Gross Margin: {min}% to {max}%'
            },
            'fa_opermargin': {
                'type': 'percentage',
                'unit': '%',
                'examples': ['5to30', '10to50', '0to20'],
                'format': 'Oper Margin: {min}% to {max}%'
            },
            'fa_profitmargin': {
                'type': 'percentage',
                'unit': '%',
                'examples': ['5to30', '10to40', '0to20'],
                'format': 'Profit Margin: {min}% to {max}%'
            },
            'ta_beta': {
                'type': 'numeric',
                'unit': 'coefficient',
                'examples': ['0.5to1.5', '1to2', '0to1'],
                'format': 'Beta: {min} to {max}'
            },
            'ta_volatility': {
                'type': 'percentage',
                'unit': '%',
                'examples': ['5to15', '10to30', '2to10'],
                'format': 'Volatility: {min}% to {max}%'
            }
        }
    
    def extract_custom_input_fields(self) -> List[CustomInputField]:
        """customextract"""
        try:
            soup = self.load_html()
            custom_inputs = []
            
            # inputfilterrelated
            input_patterns = [
                {'type': 'text', 'class': re.compile(r'.*range.*|.*custom.*')},
                {'type': 'number'},
                {'id': re.compile(r'.*_min|.*_max|.*_from|.*_to')},
                {'name': re.compile(r'.*_min|.*_max|.*_from|.*_to')},
            ]
            
            for pattern in input_patterns:
                inputs = soup.find_all('input', pattern)
                for input_elem in inputs:
                    input_id = input_elem.get('id', '')
                    input_type = input_elem.get('type', '')
                    placeholder = input_elem.get('placeholder', '')
                    pattern_attr = input_elem.get('pattern', '')
                    
                    # relatedfilter
                    associated_filter = self._guess_associated_filter(input_id, placeholder)
                    
                    if associated_filter or input_id:
                        custom_input = CustomInputField(
                            field_id=input_id,
                            field_type=input_type,
                            associated_filter=associated_filter,
                            placeholder=placeholder,
                            validation_pattern=pattern_attr
                        )
                        custom_inputs.append(custom_input)
            
            logger.info(f"{len(custom_inputs)} itemscustomdetect")
            return custom_inputs
            
        except Exception as e:
            logger.error(f"customextracterror: {e}")
            return []
    
    def _guess_associated_filter(self, input_id: str, placeholder: str) -> str:
        """relatedfilter"""
        search_text = f"{input_id} {placeholder}".lower()
        
        filter_keywords = {
            'sh_price': ['price', 'dollar', '$'],
            'cap': ['market cap', 'capitalization', 'cap'],
            'sh_avgvol': ['volume', 'vol'],
            'fa_pe': ['p/e', 'pe ratio', 'price earnings'],
            'fa_div': ['dividend', 'yield'],
            'sh_relvol': ['relative volume', 'rel vol'],
            'ta_perf': ['performance', 'perf'],
            'fa_pb': ['p/b', 'pb ratio', 'price book'],
            'fa_ps': ['p/s', 'ps ratio', 'price sales'],
            'fa_roe': ['roe', 'return on equity'],
        }
        
        for filter_name, keywords in filter_keywords.items():
            if any(keyword in search_text for keyword in keywords):
                return filter_name
        
        return ''
    
    def analyze_data_url_patterns(self, filters: List[FilterParameter]) -> List[RangePattern]:
        """data-urlattributecustomrangeanalysis"""
        range_patterns = []
        
        for filter_param in filters:
            if not filter_param.data_url and not filter_param.data_url_selected:
                continue
            
            # data-urlrangeextract
            urls_to_analyze = []
            if filter_param.data_url:
                urls_to_analyze.append(filter_param.data_url)
            if filter_param.data_url_selected:
                urls_to_analyze.append(filter_param.data_url_selected)
            
            for url in urls_to_analyze:
                patterns = self._extract_range_patterns_from_url(url, filter_param.data_filter)
                range_patterns.extend(patterns)
        
        return range_patterns
    
    def _extract_range_patterns_from_url(self, url: str, filter_name: str) -> List[RangePattern]:
        """URLrangeextract"""
        patterns = []
        
        # URLfilteranalysis
        if 'f=' in url:
            filter_part = url.split('f=')[1].split('&')[0]
            filter_items = filter_part.split(',')
            
            for item in filter_items:
                if filter_name in item:
                    # range
                    range_match = re.search(r'(\d+(?:\.\d+)?)to(\d+(?:\.\d+)?)', item)
                    if range_match:
                        min_val, max_val = range_match.groups()
                        
                        # detailsinformationfetch
                        pattern_info = self.known_range_patterns.get(filter_name, {})
                        
                        pattern = RangePattern(
                            filter_name=filter_name,
                            parameter_name=item,
                            range_type=pattern_info.get('type', 'numeric'),
                            min_value=min_val,
                            max_value=max_val,
                            unit=pattern_info.get('unit'),
                            url_pattern=item,
                            example_values=pattern_info.get('examples', [])
                        )
                        patterns.append(pattern)
        
        return patterns
    
    def generate_range_examples(self, filter_name: str) -> List[Dict[str, str]]:
        """filterrangeexample"""
        if filter_name not in self.known_range_patterns:
            return []
        
        pattern_info = self.known_range_patterns[filter_name]
        examples = []
        
        for example in pattern_info.get('examples', []):
            if 'to' in example:
                min_val, max_val = example.split('to')
                url_param = f"{filter_name}_{example}"
                description = pattern_info['format'].format(min=min_val, max=max_val)
                
                examples.append({
                    'range': example,
                    'url_parameter': url_param,
                    'description': description,
                    'full_url_example': f"https://finviz.com/screener.ashx?v=111&f={url_param}"
                })
        
        return examples
    
    def export_range_analysis_to_markdown(self, filters: List[FilterParameter], output_file: str = None):
        """customrangeanalysisresultsMarkdownexport as format"""
        if output_file is None:
            output_file = f"finviz_range_analysis_{self.html_file_path.stem}.md"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Finviz customrangerange detailsanalysis\n\n")
                f.write(f"HTMLfile: `{self.html_file_path.name}`\n\n")
                f.write("、Finvizcustomrange(manual range input)URLdetailsanalysisresults。\n\n")
                
                # customrangefilterlist
                f.write("## 🎯 customrangefilterlist\n\n")
                
                range_capable_filters = []
                for filter_param in filters:
                    has_custom = any(opt.value in ['frange', 'modal', 'custom'] for opt in filter_param.options)
                    if has_custom:
                        range_capable_filters.append(filter_param)
                
                f.write(f"detectcustomrangefilter: **{len(range_capable_filters)} items**\n\n")
                
                for filter_param in range_capable_filters:
                    f.write(f"### {filter_param.name} - `{filter_param.data_filter}`\n")
                    
                    # customrangeexample
                    examples = self.generate_range_examples(filter_param.data_filter)
                    
                    if examples:
                        f.write("#### 📊 rangeexample\n\n")
                        f.write("| range | URLparameter | description | completeURLexample |\n")
                        f.write("|---|---|---|---|\n")
                        
                        for example in examples[:3]:  # top3example
                            f.write(f"| `{example['range']}` | `{example['url_parameter']}` | {example['description']} | `{example['full_url_example']}` |\n")
                        
                        f.write("\n")
                    
                    # information
                    if filter_param.data_filter in self.known_range_patterns:
                        pattern_info = self.known_range_patterns[filter_param.data_filter]
                        f.write(f"- ****: {pattern_info['type']}\n")
                        f.write(f"- ****: {pattern_info['unit']}\n")
                        f.write(f"- ****: {pattern_info['format']}\n")
                    
                    f.write("\n")
                
                # URLanalysis
                f.write("## 🔗 URLanalysis\n\n")
                f.write("### \n")
                f.write("```\n")
                f.write("https://finviz.com/screener.ashx?v=111&f=[filter1],[filter2],[filter3]\n")
                f.write("```\n\n")
                
                f.write("### customrange\n")
                f.write("| filter |  | example |\n")
                f.write("|---|---|---|\n")
                
                for filter_name, pattern_info in self.known_range_patterns.items():
                    example = pattern_info['examples'][0] if pattern_info['examples'] else 'XtoY'
                    f.write(f"| `{filter_name}` | `{filter_name}_{{min}}to{{max}}` | `{filter_name}_{example}` |\n")
                
                f.write("\n")
                
                # examples
                f.write("## 💡 examples\n\n")
                
                practical_examples = [
                    {
                        'title': 'pricerange $10-$50stocks',
                        'url': 'https://finviz.com/screener.ashx?v=111&f=sh_price_10to50',
                        'description': 'stock price$10$50rangestocks'
                    },
                    {
                        'title': 'market cap $1B-$10Bmid',
                        'url': 'https://finviz.com/screener.ashx?v=111&f=cap_1to10',
                        'description': 'market cap$1B$10Bmid'
                    },
                    {
                        'title': 'PER 10-20',
                        'url': 'https://finviz.com/screener.ashx?v=111&f=fa_pe_10to20',
                        'description': 'PER1020stocks'
                    },
                    {
                        'title': 'dividend yield 3-7%highdividend',
                        'url': 'https://finviz.com/screener.ashx?v=111&f=fa_div_3to7',
                        'description': 'dividend yield3%7%highdividendstocks'
                    },
                    {
                        'title': ' items: technology × mid × PER',
                        'url': 'https://finviz.com/screener.ashx?v=111&f=sec_technology,cap_1to10,fa_pe_10to25',
                        'description': 'technologysectormidPER10-25'
                    }
                ]
                
                for i, example in enumerate(practical_examples, 1):
                    f.write(f"### {i}. {example['title']}\n")
                    f.write(f"**URL**: `{example['url']}`\n\n")
                    f.write(f"**description**: {example['description']}\n\n")
                
                # range
                f.write("## 🎯 range\n\n")
                f.write("### 📈 value\n")
                f.write("- ****: `10to50` (1050)\n")
                f.write("- ****: `1.5to3.5` (1.53.5)\n")
                f.write("- ****: `-10to10` (-10%+10%)\n\n")
                
                f.write("### 💰 \n")
                f.write("- **stock price**:  `sh_price_10to50` ($10-$50)\n")
                f.write("- **market cap**: 10 `cap_1to10` ($1B-$10B)\n")
                f.write("- **volume**:  `sh_avgvol_100to500` (100K-500K)\n\n")
                
                f.write("### ⚠️ notes\n")
                f.write("- minimumvaluemaximumvalue\n")
                f.write("- valueresults0 items\n")
                f.write("- filterrange\n\n")
            
            logger.info(f"customrangeanalysisresults {output_file} output")
            
        except Exception as e:
            logger.error(f"rangeanalysisMarkdownoutputerror: {e}")
    
    def analyze_with_ranges(self, export_format: str = 'both'):
        """completeanalysis(range)run"""
        try:
            logger.info("filterrangeanalysisstart...")
            
            # filterextract
            filters = self.extract_filter_parameters()
            
            if not filters:
                logger.error("filterdetect")
                return False
            
            # summary
            self.print_range_summary(filters)
            
            # resultsoutput
            if export_format in ['markdown', 'both']:
                self.export_to_markdown(filters)
                self.export_range_analysis_to_markdown(filters)
            
            if export_format in ['json', 'both']:
                self.export_to_json(filters)
                self.export_range_analysis_to_json(filters)
            
            return True
            
        except Exception as e:
            logger.error(f"rangeanalysisrunerror: {e}")
            return False
    
    def export_range_analysis_to_json(self, filters: List[FilterParameter], output_file: str = None):
        """rangeanalysisresultsJSONexport as format"""
        if output_file is None:
            output_file = f"finviz_range_analysis_{self.html_file_path.stem}.json"
        
        try:
            range_data = {
                'source_file': str(self.html_file_path),
                'analysis_type': 'custom_range_patterns',
                'range_capable_filters': [],
                'url_patterns': {},
                'practical_examples': []
            }
            
            # rangefilter
            for filter_param in filters:
                has_custom = any(opt.value in ['frange', 'modal', 'custom'] for opt in filter_param.options)
                if has_custom:
                    examples = self.generate_range_examples(filter_param.data_filter)
                    
                    filter_info = {
                        'name': filter_param.name,
                        'data_filter': filter_param.data_filter,
                        'range_examples': examples,
                        'known_pattern': filter_param.data_filter in self.known_range_patterns
                    }
                    
                    if filter_param.data_filter in self.known_range_patterns:
                        pattern_info = self.known_range_patterns[filter_param.data_filter]
                        filter_info.update({
                            'data_type': pattern_info['type'],
                            'unit': pattern_info['unit'],
                            'format': pattern_info['format']
                        })
                    
                    range_data['range_capable_filters'].append(filter_info)
            
            # URL
            for filter_name, pattern_info in self.known_range_patterns.items():
                range_data['url_patterns'][filter_name] = {
                    'pattern': f"{filter_name}_{{min}}to{{max}}",
                    'examples': pattern_info['examples'],
                    'type': pattern_info['type'],
                    'unit': pattern_info['unit']
                }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(range_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"rangeanalysisresults {output_file} output")
            
        except Exception as e:
            logger.error(f"rangeanalysisJSONoutputerror: {e}")
    
    def print_range_summary(self, filters: List[FilterParameter]):
        """rangeanalysisresultssummary"""
        print("\n" + "="*70)
        print("📊 Finviz customrangerangeanalysisresultssummary")
        print("="*70)
        
        range_capable = [f for f in filters if any(opt.value in ['frange', 'modal', 'custom'] for opt in f.options)]
        
        print(f"📄 file: {self.html_file_path.name}")
        print(f"🔢 filter: {len(filters)}")
        print(f"🎯 rangefilter: {len(range_capable)}")
        print(f"🔗 range: {len(self.known_range_patterns)}")
        
        if range_capable:
            print(f"\n🎯 rangefilter:")
            for filter_param in range_capable[:10]:  # top10 items
                examples_count = len(self.generate_range_examples(filter_param.data_filter))
                print(f"  📈 {filter_param.name}: {examples_count} itemsexample")
        
        print("\n💡 rangeURLexample:")
        example_urls = [
            "sh_price_10to50 → stock price $10-$50",
            "cap_1to10 → market cap $1B-$10B", 
            "fa_pe_10to20 → PER 10-20",
            "fa_div_3to7 → dividend yield 3-7%"
        ]
        for example in example_urls:
            print(f"  🔗 {example}")
        
        print("\n" + "="*70)

def main():
    """mainrunfunction"""
    parser = argparse.ArgumentParser(
        description='Finviz customrangeanalysistool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python finviz_range_analyzer.py
  python finviz_range_analyzer.py ../docs/finviz_screen_page.html
  python finviz_range_analyzer.py --format json
        """
    )
    
    parser.add_argument(
        'html_file',
        nargs='?',
        default='../docs/finviz_screen_page.html',
        help='analysisHTMLfile'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'json', 'both'],
        default='both',
        help='outputformat (default: both)'
    )
    
    args = parser.parse_args()
    
    print("🎯 Finviz customrangerangeanalysistool")
    print("="*60)
    
    try:
        # analysisinitialize
        analyzer = FinvizRangeAnalyzer(args.html_file)
        
        # analysisrun
        success = analyzer.analyze_with_ranges(export_format=args.format)
        
        if success:
            print("\n✅ rangeanalysiscompleted")
            
            # outputfilecheck
            stem = Path(args.html_file).stem
            
            if args.format in ['markdown', 'both']:
                range_md_file = f"finviz_range_analysis_{stem}.md"
                if os.path.exists(range_md_file):
                    size = os.path.getsize(range_md_file) / 1024
                    print(f"📄 {range_md_file} ({size:.1f} KB)")
            
            if args.format in ['json', 'both']:
                range_json_file = f"finviz_range_analysis_{stem}.json"
                if os.path.exists(range_json_file):
                    size = os.path.getsize(range_json_file) / 1024
                    print(f"📊 {range_json_file} ({size:.1f} KB)")
        else:
            print("\n❌ rangeanalysisfailed")
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