import sys
import os

# Python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_volume_surge_screener():
    """volume_surge_screenertestrun"""
    try:
        # detailscheck
        from src.finviz_client.screener import FinvizScreener
        screener = FinvizScreener()
        
        # filter itemscheck
        print("\n=== filter itemscheck ===")
        filters = screener._build_volume_surge_filters()
        print(f"filter: {filters}")
        
        # Finvizparameterconvertcheck
        print("\n=== Finvizparameterconvertcheck ===")
        finviz_params = screener._convert_filters_to_finviz(filters)
        print(f"Finvizparameter: {finviz_params}")
        
        # screeningrun
        print("\n=== screeningrun ===")
        results = screener.volume_surge_screener()
        print(f"results items: {len(results)}")
        
        # resultsdetails(first5 items)
        if results:
            print("\n=== resultsdetails(first5 items) ===")
            for i, stock in enumerate(results[:5]):
                # StockDataobjectattribute
                company_name = getattr(stock, 'company_name', 'N/A')
                price = getattr(stock, 'price', 'N/A')
                price_change = getattr(stock, 'price_change', 'N/A')
                volume = getattr(stock, 'volume', 'N/A')
                
                print(f"{i+1}. {stock.ticker} - {company_name}")
                print(f"   price: ${price} | change: {price_change}% | volume: {volume}")
                print()
        else:
            print("results0 items。")
            
    except Exception as e:
        print(f"error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_volume_surge_screener() 