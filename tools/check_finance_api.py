"""Quick check of finance endpoint."""
import requests
import sys

try:
    r = requests.get('http://localhost:5000/api/projects/4/finance/line-items', timeout=5)
    r.raise_for_status()
    data = r.json()
    
    print(f"Total: ${data['totals']['total_fee']:,.2f}")
    print(f"Reviews: {sum(1 for x in data['line_items'] if x['type']=='review')}")
    print(f"Items: {sum(1 for x in data['line_items'] if x['type']=='item')}\n")
    
    print("All line items:")
    for x in data['line_items']:
        print(f"{x['type']:6} id={x['id']:4} fee=${x.get('fee',0):>9,.2f} source={x.get('fee_source','?'):20}")
        
    print(f"\nSummary:")
    review_total = sum(x['fee'] for x in data['line_items'] if x['type']=='review')
    item_total = sum(x['fee'] for x in data['line_items'] if x['type']=='item')
    print(f"  Reviews total: ${review_total:,.2f}")
    print(f"  Items total: ${item_total:,.2f}")
    print(f"  Grand total: ${review_total + item_total:,.2f}")
        
except requests.RequestException as e:
    print(f"ERROR: {e}")
    sys.exit(1)
