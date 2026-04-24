#!/usr/bin/env python3
"""
Release Test Runner
Comprehensively run all validation tests recommended before release
"""

import sys
import os
import subprocess
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# .envfileload
load_dotenv()

# 
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# testimport
from tests.test_mcp_system_validation import MCPSystemValidationTest

class ReleaseTestRunner:
    """testrun"""
    
    def __init__(self):
        self.test_results = {}
        self.total_duration = 0
        self.skip_mcp_server_test = True  # defaultMCPservertest
    
    def print_header(self):
        """output"""
        print("=" * 100)
        print("🚀 FINVIZ MCP SERVER - RELEASE VALIDATION TESTS")
        print("=" * 100)
        print("testrun")
        print("- Environment check")
        print("- Unit testsrun") 
        print("- System validation testsrun")
        if not self.skip_mcp_server_test:
            print("- MCPserverstartup test")
        print("-" * 100)
    
    def check_environment(self):
        """Environment check"""
        print("🔍 Environment checkrunning...")
        
        checks = []
        
        # Python check
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 8):
            print(f"✅ Python : {python_version}")
            checks.append(True)
        else:
            print(f"❌ Python : {python_version} (3.8or more)")
            checks.append(False)
        
        # filecheck
        required_files = ['src/server.py', 'pyproject.toml', 'requirements.txt']
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"✅ file: {file_path}")
                checks.append(True)
            else:
                print(f"❌ file not found: {file_path}")
                checks.append(False)
        
        # check
        finviz_key = os.getenv('FINVIZ_API_KEY')
        if finviz_key:
            print(f"✅ FINVIZ_API_KEY")
            checks.append(True)
        else:
            print(f"⚠️  FINVIZ_API_KEY()")
            checks.append(True)  # warning、test
        
        # check
        try:
            import pandas, requests, bs4
            print("✅ ")
            checks.append(True)
        except ImportError as e:
            print(f"❌ : {e}")
            checks.append(False)
        
        return all(checks)
    
    def run_mcp_server_startup_test(self):
        """MCPserverstartup test()"""
        print("\n🔌 MCPserverstartup testrunning...")
        print("⚠️  : RuntimeWarningwarning")
        
        try:
            result = subprocess.run([
                sys.executable, "-c", 
                """
import sys
import subprocess
import time
import signal

# MCPserver
proc = subprocess.Popen([sys.executable, '-m', 'mcp.server.stdio', 'src.server'], 
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE)

# 3s
time.sleep(3)

# running
if proc.poll() is None:
    print('SUCCESS: MCPserver')
    proc.terminate()
    proc.wait()
    exit(0)
else:
    stdout, stderr = proc.communicate()
    if stderr:
        print(f'ERROR: {stderr.decode()}')
    exit(1)
                """
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ MCPserverstartup testsuccess")
                return True
            else:
                print(f"❌ MCPserverfailed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ MCPserverstartup testtimeout")
            return False
        except Exception as e:
            print(f"❌ MCPserverstartup testerror: {e}")
            return False
    
    def run_system_validation_tests(self):
        """System validation testsrun"""
        print("\n🧪 System validation testsrun...")
        
        start_time = time.time()
        validator = MCPSystemValidationTest()
        success = validator.run_all_tests()
        duration = time.time() - start_time
        
        self.test_results['system_validation'] = {
            'success': success,
            'duration': duration,
            'details': validator.test_results
        }
        
        return success
    
    def run_unit_tests(self):
        """Unit testsrun"""
        print("\n🔬 Unit testsrun...")
        
        # testfilelist
        unit_test_files = [
            "tests/test_basic.py",           # Unit tests
            # "tests/test_error_handling.py", # : 
        ]
        
        integration_test_files = [
            # "tests/test_mcp_integration.py", # : 
        ]
        
        all_tests_passed = True
        test_summary = {"passed": 0, "failed": 0, "total": 0}
        
        # Unit testsrun
        print("  📋 Unit tests:")
        for test_file in unit_test_files:
            if os.path.exists(test_file):
                try:
                    result = subprocess.run([
                        sys.executable, test_file
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        print(f"    ✅ {test_file}")
                        test_summary["passed"] += 1
                    else:
                        print(f"    ❌ {test_file}")
                        print(f"       error: {result.stderr[:200]}...")
                        test_summary["failed"] += 1
                        all_tests_passed = False
                    test_summary["total"] += 1
                    
                except subprocess.TimeoutExpired:
                    print(f"    ⏰ {test_file} (timeout)")
                    test_summary["failed"] += 1
                    test_summary["total"] += 1
                    all_tests_passed = False
                except Exception as e:
                    print(f"    ❌ {test_file} (runerror: {e})")
                    test_summary["failed"] += 1
                    test_summary["total"] += 1
                    all_tests_passed = False
            else:
                print(f"    ⚠️  {test_file} (file not found)")
        
        # testrun(pytest)
        print("  🔗 test:")
        if integration_test_files:
            for test_file in integration_test_files:
                if os.path.exists(test_file):
                    try:
                        result = subprocess.run([
                            sys.executable, "-m", "pytest", test_file,
                            "-v", "--tb=short", "--timeout=60"
                        ], capture_output=True, text=True, timeout=90)
                        
                        if result.returncode == 0:
                            print(f"    ✅ {test_file}")
                            test_summary["passed"] += 1
                        else:
                            print(f"    ❌ {test_file}")
                            # detailserroroutput
                            error_lines = result.stdout.split('\n')[-10:]  # 10
                            for line in error_lines:
                                if line.strip():
                                    print(f"       {line}")
                            test_summary["failed"] += 1
                            all_tests_passed = False
                        test_summary["total"] += 1
                        
                    except subprocess.TimeoutExpired:
                        print(f"    ⏰ {test_file} (timeout)")
                        test_summary["failed"] += 1
                        test_summary["total"] += 1
                        all_tests_passed = False
                    except Exception as e:
                        print(f"    ❌ {test_file} (runerror: {e})")
                        test_summary["failed"] += 1
                        test_summary["total"] += 1
                        all_tests_passed = False
                else:
                    print(f"    ⚠️  {test_file} (file not found)")
        else:
            print("    ℹ️  test: ()")
        
        # summaryoutput
        print(f"  📊 Unit testsresults: {test_summary['passed']}/{test_summary['total']} success")
        
        if all_tests_passed:
            print("✅ Unit testssuccess")
        else:
            print("❌ Unit testsfailed")
        
        return all_tests_passed
    
    def generate_release_report(self):
        """"""
        print("\n" + "=" * 100)
        print("📊 RELEASE VALIDATION REPORT")
        print("=" * 100)
        
        # summary
        all_tests_passed = all(
            result.get('success', False) 
            for result in self.test_results.values()
        )
        
        total_tests = sum(
            len(result.get('details', [])) 
            for result in self.test_results.values()
        )
        
        total_passed = sum(
            sum(1 for detail in result.get('details', []) if detail.success)
            for result in self.test_results.values()
        )
        
        print(f"📈 results:")
        print(f"   overall status: {'🟢 PASS' if all_tests_passed else '🔴 FAIL'}")
        print(f"   testsuccess: {total_passed}/{total_tests} ({(total_passed/total_tests*100):.1f}%)" if total_tests > 0 else "   testsuccess: N/A")
        print(f"   runtime: {self.total_duration:.2f}s")
        
        # by categoryresults
        print(f"\n📋 by categoryresults:")
        for category, result in self.test_results.items():
            status = "✅" if result['success'] else "❌"
            duration = result['duration']
            print(f"   {status} {category}: {duration:.2f}s")
        
        # quality metrics(System validation tests)
        if 'system_validation' in self.test_results:
            system_details = self.test_results['system_validation']['details']
            if system_details:
                total_stocks = sum(detail.stocks_found for detail in system_details)
                avg_quality = sum(detail.data_quality_score for detail in system_details) / len(system_details)
                print(f"\n📊 quality metrics:")
                print(f"   total stocks detected: {total_stocks}")
                print(f"   average quality score: {avg_quality:.1f}/100")
        
        # release decision
        print(f"\n🎯 release decision:")
        if all_tests_passed:
            print("   🟢 release approved - testsuccess")
            print("   production-ready")
        else:
            failed_categories = [cat for cat, result in self.test_results.items() if not result['success']]
            print("   🔴 release on hold - fix required")
            print(f"   failedcategory: {', '.join(failed_categories)}")
            print("   failedfix and rerun tests")
        
        print("=" * 100)
        
        return all_tests_passed
    
    def run_all_release_tests(self, include_mcp_server_test=False):
        """testrun"""
        self.skip_mcp_server_test = not include_mcp_server_test
        start_time = time.time()
        
        self.print_header()
        
        # 1. Environment check
        if not self.check_environment():
            print("❌ Environment checkfailed - testabort")
            return False
        
        # 2. Unit tests(run)
        unit_test_start = time.time()
        unit_success = self.run_unit_tests()
        unit_duration = time.time() - unit_test_start
        self.test_results['unit_tests'] = {
            'success': unit_success,
            'duration': unit_duration,
            'details': []
        }
        
        # 3. System validation tests(maintest)
        system_success = self.run_system_validation_tests()
        
        # 4. MCPserverstartup test()
        if include_mcp_server_test:
            server_test_start = time.time()
            server_success = self.run_mcp_server_startup_test()
            server_duration = time.time() - server_test_start
            self.test_results['mcp_server_startup'] = {
                'success': server_success,
                'duration': server_duration,
                'details': []
            }
        
        # runtime
        self.total_duration = time.time() - start_time
        
        # 5. 
        overall_success = self.generate_release_report()
        
        return overall_success

# mainrun
def main():
    """mainrunfunction"""
    # MCPservertest
    include_mcp_test = "--include-mcp-test" in sys.argv
    
    if include_mcp_test:
        print("🔌 MCPserverstartup testrun")
    else:
        print("⚠️  MCPserverstartup test(--include-mcp-test )")
    
    runner = ReleaseTestRunner()
    success = runner.run_all_release_tests(include_mcp_server_test=include_mcp_test)
    
    if success:
        print("\n🎉 testcompleted - success!")
        print("。")
        return True
    else:
        print("\n⚠️  testcompleted - fix required")
        print("failed、test。")
        return False

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  testinterrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n❌ unexpectederror: {e}")
        sys.exit(3) 