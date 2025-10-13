"""
Check and setup Issue Analytics system
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection, get_db_connection

def check_tables():
    """Check if Issue Analytics tables exist."""
    print("\n" + "=" * 70)
    print("Checking Issue Analytics Tables")
    print("=" * 70)
    
    try:
        with get_db_connection('ProjectManagement') as conn:
            cursor = conn.cursor()
            
            # Check for tables
            tables_to_check = [
                'IssueCategories',
                'IssueCategoryKeywords',
                'ProcessedIssues',
                'IssuePainPoints',
                'IssueComments',
                'IssueProcessingLog'
            ]
            
            found_tables = []
            missing_tables = []
            
            for table in tables_to_check:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = '{table}'
                """)
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    found_tables.append((table, count))
                    print(f"✓ {table}: {count} rows")
                else:
                    missing_tables.append(table)
                    print(f"❌ {table}: NOT FOUND")
            
            print()
            
            if missing_tables:
                print(f"Missing {len(missing_tables)} tables. Need to run SQL scripts.")
                return False
            else:
                print(f"✓ All {len(found_tables)} tables exist")
                return True
    
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

def seed_categories():
    """Run the seed categories script."""
    print("\n" + "=" * 70)
    print("Seeding Categories")
    print("=" * 70)
    
    try:
        with get_db_connection('ProjectManagement') as conn:
            cursor = conn.cursor()
            
            # Read and execute seed script
            with open('sql/seed_issue_categories.sql', 'r', encoding='utf-8') as f:
                script = f.read()
            
            # Split by GO and execute batches
            batches = [b.strip() for b in script.split('GO') if b.strip() and not b.strip().startswith('--')]
            
            for batch in batches:
                if batch and 'SELECT' in batch.upper() or 'INSERT' in batch.upper() or 'DECLARE' in batch.upper():
                    try:
                        cursor.execute(batch)
                    except Exception as e:
                        if 'duplicate' not in str(e).lower() and 'already exists' not in str(e).lower():
                            print(f"⚠️  Warning: {e}")
            
            conn.commit()
            
            # Check category count
            cursor.execute("SELECT COUNT(*) FROM IssueCategories")
            count = cursor.fetchone()[0]
            print(f"✓ Categories seeded: {count} categories")
            
            return True
    
    except Exception as e:
        print(f"❌ Error seeding categories: {e}")
        return False

def seed_keywords():
    """Run the seed keywords script."""
    print("\n" + "=" * 70)
    print("Seeding Keywords")
    print("=" * 70)
    
    try:
        with get_db_connection('ProjectManagement') as conn:
            cursor = conn.cursor()
            
            # Read and execute seed script
            with open('sql/seed_category_keywords.sql', 'r', encoding='utf-8') as f:
                script = f.read()
            
            # Split by GO and execute batches
            batches = [b.strip() for b in script.split('GO') if b.strip() and not b.strip().startswith('--')]
            
            for batch in batches:
                if batch and 'SELECT' in batch.upper() or 'INSERT' in batch.upper() or 'DECLARE' in batch.upper():
                    try:
                        cursor.execute(batch)
                    except Exception as e:
                        if 'duplicate' not in str(e).lower() and 'violation' not in str(e).lower():
                            print(f"⚠️  Warning: {e}")
            
            conn.commit()
            
            # Check keyword count
            cursor.execute("SELECT COUNT(*) FROM IssueCategoryKeywords")
            count = cursor.fetchone()[0]
            print(f"✓ Keywords seeded: {count} keywords")
            
            return True
    
    except Exception as e:
        print(f"❌ Error seeding keywords: {e}")
        return False

def verify_system():
    """Verify the complete system."""
    print("\n" + "=" * 70)
    print("System Verification")
    print("=" * 70)
    
    try:
        with get_db_connection('ProjectManagement') as conn:
            cursor = conn.cursor()
            
            # Check categories by level
            cursor.execute("""
                SELECT 
                    category_level,
                    COUNT(*) as count
                FROM IssueCategories
                WHERE is_active = 1
                GROUP BY category_level
                ORDER BY category_level
            """)
            
            print("\nCategories by Level:")
            for row in cursor.fetchall():
                level_name = {1: 'Disciplines', 2: 'Issue Types', 3: 'Sub-Types'}.get(row[0], 'Unknown')
                print(f"  Level {row[0]} ({level_name}): {row[1]} categories")
            
            # Check keywords per discipline
            cursor.execute("""
                SELECT TOP 5
                    ic.category_name,
                    COUNT(ick.keyword_id) as keyword_count
                FROM IssueCategories ic
                LEFT JOIN IssueCategoryKeywords ick ON ic.category_id = ick.category_id
                WHERE ic.category_level = 1 AND ic.is_active = 1
                GROUP BY ic.category_name
                ORDER BY keyword_count DESC
            """)
            
            print("\nTop 5 Disciplines by Keyword Count:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} keywords")
            
            # Check views
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.VIEWS 
                WHERE TABLE_NAME LIKE 'vw_Issue%'
                ORDER BY TABLE_NAME
            """)
            
            views = [row[0] for row in cursor.fetchall()]
            print(f"\n✓ Analytics Views: {len(views)} views created")
            for view in views:
                print(f"  - {view}")
            
            print("\n✓ System verification complete")
            return True
    
    except Exception as e:
        print(f"❌ Error verifying system: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("ISSUE ANALYTICS SYSTEM - SETUP & VERIFICATION")
    print("=" * 70)
    
    # Step 1: Check tables
    tables_exist = check_tables()
    
    # Step 2: Seed if needed
    if tables_exist:
        # Check if we need to seed
        try:
            with get_db_connection('ProjectManagement') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM IssueCategories")
                cat_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM IssueCategoryKeywords")
                kw_count = cursor.fetchone()[0]
        except Exception as e:
            print(f"❌ Error checking seed status: {e}")
            cat_count = 0
            kw_count = 0
        
        if cat_count == 0:
            print("\nCategories table is empty. Seeding...")
            seed_categories()
        else:
            print(f"\n✓ Categories already seeded: {cat_count} categories")
        
        if kw_count == 0:
            print("\nKeywords table is empty. Seeding...")
            seed_keywords()
        else:
            print(f"\n✓ Keywords already seeded: {kw_count} keywords")
    
    # Step 3: Verify
    verify_system()
    
    print("\n" + "=" * 70)
    print("SETUP COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Run: python services/issue_text_processor.py")
    print("2. Run: python services/issue_categorizer.py")
    print("=" * 70)
