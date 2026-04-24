#!/usr/bin/env python3
"""
Finviz custom range analysis - quick start

run:
  python quick_range_analyze.py

:
  cd scripts && python quick_range_analyze.py
"""

import os
import sys
from pathlib import Path

def main():
    print("🎯 Finviz custom range analysis - quick start")
    print("="*60)
    
    # HTMLfile
    possible_paths = [
        '../docs/finviz_screen_page.html',
        'docs/finviz_screen_page.html',
        'finviz_screen_page.html'
    ]
    
    html_file = None
    for path in possible_paths:
        if os.path.exists(path):
            html_file = path
            print(f"✅ HTMLfile: {path}")
            break
    
    if not html_file:
        print("❌ finviz_screen_page.html ")
        print("or lesscheck:")
        for path in possible_paths:
            print(f"  - {path}")
        return 1
    
    try:
        # finviz_range_analyzer.pyimport
        from finviz_range_analyzer import FinvizRangeAnalyzer
        
        print(f"📊 customrangeanalysisstart...")
        
        # analysisinitializerun
        analyzer = FinvizRangeAnalyzer(html_file)
        success = analyzer.analyze_with_ranges(export_format='both')
        
        if success:
            print("\n🎉 customrangeanalysiscompleted")
            
            # outputfilecheck
            stem = Path(html_file).stem
            output_files = [
                f"finviz_range_analysis_{stem}.md",
                f"finviz_range_analysis_{stem}.json"
            ]
            
            print("\n📁 outputfile:")
            for file in output_files:
                if os.path.exists(file):
                    size = os.path.getsize(file) / 1024
                    print(f"  ✅ {file} ({size:.1f} KB)")
                else:
                    print(f"  ❌ {file} ()")
            
            print("\n💡 customrangeURLexample:")
            print("  🔗 sh_price_10to50 → stock price $10-$50")
            print("  🔗 cap_1to10 → market cap $1B-$10B")
            print("  🔗 fa_pe_10to20 → PER 10-20")
            print("  🔗 fa_div_3to7 → dividend yield 3-7%")
            
            return 0
        else:
            print("\n❌ customrangeanalysisfailed")
            return 1
            
    except ImportError as e:
        print(f"❌ importerror: {e}")
        print("finviz_range_analyzer.py check")
        return 1
    except Exception as e:
        print(f"❌ unexpectederror: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 