from database import get_projects, connect_to_db
from constants import schema as S

print("Testing project loading...")

# Test get_projects function
try:
    projects = get_projects()
    print(f"get_projects() returned: {projects}")
    print(f"Number of projects: {len(projects)}")
except Exception as e:
    print(f"Error with get_projects(): {e}")

# Test direct query
try:
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {S.Projects.TABLE}")
        count = cursor.fetchone()[0]
        print(f"Total projects in database: {count}")

        if count > 0:
            cursor.execute(f"SELECT TOP 5 {S.Projects.ID}, {S.Projects.NAME} FROM {S.Projects.TABLE}")
            rows = cursor.fetchall()
            print(f"Sample projects: {rows}")

        conn.close()
    else:
        print("Database connection failed")
except Exception as e:
    print(f"Error with direct query: {e}")