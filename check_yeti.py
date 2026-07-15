#!/usr/bin/env python3
"""
Check Goal Zero Yeti 1000X Open Box availability and log to JSON.
Runs via GitHub Actions on schedule.
"""

import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup

URL = "https://goalzero.com/products/yeti-1000x-open-box"
RESULTS_FILE = "yeti_check_history.json"

def check_availability():
    """Fetch the product page and check if it's in stock."""
    try:
        # Set a user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        html = response.text
        
        # Check for out-of-stock indicators
        out_of_stock_phrases = [
            'out of stock',
            'sold out',
            'currently unavailable',
            'this product is no longer available'
        ]
        
        html_lower = html.lower()
        is_out_of_stock = any(phrase in html_lower for phrase in out_of_stock_phrases)
        
        # Also check for "Add to cart" button (positive indicator)
        has_add_to_cart = 'add to cart' in html_lower or 'add to' in html_lower
        
        # If no out-of-stock message AND has add-to-cart, likely in stock
        in_stock = (not is_out_of_stock) and has_add_to_cart
        
        return in_stock, None
        
    except requests.RequestException as e:
        return None, str(e)

def load_history():
    """Load previous check results."""
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_history(history):
    """Save check results to JSON file."""
    with open(RESULTS_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def main():
    print("🔍 Checking Yeti 1000X Open Box availability...")
    
    in_stock, error = check_availability()
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    result = {
        "timestamp": timestamp,
        "available": in_stock,
        "error": error
    }
    
    # Load history and add new result
    history = load_history()
    history.insert(0, result)  # Put newest first
    
    # Keep last 100 checks
    history = history[:100]
    
    # Save updated history
    save_history(history)
    
    # Save result as JSON for GitHub Actions to parse
    with open("yeti_check_result.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    # Print summary
    if in_stock:
        print(f"✅ IN STOCK as of {timestamp}")
        print(f"   URL: {URL}")
    elif in_stock is False:
        print(f"❌ OUT OF STOCK as of {timestamp}")
    else:
        print(f"⚠️  ERROR checking availability: {error}")
    
    print(f"\n📊 History: {len(history)} checks stored")
    
    # Count in-stock occurrences
    in_stock_count = sum(1 for h in history if h.get('available') is True)
    print(f"   In stock: {in_stock_count}")
    
    # Set GitHub Actions output variable
    if in_stock is True:
        print("in_stock=true", end='')
        with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
            f.write("in_stock=true\n")
        exit(0)
    else:
        with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
            f.write("in_stock=false\n")
        exit(0)

if __name__ == "__main__":
    main()
