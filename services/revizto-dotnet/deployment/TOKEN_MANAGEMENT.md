# Token Management & Expiration Handling

## Overview
The Revizto Data Exporter now features comprehensive automatic token management that handles both access token and refresh token expiration scenarios.

## How Token Expiration Works

### 1. **Proactive Token Checking** (Now Enabled)
- **When**: Before every API call
- **Check**: Examines JWT expiration timestamp 
- **Threshold**: Refreshes token if it expires within 5 minutes
- **Benefit**: Prevents 401 errors and maintains smooth operation

### 2. **Reactive Token Refresh** (Fallback)
- **When**: If proactive check fails and API returns 401 Unauthorized
- **Action**: Automatically refreshes token and retries the failed request
- **Benefit**: Handles edge cases and unexpected token issues

## Token Refresh Process

### Automatic Refresh Steps:
1. **Detect Expiration**: System checks JWT `exp` claim (handles decimal timestamps)
2. **Call Refresh API**: `POST /v5/oauth2` with refresh token
3. **Receive New Tokens**: Gets new access token and potentially new refresh token
4. **Update Configuration**: Saves tokens to `appsettings.json`
5. **Continue Operation**: Resumes API calls with new token

### Token Rotation Support:
- If Revizto provides a new refresh token, it's used for future refreshes
- If no new refresh token is provided, the existing one continues to work
- Handles both rotating and non-rotating refresh token patterns

## What Happens When Tokens Expire

### Access Token Expiration (Normal):
✅ **Handled Automatically**
- System detects expiration 5 minutes before it occurs
- Refreshes token seamlessly in background
- No interruption to data export operations
- Updates `appsettings.json` with new tokens

### Refresh Token Expiration (Rare):
❌ **Requires Re-authentication**
- System throws `RefreshTokenExpiredException`
- Application stops with clear error message
- User needs to obtain new API key from Revizto
- Use authentication helper to get fresh tokens

## Error Scenarios & Recovery

### Scenario 1: Network Issues During Refresh
- **Error**: HTTP timeout or connection failure
- **Recovery**: Automatic retry logic in API calls
- **Fallback**: Reactive refresh on next 401 error

### Scenario 2: Refresh Token Revoked
- **Error**: 403 Forbidden during refresh attempt
- **Recovery**: None - requires manual re-authentication
- **Action**: Get new API key from Revizto portal

### Scenario 3: Invalid Token Response
- **Error**: Malformed or incomplete response from refresh endpoint
- **Recovery**: System logs detailed error information
- **Action**: Check logs and potentially re-authenticate

## Monitoring Token Health

### Log Messages to Watch:
```
[INF] Access token is expired or will expire soon. Refreshing...
[INF] Access token successfully refreshed. New refresh token provided: true/false
[ERR] Refresh token appears to be expired or invalid. Re-authentication required.
```

### Token Information:
- **Access Token Lifetime**: Typically 1 hour
- **Refresh Token Lifetime**: Varies (days to months)
- **Refresh Threshold**: 5 minutes before expiration
- **Retry Logic**: 3 attempts with exponential backoff

## Configuration Files

### appsettings.json Structure:
```json
{
  "ReviztoAPI": {
    "AccessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJS...",
    "RefreshToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJS...",
    "BaseUrl": "https://app.revizto.com/api",
    "ApiKey": "your-api-key-here"
  }
}
```

## Best Practices

### For Long-Running Operations:
- Monitor logs for refresh activities
- Ensure `appsettings.json` is writable
- Keep backup of working configuration
- Test token refresh in non-production environment

### For Production Deployment:
- Set up log monitoring for token errors
- Implement alerting for `RefreshTokenExpiredException`
- Document re-authentication procedure
- Consider token lifecycle in deployment scripts

## Troubleshooting

### If Exports Keep Failing:
1. Check logs for token-related errors
2. Verify `appsettings.json` is not read-only
3. Confirm Revizto API endpoint is accessible
4. Test with fresh API key if needed

### If Tokens Not Refreshing:
1. Verify refresh token is still valid
2. Check network connectivity to Revizto
3. Ensure proper permissions on config file
4. Look for detailed error messages in logs

---
**Last Updated**: September 29, 2025  
**Status**: Fully Automated Token Management Active