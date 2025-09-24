from database import connect_to_db

conn = connect_to_db()
cursor = conn.cursor()

print("=== Checking project_id data types ===")
cursor.execute("SELECT TOP 3 project_id, project_name FROM vw_ProjectManagement_AllIssues")
for row in cursor.fetchall():
    print(f"Project ID: {row[0]} (type: {type(row[0])}) - Project: {row[1]}")

print("\n=== Checking Projects table ===")    
cursor.execute("SELECT TOP 3 ProjectID, ProjectName FROM Projects")
for row in cursor.fetchall():
    print(f"Project ID: {row[0]} (type: {type(row[0])}) - Project: {row[1]}")
    
conn.close()