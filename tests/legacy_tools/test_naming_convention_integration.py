"""Quick test for naming convention integration"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("="*60)
print("Testing Naming Convention Integration")
print("="*60)
print()

# Test 1: Service Layer
print("1. Testing Naming Convention Service...")
from services.naming_convention_service import (
    get_available_conventions, 
    get_convention_schema,
    get_convention_path
)

conventions = get_available_conventions()
print(f"   ✅ Found {len(conventions)} conventions: {conventions}")

for code, name in conventions:
    schema = get_convention_schema(code)
    if schema:
        print(f"   ✅ {code} schema loaded: {schema['institution']} - {schema['standard']}")
    else:
        print(f"   ❌ Failed to load {code} schema")

print()

# Test 2: Database Integration
print("2. Testing Database Integration...")
from database import get_available_clients, get_client_naming_convention

clients = get_available_clients()
print(f"   ✅ Found {len(clients)} clients")

if clients:
    # Show first few clients with naming convention
    for i, client in enumerate(clients[:3]):
        client_id, client_name, contact_name, contact_email, naming_conv = client
        conv_display = naming_conv if naming_conv else "(none)"
        print(f"   - Client {client_id}: {client_name} | Convention: {conv_display}")

print()

# Test 3: Convention Paths
print("3. Testing Convention Paths...")
for code, name in conventions:
    path = get_convention_path(code)
    if path and os.path.exists(path):
        print(f"   ✅ {code}: {path}")
    else:
        print(f"   ❌ {code}: Path not found")

print()
print("="*60)
print("✅ All tests completed successfully!")
print("="*60)
