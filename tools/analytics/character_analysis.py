#!/usr/bin/env python3
"""
Simple character analysis script
"""

# Template name from JSON
json_name = "AWS – MEL081 STOCKMAN (Day 1)"
# What we'd get after splitting
split_name = json_name.split(" (")[0]

print("JSON template name:", repr(json_name))
print("After split:", repr(split_name))
print("Length:", len(split_name))

print("\nCharacter analysis:")
for i, char in enumerate(split_name):
    print(f"  {i:2d}: '{char}' (ord: {ord(char)})")

# The dash character analysis
dash_in_name = split_name[4]  # Should be the dash
print(f"\nDash character: '{dash_in_name}' (ord: {ord(dash_in_name)})")
print(f"Is it regular hyphen '-' (ord 45): {ord(dash_in_name) == 45}")
print(f"Is it en-dash '–' (ord 8211): {ord(dash_in_name) == 8211}")
print(f"Is it em-dash '—' (ord 8212): {ord(dash_in_name) == 8212}")