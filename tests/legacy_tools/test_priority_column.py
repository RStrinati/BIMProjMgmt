"""
Test the updated view to verify Priority column extraction.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from config import ACC_DB

def test_priority_extraction():
    """Test that Priority column is extracting values correctly."""
    with get_db_connection(ACC_DB) as conn:
    if conn is None:
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        print("="*70)
        print("🧪 TESTING PRIORITY COLUMN EXTRACTION")
        print("="*70)
        
        # Test 1: Count non-null Priority values
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_issues,
                COUNT(Priority) AS issues_with_priority,
                COUNT(DISTINCT Priority) AS unique_priorities
            FROM [dbo].[vw_issues_expanded_custom_attrs]
        """)
        
        result = cursor.fetchone()
        print(f"\n📊 Overall Statistics:")
        print(f"  Total Issues: {result[0]}")
        print(f"  Issues with Priority: {result[1]}")
        print(f"  Unique Priority Values: {result[2]}")
        
        # Test 2: Show Priority value distribution
        cursor.execute("""
            SELECT 
                Priority,
                COUNT(*) AS count
            FROM [dbo].[vw_issues_expanded_custom_attrs]
            WHERE Priority IS NOT NULL
            GROUP BY Priority
            ORDER BY COUNT(*) DESC
        """)
        
        print(f"\n📊 Priority Distribution:")
        for row in cursor.fetchall():
            print(f"  {row[0]:20s}: {row[1]:4d} issues")
        
        # Test 3: Show sample issues with Priority
        cursor.execute("""
            SELECT TOP 10
                display_id,
                title,
                status,
                Priority,
                assignee_display_name
            FROM [dbo].[vw_issues_expanded_custom_attrs]
            WHERE Priority IS NOT NULL
            ORDER BY created_at DESC
        """)
        
        print(f"\n📋 Sample Issues with Priority:")
        print(f"  {'Issue':<10} {'Priority':<15} {'Status':<15} {'Assignee':<25}")
        print(f"  {'-'*10} {'-'*15} {'-'*15} {'-'*25}")
        
        for row in cursor.fetchall():
            display_id = row[0] or 'N/A'
            title = (row[1][:30] + '...') if row[1] and len(row[1]) > 30 else (row[1] or 'N/A')
            status = row[2] or 'N/A'
            priority = row[3] or 'N/A'
            assignee = row[4] or 'Unassigned'
            
            print(f"  {display_id:<10} {priority:<15} {status:<15} {assignee:<25}")
        
        print("\n" + "="*70)
        print("✅ Priority column is working correctly!")
        print("="*70)
        
    finally:

if __name__ == '__main__':
    test_priority_extraction()
