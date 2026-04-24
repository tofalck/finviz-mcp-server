#!/usr/bin/env python3
"""
Finviz Elite quick analysis script

Finviz Elitefilteranalysisrun
"""

import sys
import os
from pathlib import Path

# 
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from finviz_elite_analyzer import FinvizEliteAnalyzer
except ImportError as e:
    print(f"❌ importerror: {e}")
    print(":")
    print("pip install -r requirements.txt")
    sys.exit(1)

def quick_analyze():
    """quickanalysisrun"""
    print("🔍 Finviz Elite filter quickanalysis")
    print("=" * 50)
    
    # logininformationfetch
    import getpass
    
    username = input("📧 Elite username: ").strip()
    if not username:
        print("❌ username")
        return False
    
    password = getpass.getpass("🔐 Elite password: ")
    if not password:
        print("❌ password")
        return False
    
    # analysisrun
    print("\n🚀 analysisstart...")
    print("📝 login...")
    
    analyzer = FinvizEliteAnalyzer()
    
    try:
        success = analyzer.run_full_analysis(
            username=username,
            password=password,
            export_format='both'
        )
        
        if success:
            print("\n✅ analysiscompleted")
            print("\n📄 file:")
            
            # filecheck
            md_file = "finviz_elite_filters.md"
            json_file = "finviz_elite_filters.json"
            
            if os.path.exists(md_file):
                file_size = os.path.getsize(md_file) / 1024  # KB
                print(f"  📋 {md_file} ({file_size:.1f} KB)")
            
            if os.path.exists(json_file):
                file_size = os.path.getsize(json_file) / 1024  # KB
                print(f"  📊 {json_file} ({file_size:.1f} KB)")
            
            print("\n🎉 analysiscompleted")
            return True
        else:
            print("\n❌ analysisfailed")
            print("💡 or lesscheck:")
            print("  - logininformation")
            print("  - Elite")
            print("  - ")
            return False
            
    except KeyboardInterrupt:
        print("\n⏹️  interrupted")
        return False
    except Exception as e:
        print(f"\n❌ unexpectederror: {e}")
        return False

def main():
    """mainrun"""
    try:
        success = quick_analyze()
        
        if success:
            # resultsfilestatistics
            try:
                import json
                
                with open('finviz_elite_filters.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"\n📈 statistics:")
                print(f"  🔢 detectfilter: {len(data)}")
                
                # categorystatistics
                categories = {}
                for item in data:
                    category = "other"  # default
                    # category
                    name = item.get('name', '')
                    if 'Exchange' in name or 'Index' in name or 'Sector' in name:
                        category = "basic information"
                    elif 'Price' in name or 'Cap' in name:
                        category = "stock pricemarket cap"
                    elif 'Volume' in name:
                        category = "volume"
                    elif 'Performance' in name:
                        category = "technical analysis"
                    
                    categories[category] = categories.get(category, 0) + 1
                
                for cat, count in categories.items():
                    if count > 0:
                        print(f"  📊 {cat}: {count} items")
                        
            except Exception as e:
                print(f"  📊 statisticsfetcherror: {e}")
        
        print("\n👋 analysiscompleted")
        
    except KeyboardInterrupt:
        print("\n👋 analysisinterrupted")
    except Exception as e:
        print(f"❌ runerror: {e}")

if __name__ == "__main__":
    main() 