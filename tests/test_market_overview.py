#!/usr/bin/env python3
"""
Market Overviewtest
"""
import os
import sys

# 
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_import():
    """importtest"""
    try:
        from utils.validators import validate_ticker
        from utils.finviz_client import FinvizClient
        from utils.screeners import FinvizScreener
        print("✅ importsuccess")
        return True
    except Exception as e:
        print(f"❌ importerror: {str(e)}")
        return False

def test_market_overview_syntax():
    """syntax check"""
    try:
        # server.pysyntax check
        import ast
        with open('src/server.py', 'r', encoding='utf-8') as f:
            source = f.read()
        
        ast.parse(source)
        print("✅ server.py syntax checksuccess")
        return True
    except SyntaxError as e:
        print(f"❌ error: {str(e)}")
        print(f"    {e.lineno}: {e.text}")
        return False

def test_finviz_tools():
    """Finviztooltest"""
    try:
        # test
        from utils.validators import validate_ticker
        
        # 
        assert validate_ticker("SPY") == True
        assert validate_ticker("QQQ") == True
        assert validate_ticker("AAPL") == True
        
        # 
        assert validate_ticker("") == False
        assert validate_ticker("12345") == False
        
        print("✅ testsuccess")
        return True
    except Exception as e:
        print(f"❌ testerror: {str(e)}")
        return False

def main():
    print("🚀 Market Overview implementationteststart")
    print("=" * 50)
    
    # testrun
    tests = [
        ("importtest", test_import),
        ("syntax check", test_market_overview_syntax),
        ("Finviztooltest", test_finviz_tools)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📊 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"🎯 testresults: {passed}/{total} passed")
    
    if passed == total:
        print("✅ testsuccess")
        print("🚀 market_overviewimplementationcompleted")
    else:
        print("❌ testfailed")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 