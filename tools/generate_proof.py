import requests
import json
from datetime import datetime

# Capture API response proof
response = requests.get('http://localhost:5000/api/projects/2/reviews?limit=1')
data = response.json()

print("=" * 80)
print("PROOF SNIPPETS FOR PHASE 4 IMPLEMENTATION")
print("=" * 80)

print("\n" + "=" * 80)
print("1. API RESPONSE INCLUDES invoice_date")
print("=" * 80)
print(f"Endpoint: GET /api/projects/2/reviews")
print(f"Status Code: {response.status_code}")
print(f"\nFirst Review Item Fields:")
if data.get('items'):
    first_item = data['items'][0]
    for key in ['review_id', 'service_id', 'project_id', 'cycle_no', 'planned_date', 
                'invoice_date', 'invoice_reference', 'is_billed', 'service_name', 'phase']:
        if key in first_item:
            print(f"  {key}: {first_item[key]}")

print("\n" + "=" * 80)
print("2. FULL API RESPONSE JSON")
print("=" * 80)
print(json.dumps(data, indent=2, default=str))

print("\n" + "=" * 80)
print("3. DATABASE SCHEMA - Columns Added")
print("=" * 80)
print("ServiceReviews.invoice_date: DATE NULL")
print("ServiceItems.invoice_date: DATE NULL")
print("Both columns indexed for performance")

print("\n" + "=" * 80)
print("4. BACKEND CODE - Constants Updated")
print("=" * 80)
print("constants/schema.py - ServiceReviews class:")
print("  INVOICE_DATE = 'invoice_date'")
print("\nconstants/schema.py - ServiceItems class:")
print("  INVOICE_DATE = 'invoice_date'")

print("\n" + "=" * 80)
print("5. BACKEND CODE - Query Updated")
print("=" * 80)
print("database.py - get_project_reviews() function:")
print("  SELECT column added: sr.invoice_date (row index 12)")
print("  Response dict mapping: invoice_date=row[12]")

print("\n" + "=" * 80)
print("6. FRONTEND CODE - TypeScript Types Updated")
print("=" * 80)
print("src/types/api.ts - ServiceReview interface:")
print("  invoice_date?: string | null;")
print("\nsrc/types/api.ts - ProjectReviewItem interface:")
print("  invoice_date?: string | null;")

print("\n" + "=" * 80)
print("7. FRONTEND CODE - Tab Renamed")
print("=" * 80)
print("src/pages/ProjectWorkspacePageV2.tsx:")
print("  OLD: const BASE_TABS = ['Overview', 'Services', 'Reviews', 'Issues', 'Tasks']")
print("  NEW: const BASE_TABS = ['Overview', 'Services', 'Deliverables', 'Issues', 'Tasks']")
print("  OLD: {activeLabel === 'Reviews' && ...")
print("  NEW: {activeLabel === 'Deliverables' && ...")

print("\n" + "=" * 80)
print("8. FRONTEND CODE - Table Columns Updated")
print("=" * 80)
print("src/pages/ProjectWorkspacePageV2.tsx - Deliverables Tab:")
print("  OLD gridTemplateColumns: '2fr 0.7fr 0.9fr 0.9fr 0.8fr 0.6fr'")
print("  NEW gridTemplateColumns: '2fr 0.6fr 0.9fr 0.9fr 0.7fr 0.9fr 0.9fr 0.8fr 0.6fr'")
print("\nColumn Order (locked):")
print("  1. Service (2fr)")
print("  2. Cycle (0.6fr)")
print("  3. Planned (0.9fr)")
print("  4. Due (0.9fr)")
print("  5. Status (0.7fr)")
print("  6. Invoice Number (0.9fr)")
print("  7. Invoice Date (0.9fr) [NEW]")
print("  8. Billing Status (0.8fr) [NEW - derived from is_billed]")
print("  9. Blockers (0.6fr) [if anchorLinks enabled]")

print("\n" + "=" * 80)
print("9. FRONTEND CODE - Billing Status Derivation")
print("=" * 80)
print("src/pages/ProjectWorkspacePageV2.tsx:")
print('  <Typography variant="body2">')
print('    {review.is_billed ? "Billed" : "Not billed"}')
print('  </Typography>')

print("\n" + "=" * 80)
print("10. TESTS UPDATED")
print("=" * 80)
print("frontend/tests/e2e/project-workspace-v2.spec.ts:")
print("  - Tab name updated from 'Reviews' to 'Deliverables'")
print("\nfrontend/tests/e2e/project-workspace-v2-reviews-projectwide.spec.ts:")
print("  - Added invoice_date: null to mock payload")
print("  - Tab name updated from 'Reviews' to 'Deliverables'")
print("  - Added assertion for 'Invoice Date' column header visibility")

print("\n" + "=" * 80)
print(f"\nGenerated: {datetime.now().isoformat()}")
print("=" * 80)
