#!/usr/bin/env python3
"""Test script to check if phase1_enhanced_ui can be imported"""

try:
    import phase1_enhanced_ui
    print("✅ phase1_enhanced_ui imported successfully")
    
    # Try to access the classes
    print("Available classes:")
    for item in dir(phase1_enhanced_ui):
        if item[0].isupper():  # Classes typically start with uppercase
            print(f"  - {item}")
            
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")
