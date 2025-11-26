# Hub Access Troubleshooting Guide

## 🎯 Your Current Issue: App Not Provisioned to Other Hubs

Based on your description, you can see your own hub but not others where you have access. This is the **classic app provisioning issue**.

## 🔍 Step 1: Run Diagnostic

First, let's get a detailed diagnosis of your current situation:

```bash
# After completing OAuth authentication, visit:
http://localhost:3000/diagnose-hub-access
```

This new endpoint will:
- ✅ Test your current tokens
- 🔍 Identify specific missing provisioning
- 📋 Provide exact steps to fix each issue
- 🌍 Test EMEA region support if needed

## 🚨 Step 2: The Root Cause

**Even with 3-legged OAuth, your app must be provisioned to each ACC/BIM 360 account.**

Your CLIENT_ID `HSIzVK9vT8AGY0emotXg...` is probably only provisioned to:
- ✅ Your own ACC/BIM 360 account (that's why you see your hub)
- ❌ SINSW hub (and others where you're admin/member)

## 🔧 Step 3: Fix App Provisioning

### For Each Hub You Need Access To:

#### A. **Contact Account Admin**
Find the **Account Admin** for each hub (SINSW, etc.) and send them this message:

---

**Subject**: APS App Provisioning Request - Custom Integration Setup

Hi [Account Admin Name],

I need to add a custom APS (Autodesk Platform Services) application to access our ACC/BIM 360 data. Could you please help me provision the following app?

**App Details:**
- **Client ID**: `HSIzVK9vT8AGY0emotXgOylhsczvoO0XSPy6M76vAAovAeN8`
- **App Name**: APS OAuth Demo (or whatever name you prefer)
- **Required Permissions**:
  - ✅ **Document Management** (required for file/project access)
  - ✅ **Account Admin** (optional, for admin operations)

**Steps to Add the App:**
1. Log into ACC/BIM 360
2. Go to **Account Admin → Settings → Custom Integrations**
3. Click **"Add Custom Integration"**
4. Enter the Client ID above
5. Select **"Document Management"** permission
6. Select **"Account Admin"** permission (if admin operations needed)
7. **Approve** the integration

**If "Custom Integrations" menu is missing:**
Please email **bim360appsactivations@autodesk.com** to enable Custom Integrations for this account.

Thanks!

---

#### B. **Verify Your Project Access**
Even after app provisioning, ensure you have **"Docs → Files"** access in each project:

1. **Test in Browser**: Go to ACC/BIM 360 web interface
2. **Navigate**: To each project you expect to see
3. **Check**: Can you open **Docs → Files**?
4. **If No**: Request project access from project admin

## 🧪 Step 4: Test the Fix

### After App Provisioning:

1. **Re-authenticate** (get fresh token):
   ```
   http://localhost:3000/login
   ```

2. **Test hub access**:
   ```
   http://localhost:3000/hubs
   ```

3. **Run diagnostics**:
   ```
   http://localhost:3000/diagnose-hub-access
   ```

4. **Test EMEA region** (if applicable):
   ```
   http://localhost:3000/hubs?region=EMEA
   ```

## 🌍 Step 5: EMEA Region Support

If any projects are in Europe, add the region parameter:

```javascript
// For European projects, use:
headers: {
    'x-ads-region': 'EMEA'
}
```

Your app now supports this automatically via:
- Query parameter: `?region=EMEA`
- Header: `x-ads-region: EMEA`

## 🎭 Step 6: Validate with Official Sample

To confirm everything works, test with Autodesk's official sample:

1. **Visit**: [APS Hubs Browser Sample](https://autodesk-forge.github.io/forge-tutorial-postman/tutorial_06_hubs_browser.html)
2. **Login**: With your account
3. **Expected**: Should see ALL hubs you have access to
4. **If Missing**: App provisioning still needed

## 📊 Expected Results After Fix

### Before App Provisioning:
```json
{
    "hubCount": 1,
    "hubs": [
        {
            "id": "b.your-account-id",
            "name": "Your Company Hub"
        }
    ]
}
```

### After App Provisioning:
```json
{
    "hubCount": 3,
    "hubs": [
        {
            "id": "b.your-account-id", 
            "name": "Your Company Hub"
        },
        {
            "id": "b.sinsw-account-id",
            "name": "SINSW Hub" 
        },
        {
            "id": "b.other-account-id",
            "name": "Other Hub"
        }
    ]
}
```

## 🔄 Alternative: Create Account-Specific Apps

If you can't get your app provisioned to other accounts, create separate apps:

1. **Create New App** for each account you need access to
2. **Have Account Admin** create the app directly in their Developer Console
3. **Use Different CLIENT_ID/SECRET** for each account

## ⚡ Quick Test Commands

```bash
# 1. Complete authentication
curl http://localhost:3000/login

# 2. Test hub access
curl http://localhost:3000/hubs

# 3. Run comprehensive diagnostics  
curl http://localhost:3000/diagnose-hub-access

# 4. Test specific hub projects
curl http://localhost:3000/projects/{hubId}
```

## 🎯 Summary

Your issue is **app provisioning**, not code or OAuth configuration. The OAuth flows are working correctly, but each ACC/BIM 360 account admin must add your app to their account for you to see their hubs/projects.

**Next Action**: Contact the Account Admins for SINSW and other hubs using the email template above.

---

**Need Help?** Run `/diagnose-hub-access` for specific guidance based on your current setup.