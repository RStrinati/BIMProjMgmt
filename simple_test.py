#!/usr/bin/env python3
"""Simple test script"""

from database import connect_to_db, get_review_cycles

print("Testing simple review cycles...")

try:
    cycles = get_review_cycles(2)
    print(f"Found {len(cycles)} cycles for project 2")
    for cycle in cycles:
        print(f"  {cycle}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
