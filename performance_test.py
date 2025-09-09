#!/usr/bin/env python3
"""
Performance testing script for BBQ application
Tests various endpoints and measures response times
"""

import requests
import time
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

BASE_URL = "http://localhost:3000"

def test_endpoint(endpoint, method="GET", data=None, headers=None):
    """Test a single endpoint and return response time and status"""
    url = f"{BASE_URL}{endpoint}"
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        return {
            'endpoint': endpoint,
            'method': method,
            'status_code': response.status_code,
            'response_time_ms': response_time,
            'success': response.status_code < 400
        }
    except requests.exceptions.RequestException as e:
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        return {
            'endpoint': endpoint,
            'method': method,
            'status_code': 0,
            'response_time_ms': response_time,
            'success': False,
            'error': str(e)
        }

def test_registration_performance(num_requests=10):
    """Test registration endpoint performance"""
    print(f"\n🧪 Testing registration endpoint with {num_requests} requests...")
    
    test_data = {
        "name": "Performance Test User",
        "houseNumber": "999",
        "email": "perf@test.com",
        "personsAdults": 2,
        "personsChildren": 1,
        "allergiesNotes": "Performance test registration"
    }
    
    results = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(test_endpoint, "/api/register", "POST", test_data)
            for _ in range(num_requests)
        ]
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if result['success']:
                print(f"✅ {result['endpoint']}: {result['response_time_ms']:.2f}ms")
            else:
                print(f"❌ {result['endpoint']}: {result['response_time_ms']:.2f}ms (Status: {result['status_code']})")
    
    return results

def test_static_files():
    """Test static file serving performance"""
    print("\n📁 Testing static file serving...")
    
    static_files = [
        "/static/style.css",
        "/static/script.js",
        "/static/bbq_achtergrond.png",
        "/static/favicon.png"
    ]
    
    results = []
    for file_path in static_files:
        result = test_endpoint(file_path)
        results.append(result)
        if result['success']:
            print(f"✅ {file_path}: {result['response_time_ms']:.2f}ms")
        else:
            print(f"❌ {file_path}: {result['response_time_ms']:.2f}ms")
    
    return results

def test_main_pages():
    """Test main page performance"""
    print("\n🏠 Testing main pages...")
    
    pages = [
        ("/", "Home page"),
        ("/success", "Success page"),
        ("/login", "Login page")
    ]
    
    results = []
    for endpoint, description in pages:
        result = test_endpoint(endpoint)
        results.append(result)
        if result['success']:
            print(f"✅ {description} ({endpoint}): {result['response_time_ms']:.2f}ms")
        else:
            print(f"❌ {description} ({endpoint}): {result['response_time_ms']:.2f}ms")
    
    return results

def analyze_results(results, test_name):
    """Analyze and display test results"""
    if not results:
        return
    
    successful_results = [r for r in results if r['success']]
    response_times = [r['response_time_ms'] for r in successful_results]
    
    if response_times:
        print(f"\n📊 {test_name} Performance Analysis:")
        print(f"   Total requests: {len(results)}")
        print(f"   Successful: {len(successful_results)}")
        print(f"   Failed: {len(results) - len(successful_results)}")
        print(f"   Average response time: {statistics.mean(response_times):.2f}ms")
        print(f"   Median response time: {statistics.median(response_times):.2f}ms")
        print(f"   Min response time: {min(response_times):.2f}ms")
        print(f"   Max response time: {max(response_times):.2f}ms")
        
        if len(response_times) > 1:
            print(f"   Standard deviation: {statistics.stdev(response_times):.2f}ms")
    else:
        print(f"\n❌ {test_name}: No successful requests")

def main():
    """Main performance test function"""
    print("🚀 BBQ Application Performance Test")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start the application first.")
        sys.exit(1)
    
    print("✅ Server is running, starting performance tests...")
    
    # Run tests
    main_results = test_main_pages()
    static_results = test_static_files()
    registration_results = test_registration_performance(5)  # Reduced for testing
    
    # Analyze results
    analyze_results(main_results, "Main Pages")
    analyze_results(static_results, "Static Files")
    analyze_results(registration_results, "Registration API")
    
    # Overall summary
    all_results = main_results + static_results + registration_results
    successful_results = [r for r in all_results if r['success']]
    response_times = [r['response_time_ms'] for r in successful_results]
    
    if response_times:
        print(f"\n🎯 Overall Performance Summary:")
        print(f"   Total requests: {len(all_results)}")
        print(f"   Success rate: {len(successful_results)/len(all_results)*100:.1f}%")
        print(f"   Average response time: {statistics.mean(response_times):.2f}ms")
        print(f"   Median response time: {statistics.median(response_times):.2f}ms")
        
        # Performance benchmarks
        avg_time = statistics.mean(response_times)
        if avg_time < 100:
            print("   🟢 Excellent performance!")
        elif avg_time < 500:
            print("   🟡 Good performance")
        elif avg_time < 1000:
            print("   🟠 Acceptable performance")
        else:
            print("   🔴 Performance needs improvement")

if __name__ == "__main__":
    main()


