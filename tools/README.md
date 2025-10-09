# Tools Directory - Configuration Guide

## 🔒 Secure Configuration Management

This directory contains tools and utilities for the BIM Project Management system, including **secure configuration management** to prevent credential exposure.

## Quick Start

### 1. First-Time Setup

```bash
# Copy the template to create your local configuration
copy appsettings.template.json appsettings.json

# Edit appsettings.json with your actual credentials
notepad appsettings.json
```

### 2. Configure Your Credentials

Edit `appsettings.json` with your actual values:

```json
{
  "ReviztoAPI": {
    "BaseUrl": "https://api.sydney.revizto.com",
    "Region": "sydney",
    "AccessToken": "your-actual-access-token",
    "RefreshToken": "your-actual-refresh-token",
    "TokenUpdatedAt": "2025-10-09T00:00:00.0000000+00:00"
  },
  "Database": {
    "ConnectionString": "Server=YOUR_SERVER\\INSTANCE;Database=YOUR_DATABASE;Trusted_Connection=True;"
  },
  "ExportSettings": {
    "OutputDirectory": "C:\\Path\\To\\Your\\Exports",
    "LogDirectory": "C:\\Path\\To\\Your\\Logs"
  }
}
```

### 3. Verify Configuration

```bash
# Test that configuration loads correctly
python config_loader.py
```

Expected output:
```
=== Configuration Loader Test ===

✅ Configuration loaded successfully

Revizto API:
  Base URL: https://api.sydney.revizto.com
  Region: sydney
  Access Token: ***configured***
  Refresh Token: ***configured***

Database:
  Connection String: ***configured***
```

## Files in This Directory

| File | Description | Version Control |
|------|-------------|-----------------|
| `appsettings.json` | **Your actual credentials** | ❌ **NEVER COMMIT** (in .gitignore) |
| `appsettings.template.json` | Placeholder template for team | ✅ Safe to commit |
| `config_loader.py` | Secure configuration utility | ✅ Safe to commit |

## Usage in Code

### Basic Configuration Loading

```python
from tools.config_loader import load_config

config = load_config()
access_token = config['ReviztoAPI']['AccessToken']
```

### Get Specific Configuration

```python
from tools.config_loader import get_connection_string, get_revizto_config

# Database connection
conn_string = get_connection_string()

# Revizto API settings
revizto = get_revizto_config()
base_url = revizto['BaseUrl']
access_token = revizto['AccessToken']
```

### Environment Variable Overrides

Environment variables take priority over `appsettings.json`:

```powershell
# Windows PowerShell
$env:REVIZTO_ACCESS_TOKEN="your-new-token"
$env:DB_CONNECTION_STRING="Server=PROD_SERVER;Database=ProdDB;..."

# Run your application - it will use these values
python your_script.py
```

Supported environment variables:
- `REVIZTO_BASE_URL`
- `REVIZTO_REGION`
- `REVIZTO_ACCESS_TOKEN`
- `REVIZTO_REFRESH_TOKEN`
- `DB_CONNECTION_STRING`
- `EXPORT_OUTPUT_DIR`
- `EXPORT_LOG_DIR`
- `LOG_LEVEL`

### Update Revizto Tokens

```python
from tools.config_loader import update_revizto_tokens

# After refreshing your API tokens
update_revizto_tokens(
    access_token="new-access-token",
    refresh_token="new-refresh-token"
)
```

## Security Best Practices

### ✅ DO

- ✅ Copy `appsettings.template.json` to `appsettings.json` locally
- ✅ Keep your `appsettings.json` file secure and private
- ✅ Use environment variables for production deployments
- ✅ Rotate API tokens regularly
- ✅ Verify `appsettings.json` is in `.gitignore`

### ❌ DON'T

- ❌ Commit `appsettings.json` to version control
- ❌ Share your `appsettings.json` file via email/chat
- ❌ Hardcode credentials in Python scripts
- ❌ Store credentials in public repositories
- ❌ Use production credentials in development

### Verify Security

```bash
# Confirm appsettings.json is ignored
git check-ignore tools/appsettings.json
# Should output: tools/appsettings.json

# Check git status
git status
# Should NOT show appsettings.json
```

## Troubleshooting

### Error: "Configuration contains placeholder value"

**Problem**: You're using the template file without configuring actual values.

**Solution**:
```bash
# 1. Copy template to appsettings.json
copy appsettings.template.json appsettings.json

# 2. Edit with your actual credentials
notepad appsettings.json

# 3. Test again
python config_loader.py
```

### Error: "appsettings.json not found"

**Problem**: Configuration file doesn't exist.

**Solution**: Copy the template as shown above.

### Configuration Not Taking Effect

**Problem**: Changes to `appsettings.json` aren't being used.

**Solution**: Check if environment variables are overriding your values:
```powershell
# View current environment variables
Get-ChildItem Env: | Where-Object {$_.Name -like "*REVIZTO*" -or $_.Name -like "*DB_*"}

# Clear specific variable if needed
Remove-Item Env:REVIZTO_ACCESS_TOKEN
```

## Team Setup Instructions

When onboarding new team members:

1. **Share this README** and the template file
2. **Do NOT share** your `appsettings.json` file
3. **Provide credentials** via secure channel (password manager, secure chat)
4. **Instruct them** to copy template and configure locally
5. **Verify** they understand `.gitignore` prevents credential commits

## Production Deployment

For production environments, use environment variables instead of `appsettings.json`:

```bash
# Set environment variables in your deployment environment
# Azure App Service, AWS, Docker, etc.

REVIZTO_ACCESS_TOKEN=production-token
DB_CONNECTION_STRING=production-connection-string
LOG_LEVEL=Warning
```

The `config_loader.py` automatically prioritizes environment variables over file-based configuration.

## Support

If you encounter configuration issues:

1. Run `python config_loader.py` to test
2. Check `.gitignore` includes `tools/appsettings.json`
3. Verify no placeholder values remain in your config
4. Check environment variables aren't conflicting
5. Consult the main project README for database setup

---

**Remember**: Your `appsettings.json` contains sensitive credentials. Treat it like a password file and never commit it to version control!
