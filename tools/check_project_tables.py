#!/usr/bin/env python3
"""
Script to analyze project tables structure and data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
import pyodbc

def check_table_structure_and_data(table_name):
    """Check table structure and sample data"""
    with get_db_connection() as conn:
    if conn is None:
        print(f"❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        print(f"\n{'='*60}")
        print(f"TABLE: {table_name}")
        print(f"{'='*60}")
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
        """, (table_name,))
        
        if cursor.fetchone()[0] == 0:
            print(f"❌ Table '{table_name}' does not exist")
            return
        
        # Get table structure
        print(f"\n📋 STRUCTURE:")
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """, (table_name,))
        
        columns = cursor.fetchall()
        print(f"{'Column Name':<25} {'Data Type':<15} {'Nullable':<10} {'Max Length':<12} {'Default'}")
        print("-" * 80)
        
        for col in columns:
            col_name, data_type, nullable, default, max_length = col
            max_len_str = str(max_length) if max_length else "N/A"
            default_str = str(default) if default else "N/A"
            print(f"{col_name:<25} {data_type:<15} {nullable:<10} {max_len_str:<12} {default_str}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"\n📊 TOTAL ROWS: {row_count}")
        
        if row_count > 0:
            # Get sample data (first 10 rows)
            cursor.execute(f"SELECT TOP 10 * FROM {table_name}")
            sample_data = cursor.fetchall()
            
            print(f"\n📝 SAMPLE DATA (first 10 rows):")
            column_names = [desc[0] for desc in cursor.description]
            
            # Print headers
            header = " | ".join(f"{name[:15]:<15}" for name in column_names)
            print(header)
            print("-" * len(header))
            
            # Print sample rows
            for row in sample_data:
                row_str = " | ".join(f"{str(val)[:15]:<15}" if val is not None else f"{'NULL':<15}" for val in row)
                print(row_str)
        
    except Exception as e:
        print(f"❌ Error checking table {table_name}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:

def check_relationships():
    """Check relationships between projects and project_aliases tables"""
    with get_db_connection() as conn:
    if conn is None:
        print(f"❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        print(f"\n{'='*60}")
        print("RELATIONSHIP ANALYSIS")
        print(f"{'='*60}")
        
        # Check if both tables exist
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME IN ('projects', 'project_aliases') AND TABLE_TYPE = 'BASE TABLE'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        if 'projects' not in existing_tables:
            print("❌ 'projects' table not found")
            return
        if 'project_aliases' not in existing_tables:
            print("❌ 'project_aliases' table not found")
            return
        
        # Check foreign key relationships
        cursor.execute("""
            SELECT 
                fk.name AS FK_Name,
                tp.name AS Parent_Table,
                cp.name AS Parent_Column,
                tr.name AS Referenced_Table,
                cr.name AS Referenced_Column
            FROM sys.foreign_keys fk
            INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
            INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
            INNER JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
            INNER JOIN sys.columns cp ON fkc.parent_column_id = cp.column_id AND fkc.parent_object_id = cp.object_id
            INNER JOIN sys.columns cr ON fkc.referenced_column_id = cr.column_id AND fkc.referenced_object_id = cr.object_id
            WHERE tp.name = 'project_aliases' OR tr.name = 'project_aliases' OR tp.name = 'projects' OR tr.name = 'projects'
        """)
        
        fks = cursor.fetchall()
        if fks:
            print("🔗 FOREIGN KEY RELATIONSHIPS:")
            for fk in fks:
                print(f"  {fk[0]}: {fk[1]}.{fk[2]} -> {fk[3]}.{fk[4]}")
        else:
            print("ℹ️ No foreign key relationships found between these tables")
        
        # Try to find logical relationships by examining data
        try:
            cursor.execute("""
                SELECT TOP 5 
                    p.project_id as p_id, 
                    p.project_name as p_name,
                    pa.project_id as pa_project_id,
                    pa.alias_name
                FROM projects p
                LEFT JOIN project_aliases pa ON p.project_id = pa.project_id
                WHERE pa.project_id IS NOT NULL
            """)
            
            matches = cursor.fetchall()
            if matches:
                print(f"\n🎯 SAMPLE MATCHING RECORDS:")
                print(f"{'Project ID':<12} {'Project Name':<25} {'Alias':<25}")
                print("-" * 65)
                for match in matches:
                    print(f"{match[0]:<12} {match[1][:24]:<25} {match[3][:24]:<25}")
            else:
                print(f"\n⚠️ No matching records found using project_id")
                
                # Try alternative matching approaches
                cursor.execute("SELECT TOP 3 * FROM project_aliases")
                aliases = cursor.fetchall()
                if aliases:
                    print(f"\nSample project_aliases data for analysis:")
                    alias_columns = [desc[0] for desc in cursor.description]
                    print(f"Columns: {alias_columns}")
                    for alias in aliases:
                        print(f"  {alias}")
                        
        except Exception as e:
            print(f"⚠️ Error checking relationships: {str(e)}")
    
    except Exception as e:
        print(f"❌ Error in relationship analysis: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:

if __name__ == "__main__":
    print("🔍 CHECKING PROJECT MANAGEMENT TABLES")
    print(f"Database: ProjectManagement")
    
    # Check both tables
    check_table_structure_and_data("projects")
    check_table_structure_and_data("project_aliases")
    
    # Analyze relationships
    check_relationships()
    
    print(f"\n✅ TABLE ANALYSIS COMPLETE")