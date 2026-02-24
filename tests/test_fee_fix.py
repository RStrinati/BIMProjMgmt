#!/usr/bin/env python3
"""Test fee resolution directly."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.financial_data_service import FinancialDataService

try:
    result = FinancialDataService.get_line_items(4)
    print("Result:", result)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
