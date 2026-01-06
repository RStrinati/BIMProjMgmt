import os
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load variables from .env file if python-dotenv is available
except ModuleNotFoundError:
    # The optional dependency python-dotenv is not installed in some
    # environments (e.g. during CI tests). Falling back to environment
    # variables only keeps the configuration flexible without raising an
    # import error.
    pass

class Config:
    # SQL Server DB config
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    DB_SERVER = os.getenv("DB_SERVER", r"np:\\.\pipe\MSSQL$SQLEXPRESS\sql\query")
    DB_USER = os.getenv("DB_USER", "admin02")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")

    PROJECT_MGMT_DB = os.getenv("PROJECT_MGMT_DB", "ProjectManagement")
    WAREHOUSE_DB = os.getenv("WAREHOUSE_DB", "ProjectManagement")
    ACC_DB = os.getenv("ACC_DB", "acc_data_schema")
    REVIT_HEALTH_DB = os.getenv("REVIT_HEALTH_DB", "RevitHealthCheckDB")
    REVIZTO_DB = os.getenv("REVIZTO_DB", "ReviztoData")

    # External Service Endpoints
    ACC_SERVICE_URL = os.getenv("ACC_SERVICE_URL", "http://localhost:4000/api/v1")
    REVIZTO_SERVICE_URL = os.getenv("REVIZTO_SERVICE_URL", "http://localhost:5000/api/v1")
    APS_AUTH_SERVICE_URL = os.getenv("APS_AUTH_SERVICE_URL", "http://localhost:3000")
    APS_AUTH_LOGIN_PATH = os.getenv("APS_AUTH_LOGIN_PATH", "/login-pkce")

    # Service Auth Tokens (managed by token broker)
    ACC_SERVICE_TOKEN = os.getenv("ACC_SERVICE_TOKEN", "")
    REVIZTO_SERVICE_TOKEN = os.getenv("REVIZTO_SERVICE_TOKEN", "")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_JSON = os.getenv("LOG_JSON", "true").lower() == "true"

# Provide module-level aliases for backwards compatibility with code that
# imports configuration values directly from this module.
PROJECT_MGMT_DB = Config.PROJECT_MGMT_DB
WAREHOUSE_DB = Config.WAREHOUSE_DB
ACC_DB = Config.ACC_DB
REVIT_HEALTH_DB = Config.REVIT_HEALTH_DB
REVIZTO_DB = Config.REVIZTO_DB
ACC_SERVICE_URL = Config.ACC_SERVICE_URL
REVIZTO_SERVICE_URL = Config.REVIZTO_SERVICE_URL
ACC_SERVICE_TOKEN = Config.ACC_SERVICE_TOKEN
REVIZTO_SERVICE_TOKEN = Config.REVIZTO_SERVICE_TOKEN
APS_AUTH_SERVICE_URL = Config.APS_AUTH_SERVICE_URL
APS_AUTH_LOGIN_PATH = Config.APS_AUTH_LOGIN_PATH
