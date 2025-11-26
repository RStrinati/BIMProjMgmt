# APS OAuth Setup Guide - 2-Legged & 3-Legged for Hub Access

## Overview
This guide explains how to set up both 2-legged (app-level) and 3-legged (user-level) OAuth authentication for Autodesk Platform Services (APS) with full hub access including admin permissions.

## Prerequisites

### 1. Autodesk Developer Console Setup
**CRITICAL**: Your APS app must be configured correctly in the developer console.

**Go to**: https://developer.autodesk.com/myapps
**Current App ID**: `HSIzVK9vT8AGY0emotXgOylhsczvoO0XSPy6M76vAAovAeN8`

### 2. Required API Access
Your app MUST have these APIs enabled:

✅ **Authentication API** (automatically included)
✅ **Data Management API** (required for data:read, data:write, account:read scopes)
✅ **ACC Model Coordinate API** (for BIM 360/ACC hub access)
✅ **Model Derivative API** (for viewing models)

**If missing**: Contact Autodesk support or create a new app with proper API access.

## OAuth Flow Configuration

### 2-Legged OAuth (App-Level Access)
**Purpose**: App can access hubs/projects without user login
**Scopes Used**: `account:read data:read data:write viewables:read`

```javascript
// Current implementation in /login-2legged endpoint
const scopes = 'account:read data:read data:write viewables:read';
```

**Key Requirements:**
- `account:read` is ESSENTIAL for hub access
- App must be added to ACC/BIM 360 projects by an admin
- Works for accessing projects where the app has permissions

### 3-Legged OAuth (User-Level Access)
**Purpose**: User authenticates and app acts on their behalf
**Scopes Used**: `user-profile:read data:read data:write account:read account:write viewables:read`

```javascript
// Current implementation in /login and /login-pkce endpoints
const scopes = [
    'user-profile:read',     // User information
    'data:read',             // Read project data  
    'data:write',            // Write project data
    'account:read',          // Essential for hub access
    'account:write',         // For admin operations on hubs
    'viewables:read'         // View models and documents
].join(' ');
```

**Key Benefits:**
- `account:write` allows admin operations on hubs
- Access to all hubs where user is admin/member
- Can perform user-specific operations

## Testing the Setup

### Test 2-Legged OAuth
1. **Visit**: http://localhost:3000/login-2legged
2. **Expected Success Response**:
   ```json
   {
     "success": true,
     "message": "✅ 2-legged OAuth successful!",
     "tokenInfo": {
       "token_type": "Bearer",
       "expires_in": 3599,
       "scope": "account:read data:read data:write viewables:read"
     }
   }
   ```
3. **If it fails**: Check the troubleshooting section below

### Test 3-Legged OAuth
1. **Visit**: http://localhost:3000/login
2. **Follow the authentication flow**
3. **Expected**: Redirects to Autodesk login, then back with success

### Test Hub Access
After successful OAuth, test hub access:
```
GET http://localhost:3000/hubs
```

**Expected Response**: List of ACC/BIM 360 hubs where you have access

## Troubleshooting

### "invalid_scope" Error in 2-Legged OAuth

**Root Cause**: App not configured for required APIs in Developer Console

**Solutions:**
1. **Check App Configuration**:
   - Go to https://developer.autodesk.com/myapps
   - Find app: `HSIzVK9vT8AGY0emotXgOylhsczvoO0XSPy6M76vAAovAeN8`
   - Ensure "Data Management API" is enabled
   - Ensure "ACC Model Coordinate API" is enabled

2. **Create New App** (if current app can't be modified):
   - Create new "Server Application" 
   - Enable all required APIs
   - Update CLIENT_ID and CLIENT_SECRET in index.js

### No Hub Access After Successful OAuth

**Possible Issues:**
1. **User not added to hubs**: Admin must add your user to ACC/BIM 360 hubs
2. **App not added to projects** (2-legged): Admin must add app to specific projects
3. **Missing account:read scope**: Verify scope includes `account:read`

### Authentication Works but Hub List is Empty

**Solutions:**
1. **Verify Admin Access**: Ensure you're admin in target ACC/BIM 360 hubs
2. **Check Project Membership**: Verify you're member of projects in hubs
3. **Test Different User**: Try with different admin user account

## Hub Access Requirements

### For 2-Legged OAuth (App Access)
- App must be added to ACC/BIM 360 projects by hub admin
- App needs `account:read` scope minimum
- Limited to projects where app is explicitly added

### For 3-Legged OAuth (User Access)  
- User must be admin/member of ACC/BIM 360 hubs
- User authenticates and grants permission
- Access to all hubs/projects where user has permissions
- With `account:write` scope, can perform admin operations

## Current Implementation Status

✅ **2-Legged OAuth**: Updated with proper scopes for hub access
✅ **3-Legged OAuth**: Updated with admin-level scopes
✅ **Hub Access Endpoints**: `/hubs`, `/projects/{hubId}` available
✅ **Error Handling**: Enhanced diagnostics for troubleshooting

## Next Steps

1. **Test both OAuth flows** using the endpoints above
2. **Verify hub access** works with your admin account  
3. **If issues persist**: Check Autodesk Developer Console app configuration
4. **For production**: Move CLIENT_ID/CLIENT_SECRET to environment variables

---

**Need Help?**
- Check the enhanced error messages in the application
- Visit `/diagnose` endpoint for detailed diagnostic information
- Ensure your Autodesk account has admin access to target hubs