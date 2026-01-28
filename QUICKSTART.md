# Quick Start - Environment Setup

## ✅ Files Created

1. **`.env`** - Your local environment configuration (already created with placeholder values)
2. **`.env.example`** - Template for team members (can be committed to Git)
3. **`.gitignore`** - Already configured to exclude `.env` from version control

## 🚀 Next Steps

### 1. Update Database Credentials

Open `.env` and replace these placeholder values with your actual credentials:

```bash
DB_USER=your_database_username_here     # ← Change this
DB_PASSWORD=your_secure_password_here   # ← Change this
```

For example:
```bash
DB_USER=sa
DB_PASSWORD=MySecurePassword123!
```

### 2. Verify Configuration

Run the security verification script:

```bash
python tools/verify_security_fixes.py
```

Expected output: `✅ All security checks passed!`

### 3. Start the Application

```bash
# Backend (Terminal 1)
cd backend
python app.py

# Frontend (Terminal 2)
cd frontend
npm run dev
```

## 🔒 Security Notes

- ✅ `.env` is already in `.gitignore` - it will NOT be committed
- ✅ `.env.example` is the template - this CAN be committed
- ⚠️ **NEVER** commit your actual `.env` file with credentials
- ⚠️ **NEVER** share your `.env` file or credentials in chat/email

## 📝 Configuration Reference

### Required (Must Change)
- `DB_USER` - Your SQL Server username
- `DB_PASSWORD` - Your SQL Server password

### Optional (Good Defaults)
- `CORS_ORIGINS` - Already set for local development
- `LOG_LEVEL` - Set to `DEBUG` for development, `INFO` for production
- `DB_SERVER` - Already set to `.\SQLEXPRESS` (local SQL Express)

### Production Deployment

When deploying to production:

1. Change `LOG_LEVEL=INFO`
2. Update `CORS_ORIGINS` to your actual domain(s):
   ```bash
   CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
   ```
3. Use stronger credentials
4. Consider using a secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)

## 🆘 Troubleshooting

### "Database credentials not configured" error
- Open `.env` and set `DB_USER` and `DB_PASSWORD` with actual values
- Make sure there are no quotes around the values
- Restart the application after changing

### CORS errors in browser
- Check `CORS_ORIGINS` in `.env` matches your frontend URL
- Default is `http://localhost:5173,http://localhost:3000`

### Can't find .env file
- Make sure you're in the project root directory
- File might be hidden - enable "Show hidden files" in your file explorer
- On Windows: `dir /a` to see hidden files
- On Linux/Mac: `ls -la` to see hidden files

## 📚 Additional Documentation

- [Full Security Audit](docs/security/SECURITY_AUDIT.md)
- [Complete Environment Setup Guide](docs/security/ENVIRONMENT_SETUP.md)
- [Security Fixes Summary](SECURITY_FIXES_SUMMARY.md)
