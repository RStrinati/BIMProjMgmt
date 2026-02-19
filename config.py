import os
from pathlib import Path

def _load_env_from_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if not key:
            continue
        if key not in os.environ or os.environ.get(key, "") == "":
            os.environ[key] = val
try:
    from dotenv import load_dotenv
    # Load repo-root .env regardless of current working directory
    repo_root_env = Path(__file__).resolve().parent / ".env"
    # Use override=True so values in .env take precedence over empty shell vars.
    load_dotenv(dotenv_path=repo_root_env, override=True)
except ModuleNotFoundError:
    # The optional dependency python-dotenv is not installed in some
    # environments (e.g. during CI tests). Falling back to environment
    # variables only keeps the configuration flexible without raising an
    # import error.
    repo_root_env = Path(__file__).resolve().parent / ".env"
    _load_env_from_file(repo_root_env)

class Config:
    # SQL Server DB config
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    # Default to local SQLEXPRESS via shared memory; override with DB_SERVER as needed.
    DB_SERVER = os.getenv("DB_SERVER", r".\SQLEXPRESS")
    DB_USER = os.getenv("DB_USER")  # SECURITY: No default - must be explicitly set
    DB_PASSWORD = os.getenv("DB_PASSWORD")  # SECURITY: No default - must be explicitly set
    
    # Validate critical credentials are set
    if not DB_USER or not DB_PASSWORD:
        raise ValueError(
            "CRITICAL: Database credentials not configured. "
            "Set DB_USER and DB_PASSWORD environment variables before running."
        )

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
