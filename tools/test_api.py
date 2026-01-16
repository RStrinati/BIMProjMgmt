import requests
import json

try:
    # Call the reviews endpoint with project 2
    r = requests.get('http://localhost:5000/api/projects/2/reviews?limit=2')
    print('Status:', r.status_code)
    if r.status_code == 200:
        data = r.json()
        print('\n===== API Response (first 2 reviews) =====')
        if data.get('items'):
            print('\nFirst Review:')
            first_item = data['items'][0]
            for key, value in first_item.items():
                print(f'  {key}: {value}')
            print('\n===== Checking for invoice_date field =====')
            if 'invoice_date' in first_item:
                print(f'✓ invoice_date field FOUND: {first_item.get("invoice_date")}')
            else:
                print('✗ invoice_date field NOT FOUND')
        else:
            print('No items in response')
    else:
        print('Response:', r.text[:500])
except Exception as e:
    print('Error:', str(e))
    import traceback
    traceback.print_exc()
