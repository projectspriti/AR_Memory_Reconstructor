#!/usr/bin/env python3
"""Simple health check for AR Memory Reconstructor Backend"""

import requests

def main():
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ Server is healthy")
            print(f"  Database: {data.get('database')}")
            return True
        else:
            print(f"✗ Server error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Server not running")
        return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

if __name__ == "__main__":
    main()