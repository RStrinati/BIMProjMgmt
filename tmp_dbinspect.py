import pyodbc
from config import Config
conn = pyodbc.connect(f"DRIVER={{{Config.DB_DRIVER}}};SERVER={Config.DB_SERVER};DATABASE={Config.REVIT_HEALTH_DB};UID={Config.DB_USER};PWD={Config.DB_PASSWORD}")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM dbo.tblRvtProjHealth")
print('rows:', cur.fetchone()[0])
cols = None
cur.execute("SELECT TOP 1 * FROM dbo.tblRvtProjHealth ORDER BY nId DESC")
row = cur.fetchone()
cols = [desc[0] for desc in cur.description]
if row:
    print('column sizes (strings only):')
    for col, val in zip(cols, row):
        if isinstance(val, str):
            print(f"  {col}: {len(val)} chars")
cur.execute("SELECT SUM(DATALENGTH(jsonViews)) FROM dbo.tblRvtProjHealth")
print('total jsonViews bytes:', cur.fetchone()[0])
cur.execute("SELECT SUM(DATALENGTH(jsonFamilies)) FROM dbo.tblRvtProjHealth")
print('total jsonFamilies bytes:', cur.fetchone()[0])
cur.execute("SELECT SUM(DATALENGTH(jsonFamily_sizes)) FROM dbo.tblRvtProjHealth")
print('total jsonFamily_sizes bytes:', cur.fetchone()[0])
cur.execute("SELECT SUM(DATALENGTH(jsonWarnings)) FROM dbo.tblRvtProjHealth")
print('total jsonWarnings bytes:', cur.fetchone()[0])
conn.close()
