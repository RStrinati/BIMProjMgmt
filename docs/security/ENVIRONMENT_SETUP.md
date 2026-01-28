# Environment Configuration Guide

## Production Environment Setup

After the security fixes, you **MUST** configure these environment variables before running the application:

### Critical (No Defaults - Application Won't Start Without These)

```bash
# Database Credentials - MUST be set explicitly
export DB_USER=your_db_username
export DB_PASSWORD=your_db_password
```

### Security Configuration

```bash
# CORS Origins - Restrict to your domain(s)
export CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Logging Level - Use INFO in production, DEBUG only for development
export LOG_LEVEL=INFO
```

### Optional (Have Sensible Defaults)

```bash
# Database Configuration
export DB_SERVER=.\SQLEXPRESS                    # SQL Server instance
export DB_DRIVER="ODBC Driver 17 for SQL Server" # ODBC driver version
export PROJECT_MGMT_DB=ProjectManagement         # Main database
export WAREHOUSE_DB=ProjectManagement            # Analytics database

# External Services
export ACC_SERVICE_URL=http://localhost:4000/api/v1
export REVIZTO_SERVICE_URL=http://localhost:5000/api/v1
export APS_AUTH_SERVICE_URL=http://localhost:3000
export APS_AUTH_LOGIN_PATH=/login-pkce

# Service Tokens (if using token-based authentication)
export ACC_SERVICE_TOKEN=your_acc_token
export REVIZTO_SERVICE_TOKEN=your_revizto_token
```

## Setup Methods

### Method 1: .env File (Recommended for Development)

Create `.env` file in project root:

```env
# .env
DB_USER=dev_user
DB_PASSWORD=dev_secure_password
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
LOG_LEVEL=DEBUG
```

**Important**: Add `.env` to `.gitignore`:
```bash
echo ".env" >> .gitignore
```

### Method 2: System Environment Variables (Recommended for Production)

**Windows (PowerShell)**:
```powershell
[Environment]::SetEnvironmentVariable("DB_USER", "prod_user", "User")
[Environment]::SetEnvironmentVariable("DB_PASSWORD", "prod_secure_password", "User")
[Environment]::SetEnvironmentVariable("CORS_ORIGINS", "https://yourdomain.com", "User")
[Environment]::SetEnvironmentVariable("LOG_LEVEL", "INFO", "User")
```

**Windows (Command Prompt)**:
```cmd
setx DB_USER prod_user
setx DB_PASSWORD prod_secure_password
setx CORS_ORIGINS https://yourdomain.com
setx LOG_LEVEL INFO
```

**Linux/macOS (.bashrc or .zshrc)**:
```bash
export DB_USER=prod_user
export DB_PASSWORD=prod_secure_password
export CORS_ORIGINS=https://yourdomain.com
export LOG_LEVEL=INFO
```

### Method 3: Docker (Recommended for Containerized Deployments)

**Dockerfile**:
```dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV CORS_ORIGINS=${CORS_ORIGINS}
ENV LOG_LEVEL=INFO
CMD ["python", "backend/app.py"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      DB_USER: ${DB_USER}
      DB_PASSWORD: ${DB_PASSWORD}
      CORS_ORIGINS: ${CORS_ORIGINS}
      LOG_LEVEL: INFO
    ports:
      - "5000:5000"
```

### Method 4: Kubernetes Secrets (Enterprise)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: bim-secrets
type: Opaque
stringData:
  DB_USER: prod_user
  DB_PASSWORD: prod_secure_password
  CORS_ORIGINS: https://yourdomain.com
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: bim-config
data:
  LOG_LEVEL: "INFO"
```

## Verification

Before deploying, verify your configuration:

```python
# test_config.py
from config import Config

print(f"Database: {Config.DB_SERVER}")
print(f"Database User: {'***' if Config.DB_USER else 'NOT SET'}")
print(f"CORS Origins: Configured" if hasattr(Config, 'CORS_ORIGINS') else "Using defaults")
print(f"Log Level: {Config.LOG_LEVEL}")

# Try to create a connection
from database_pool import db_manager
try:
    with db_manager.get_connection() as conn:
        print("✓ Database connection successful")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
```

Run: `python test_config.py`

## Security Checklist

Before production deployment:

- [ ] `DB_USER` and `DB_PASSWORD` are set (not defaults)
- [ ] `CORS_ORIGINS` points to your actual domain
- [ ] `LOG_LEVEL` is set to `INFO` (not `DEBUG`)
- [ ] All secrets are stored securely (not in code)
- [ ] `.env` file is in `.gitignore`
- [ ] Database connection test passes
- [ ] No credentials in Git history
- [ ] Backup plan for credentials exists
- [ ] Certificate/TLS configured for HTTPS

## Common Issues

### "CRITICAL: Database credentials not configured"
**Solution**: Set `DB_USER` and `DB_PASSWORD` environment variables

### CORS errors in browser
**Solution**: Update `CORS_ORIGINS` to match your frontend domain
```bash
export CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Logging too verbose
**Solution**: Set `LOG_LEVEL=INFO` for production
```bash
export LOG_LEVEL=INFO
```

### Database connection timeout
**Solution**: Check database server is running and credentials are correct
```bash
# Test connection
python -c "from database_pool import db_manager; db_manager.get_connection()"
```

## References

- [OWASP Environment Variables](https://owasp.org/www-community/attacks/Environment_Variable_Manipulation)
- [12 Factor App - Configuration](https://12factor.net/config)
- [Flask Configuration Best Practices](https://flask.palletsprojects.com/en/3.0.x/config/)
