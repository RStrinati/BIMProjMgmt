from database import insert_project_full

# Test data similar to what the frontend sends
test_data = {
    'project_name': 'Test Project from Script',
    'client_id': 1,
    'type_id': 1,
    'folder_path': 'C:/test/path',
    'start_date': '2024-01-01',
    'end_date': '2024-12-31',
    'status': 'Planning',
    'priority': 'Medium'
}

print("Testing insert_project_full with data:")
for k, v in test_data.items():
    print(f"  {k}: {v} ({type(v)})")

try:
    result = insert_project_full(test_data)
    print(f"Result: {result}")
    if result:
        print("✅ Project inserted successfully")
    else:
        print("❌ Project insertion failed")
except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()