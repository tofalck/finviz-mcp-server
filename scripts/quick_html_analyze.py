#!/usr/bin/env python3
"""
Finviz HTML quick analysis script

Finviz HTMLfileanalysis
"""

import sys
import os
from pathlib import Path

# 
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from finviz_html_analyzer import FinvizHTMLAnalyzer
except ImportError as e:
    print(f"❌ importerror: {e}")
    print(":")
    print("pip install beautifulsoup4 lxml")
    sys.exit(1)

def quick_html_analyze(html_file: str = None):
    """HTMLanalysisrun"""
    print("🔍 Finviz HTML filter quickanalysis")
    print("=" * 50)
    
    # HTMLfilecheck
    if html_file is None:
        # default
        default_files = [
            'finviz_screen_page.html',
            '../docs/finviz_screen_page.html',
            'finviz_elite_page.html',
            '../finviz_screen_page.html'
        ]
        
        found_file = None
        for file_path in default_files:
            if os.path.exists(file_path):
                found_file = file_path
                break
        
        if found_file:
            html_file = found_file
        else:
            print("❌ HTMLfile。")
            print("\nor lessfile:")
            for file_path in default_files:
                print(f"  - {file_path}")
            
            # 
            custom_path = input("\n、HTMLfile: ").strip()
            if custom_path and os.path.exists(custom_path):
                html_file = custom_path
            else:
                print("❌ HTMLfile")
                return False
    
    print(f"📄 HTMLfile: {html_file}")
    
    try:
        # analysisinitialize
        analyzer = FinvizHTMLAnalyzer(html_file)
        
        print("🔄 analysis...")
        
        # analysisrun
        success = analyzer.analyze(export_format='both')
        
        if success:
            print("\n✅ analysiscompleted")
            
            # outputfilecheck
            stem = Path(html_file).stem
            
            md_file = f"finviz_filters_analysis_{stem}.md"
            json_file = f"finviz_filters_analysis_{stem}.json"
            
            if os.path.exists(md_file):
                size = os.path.getsize(md_file) / 1024
                print(f"📄 {md_file} ({size:.1f} KB)")
            
            if os.path.exists(json_file):
                size = os.path.getsize(json_file) / 1024
                print(f"📊 {json_file} ({size:.1f} KB)")
            
            print("\n💡 usage:")
            print(f"  - Markdown: {md_file} parameterlistcheck")
            print(f"  - JSON: {json_file} check")
            
            return True
        else:
            print("\n❌ analysisfailed")
            return False
            
    except FileNotFoundError as e:
        print(f"❌ fileerror: {e}")
        return False
    except Exception as e:
        print(f"❌ unexpectederror: {e}")
        return False

def main():
    """mainrunfunction"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Finviz HTML quickanalysistool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python quick_html_analyze.py
  python quick_html_analyze.py finviz_screen_page.html
  python quick_html_analyze.py ../docs/finviz_screen_page.html
        """
    )
    
    parser.add_argument(
        'html_file',
        nargs='?',
        help='analysisHTMLfile ()'
    )
    
    args = parser.parse_args()
    
    success = quick_html_analyze(args.html_file)
    
    if not success:
        print("\n🔧 :")
        print("1. HTMLfilecheck")
        print("2. check:")
        print("   pip install beautifulsoup4 lxml")
        print("3. HTMLfileFinvizcheck")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 