#!/usr/bin/env python3
"""Test fee resolution directly."""

import sys
sys.path.insert(0, '.')

from services.financial_data_service import FinancialDataService

try:
    result = FinancialDataService.get_line_items(4)
    print("Result:", result)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
