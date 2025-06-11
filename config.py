import os

DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
DB_SERVER = os.getenv("DB_SERVER", "P-NB-USER-028\\SQLEXPRESS")
DB_USER = os.getenv("DB_USER", "admin02")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")

# Default database names
PROJECT_MGMT_DB = os.getenv("PROJECT_MGMT_DB", "ProjectManagement")
ACC_DB = os.getenv("ACC_DB", "acc_data_schema")
REVIT_HEALTH_DB = os.getenv("REVIT_HEALTH_DB", "RevitHealthCheckDB")
