import sys
import os
from collections import defaultdict, Counter

# Python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def analyze_volume_surge_stocks():
    """volumesurgestocksdetails"""
    try:
        from src.finviz_client.screener import FinvizScreener
        screener = FinvizScreener()
        
        print("=== volumesurgestocksdetails ===")
        
        # screeningrun
        results = screener.volume_surge_screener()
        print(f"stocks: {len(results)}")
        
        # sector
        sector_analysis = defaultdict(list)
        industry_analysis = defaultdict(list)
        
        # pricechange
        price_change_ranges = {
            "10%or more": [],
            "5-10%": [],
            "2-5%": []
        }
        
        # market cap
        market_cap_ranges = {
            "large (50B+)": [],
            "mid (2B-50B)": [],
            "small (300M-2B)": []
        }
        
        # topstocksdetails
        top_performers = []
        
        for i, stock in enumerate(results[:20]):  # top20stocksdetails
            # sectorinformation
            sector = getattr(stock, 'sector', 'Unknown')
            industry = getattr(stock, 'industry', 'Unknown')
            
            # basic information
            ticker = stock.ticker
            price = getattr(stock, 'price', 0)
            price_change = getattr(stock, 'price_change', 0)
            volume = getattr(stock, 'volume', 0)
            market_cap = getattr(stock, 'market_cap', 0)
            
            # 
            sector_analysis[sector].append({
                'ticker': ticker,
                'price_change': price_change,
                'volume': volume
            })
            
            industry_analysis[industry].append(ticker)
            
            # pricechange
            if price_change >= 10:
                price_change_ranges["10%or more"].append(ticker)
            elif price_change >= 5:
                price_change_ranges["5-10%"].append(ticker)
            else:
                price_change_ranges["2-5%"].append(ticker)
            
            # market cap()
            if market_cap and market_cap > 50000:  # 50B+
                market_cap_ranges["large (50B+)"].append(ticker)
            elif market_cap and market_cap > 2000:  # 2B-50B
                market_cap_ranges["mid (2B-50B)"].append(ticker)
            else:
                market_cap_ranges["small (300M-2B)"].append(ticker)
            
            # top
            if i < 10:
                top_performers.append({
                    'rank': i + 1,
                    'ticker': ticker,
                    'price': price,
                    'price_change': price_change,
                    'volume': volume,
                    'sector': sector
                })
        
        # resultsoutput
        print("\n=== TOP 10  ===")
        for performer in top_performers:
            print(f"{performer['rank']:2d}. {performer['ticker']:6s} | "
                  f"{performer['price_change']:+6.2f}% | "
                  f"${performer['price']:7.2f} | "
                  f"{performer['volume']/1000000:6.1f}M vol | "
                  f"{performer['sector']}")
        
        print("\n=== sector ===")
        sector_summary = {}
        for sector, stocks in sector_analysis.items():
            count = len(stocks)
            avg_change = sum(s['price_change'] for s in stocks) / count if count > 0 else 0
            sector_summary[sector] = {'count': count, 'avg_change': avg_change}
            print(f"{sector:25s}: {count:3d}stocks (averagechange: {avg_change:+5.2f}%)")
        
        print("\n=== pricechange ===")
        for range_name, tickers in price_change_ranges.items():
            print(f"{range_name:10s}: {len(tickers):3d}stocks ({len(tickers)/len(results)*100:4.1f}%)")
            if tickers:
                print(f"  stocks: {', '.join(tickers[:5])}")
        
        print("\n=== market cap ===")
        for cap_range, tickers in market_cap_ranges.items():
            print(f"{cap_range:15s}: {len(tickers):3d}stocks")
        
        # results
        return {
            'total_stocks': len(results),
            'top_performers': top_performers,
            'sector_summary': sector_summary,
            'price_change_distribution': {k: len(v) for k, v in price_change_ranges.items()},
            'market_cap_distribution': {k: len(v) for k, v in market_cap_ranges.items()},
            'top_sectors': sorted(sector_summary.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        }
        
    except Exception as e:
        print(f"error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    analyze_volume_surge_stocks() 