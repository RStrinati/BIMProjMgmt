"""
Diagnostic script to investigate the backend 500 error for GET /quality/models/{id}

This script:
1. Queries the ExpectedModels table directly
2. Tests the API endpoint
3. Checks for data integrity issues
4. Identifies the root cause
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from config import Config
from database_pool import get_db_connection

def diagnose_model_error(model_id: int, project_id: int = 2):
    """Diagnose why GET /quality/models/{id} returns 500"""
    
    print(f"\n{'='*60}")
    print(f"DIAGNOSING MODEL ID: {model_id} (Project: {project_id})")
    print(f"{'='*60}\n")
    
    # Step 1: Check if model exists
    print("Step 1: Check if model exists in database...")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    expected_model_id,
                    project_id,
                    expected_model_key,
                    abv,
                    registered_model_name,
                    display_name,
                    company,
                    discipline,
                    description,
                    bim_contact,
                    notes,
                    created_at,
                    updated_at
                FROM ExpectedModels
                WHERE expected_model_id = ?
            """, (model_id,))
            
            row = cursor.fetchone()
            if not row:
                print(f"❌ Model {model_id} does NOT exist in database")
                return
            
            print(f"✅ Model found:")
            print(f"   ID: {row[0]}")
            print(f"   Project: {row[1]}")
            print(f"   Key: {row[2]}")
            print(f"   ABV: {row[3]}")
            print(f"   Registered Name: {row[4]}")
            print(f"   Display Name: {row[5]}")
            print(f"   Company: {row[6]}")
            print(f"   Discipline: {row[7]}")
            
            registered_name = row[4]
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Check aliases
    print(f"\nStep 2: Check ExpectedModelAliases...")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    expected_model_alias_id,
                    match_type,
                    alias_pattern,
                    created_at
                FROM ExpectedModelAliases
                WHERE expected_model_id = ?
            """, (model_id,))
            
            aliases = cursor.fetchall()
            if aliases:
                print(f"✅ Found {len(aliases)} aliases:")
                for alias in aliases:
                    print(f"   - ID {alias[0]}: {alias[1]} - {alias[2]}")
            else:
                print(f"⚠️ No aliases found (this is OK)")
    except Exception as e:
        print(f"❌ Alias query error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Step 3: Test ACC database query
    print(f"\nStep 3: Test ACC vw_files_expanded_pm query...")
    if registered_name:
        try:
            with get_db_connection(Config.ACC_DB) as acc_conn:
                cursor = acc_conn.cursor()
                cursor.execute("""
                    SELECT TOP 1
                        file_name,
                        folder_path,
                        last_modified_date,
                        file_size
                    FROM vw_files_expanded_pm
                    WHERE file_name LIKE ?
                    ORDER BY last_modified_date DESC
                """, (f'%{registered_name}%',))
                
                obs = cursor.fetchone()
                if obs:
                    print(f"✅ Found observed match in ACC:")
                    print(f"   File: {obs[0]}")
                    print(f"   Path: {obs[1]}")
                    print(f"   Modified: {obs[2]}")
                    print(f"   Size: {obs[3]}")
                else:
                    print(f"⚠️ No matching file in ACC (this is OK)")
        except Exception as e:
            print(f"❌ ACC query error: {str(e)}")
            print(f"   This might be the cause of the 500 error!")
            import traceback
            traceback.print_exc()
    else:
        print(f"⚠️ Skipping ACC query (no registered_model_name)")
    
    # Step 4: Check for NULL/invalid values
    print(f"\nStep 4: Check for data integrity issues...")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check for DATETIME conversion issues
            cursor.execute("""
                SELECT 
                    CASE WHEN created_at IS NULL THEN 1 ELSE 0 END as created_null,
                    CASE WHEN updated_at IS NULL THEN 1 ELSE 0 END as updated_null,
                    CASE WHEN notes_updated_at IS NULL THEN 1 ELSE 0 END as notes_updated_null,
                    CASE WHEN expected_delivery_date IS NULL THEN 1 ELSE 0 END as delivery_date_null,
                    CASE WHEN actual_delivery_date IS NULL THEN 1 ELSE 0 END as actual_date_null
                FROM ExpectedModels
                WHERE expected_model_id = ?
            """, (model_id,))
            
            nulls = cursor.fetchone()
            print(f"   Null checks:")
            print(f"   - created_at: {'NULL' if nulls[0] else 'OK'}")
            print(f"   - updated_at: {'NULL' if nulls[1] else 'OK'}")
            print(f"   - notes_updated_at: {'NULL' if nulls[2] else 'OK'}")
            print(f"   - expected_delivery_date: {'NULL' if nulls[3] else 'OK'}")
            print(f"   - actual_delivery_date: {'NULL' if nulls[4] else 'OK'}")
            
            if nulls[2] == 0:  # notes_updated_at is NOT NULL
                print(f"\n   ⚠️ notes_updated_at is NOT NULL - checking value...")
                cursor.execute("""
                    SELECT notes_updated_at
                    FROM ExpectedModels
                    WHERE expected_model_id = ?
                """, (model_id,))
                notes_updated = cursor.fetchone()[0]
                print(f"   Value: {notes_updated}")
                print(f"   Type: {type(notes_updated)}")
                
    except Exception as e:
        print(f"❌ Integrity check error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Simulate API call
    print(f"\nStep 5: Test API endpoint...")
    try:
        import requests
        response = requests.get(f"http://localhost:5000/api/projects/{project_id}/quality/models/{model_id}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 500:
            print(f"   ❌ 500 Error confirmed")
            try:
                error = response.json()
                print(f"   Error message: {error.get('error', 'Unknown')}")
            except:
                print(f"   Error body: {response.text}")
        elif response.status_code == 200:
            print(f"   ✅ API call succeeded")
            print(f"   Model: {response.json().get('registeredModelName')}")
        else:
            print(f"   Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API test error: {str(e)}")
    
    print(f"\n{'='*60}")
    print("DIAGNOSIS COMPLETE")
    print(f"{'='*60}\n")
    
    print("Possible causes of 500 error:")
    print("1. ACC database connection failure")
    print("2. Invalid datetime format in notes_updated_at or other date fields")
    print("3. Missing column in ExpectedModels table (check schema)")
    print("4. Null pointer when accessing nested fields")
    print("\nRecommendation:")
    print("Check backend logs for full traceback:")
    print("  cat backend/logs/log*.txt | grep -A 10 'quality/models'")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Diagnose model detail 500 error")
    parser.add_argument("--model-id", type=int, default=9, help="Model ID to diagnose")
    parser.add_argument("--project-id", type=int, default=2, help="Project ID")
    
    args = parser.parse_args()
    
    diagnose_model_error(args.model_id, args.project_id)
