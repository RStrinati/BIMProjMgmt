# Create New APS App for 2-Legged OAuth

## Steps to Create a New App

1. **Go to Autodesk Developer Console**: https://developer.autodesk.com/myapps
2. **Click "Create App"**
3. **Configure the app:**
   - **App Name**: "APS Demo 2-Legged OAuth"
   - **App Type**: "Server Application" (supports both 2-legged and 3-legged)
   - **Description**: "Demo app for 2-legged OAuth testing"
   
4. **Enable Required APIs:**
   - ✅ **Authentication API** (automatic)
   - ✅ **Data Management API** (for data:read, data:write scopes)
   - ✅ **Model Derivative API** (for model viewing)
   - ✅ **Design Automation API** (optional, for advanced features)

5. **Copy the new credentials:**
   - Client ID
   - Client Secret

6. **Update index.js with new credentials:**
   ```javascript
   const CLIENT_ID = 'YOUR_NEW_CLIENT_ID';
   const CLIENT_SECRET = 'YOUR_NEW_CLIENT_SECRET';
   ```

## Testing the New App

After creating the new app, test the 2-legged OAuth:
- Visit: http://localhost:3000/login-2legged
- Should return success with access token

## Common Scopes for 2-Legged OAuth

```javascript
// Basic data access
'data:read data:write'

// With model viewing
'data:read data:write viewables:read'

// For ACC/BIM 360 projects (if app has access)
'data:read data:write account:read'
```

## Important Notes

- 2-legged OAuth doesn't support user-specific scopes like:
  - `user-profile:read`
  - `user-management:read`
- These are only available in 3-legged OAuth flows where user consent is required