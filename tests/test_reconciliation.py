#!/usr/bin/env python3
"""Test reconciliation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.financial_data_service import FinancialDataService

try:
    result = FinancialDataService.get_reconciliation(4)
    print("Reconciliation Result:")
    print("Project:", result.get('project'))
    print("Services:", len(result.get('by_service', [])))
    for svc in result.get('by_service', []):
        print(f"  {svc['service_code']}: agreed={svc['agreed_fee']}, line_items={svc['line_items_total_fee']}, variance={svc['variance']}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
