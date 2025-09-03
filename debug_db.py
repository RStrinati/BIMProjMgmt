"""
Debug script to check database contents
"""
from database import connect_to_db
from constants import schema as S

def check_projects_table():
    """Check what's in the projects table"""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        print("❌ Cannot connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        # Check projects table structure and data
        print("=== PROJECTS TABLE ===")
        cursor.execute(f"""
            SELECT TOP 3 {S.Projects.ID}, {S.Projects.NAME}, {S.Projects.CLIENT_ID}, 
                   {S.Projects.START_DATE}, {S.Projects.END_DATE}
            FROM dbo.{S.Projects.TABLE}
        """)
        
        rows = cursor.fetchall()
        for row in rows:
            print(f"Project ID: {row[0]}, Name: {row[1]}, Client ID: {row[2]}, Start: {row[3]}, End: {row[4]}")
        
        # Check if clients table has any data
        print("\n=== CLIENTS TABLE ===")
        cursor.execute(f"""
            SELECT TOP 3 {S.Clients.CLIENT_ID}, {S.Clients.CLIENT_NAME}, 
                   {S.Clients.CONTACT_NAME}, {S.Clients.CONTACT_EMAIL}
            FROM dbo.{S.Clients.TABLE}
        """)
        
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"Client ID: {row[0]}, Name: {row[1]}, Contact: {row[2]}, Email: {row[3]}")
        else:
            print("No clients found in table")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_projects_table()
