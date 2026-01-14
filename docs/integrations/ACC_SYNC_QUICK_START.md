# ACC Sync Quick Start Guide

## What You Can Do Now

With the enhanced ACC sync feature, you can now:

✅ **Authenticate** with Autodesk Construction Cloud  
✅ **Browse** all accessible hubs and projects  
✅ **View** detailed project information (folders, files, metadata)  
✅ **Explore** model files (RVT, IFC, DWG, NWD, etc.)  
✅ **Review** project issues with status and priority  
✅ **See** team members with roles and contact information  

## Getting Started

### Step 1: Start the APS Auth Demo Service

The ACC sync feature requires the `aps-auth-demo` Node.js service to handle authentication.

```bash
cd services/aps-auth-demo
npm install
node index.js
```

The service should start on `http://localhost:3000`.

### Step 2: Configure Environment Variables

Create a `.env` file in the `services/aps-auth-demo` directory with your Autodesk credentials:

```env
CLIENT_ID=your_autodesk_client_id
CLIENT_SECRET=your_autodesk_client_secret
CALLBACK_URL=http://localhost:3000/callback
PORT=3000
```

**Don't have credentials?** Follow these steps:

1. Go to https://aps.autodesk.com/myapps/
2. Click "Create App"
3. Choose "Web App"
4. Set callback URL: `http://localhost:3000/callback`
5. Enable these APIs:
   - Data Management API
   - Construction Cloud API
   - User Profile API
6. Copy your Client ID and Secret

### Step 3: Start the Backend Flask Server

```bash
# From project root
cd backend
python app.py
```

The backend should start on `http://localhost:5000`.

### Step 4: Start the Frontend React App

```bash
# From project root
cd frontend
npm install
npm run dev
```

The frontend should start on `http://localhost:5173`.

### Step 5: Navigate to Data Imports

1. Open your browser to `http://localhost:5173`
2. Navigate to the Data Imports page
3. Click on the "ACC Sync (APS)" tab

## Using the ACC Sync Feature

### 1. Authenticate

Click the **"Authenticate"** button to open the Autodesk login page in a new window.

- Sign in with your Autodesk account
- Grant permissions when prompted
- Keep the window open until login completes
- The service stores your authentication token

### 2. Load Hubs

After authentication, click **"Load hubs"** to retrieve all hubs you have access to.

You'll see:
- Hub name and region
- Authentication method (user token or app token)
- Hub count

### 3. Select a Hub

Click on any hub in the list to view its projects.

The hub will be highlighted when selected.

### 4. Select a Project

Click on any project to view detailed information.

The project details panel will expand with 4 tabs:

#### **Overview Tab**
- Project status and dates
- Total folders and files
- Model folders with file counts

#### **Files Tab**
- List of all model files (RVT, IFC, DWG, etc.)
- File versions and sizes
- Last modified dates
- Folder locations

#### **Issues Tab**
- Project issues with status
- Priority levels
- Assigned users
- Creation dates
- Custom attributes

#### **Users Tab**
- Team members
- Email addresses
- Roles and permissions
- Company affiliations
- Status (active/inactive)

## Example Workflow

### Scenario: Reviewing Model Files for a BIM Coordination Meeting

1. **Authenticate** with Autodesk
2. **Select Hub**: "ABC Company - North America"
3. **Select Project**: "Downtown Office Tower - MEP Coordination"
4. **Switch to Files Tab**
5. **Review Models**:
   - See latest Revit model: `Arch-Model-v23.rvt` (updated yesterday)
   - Check MEP models: `MEP-HVAC-v12.rvt`, `MEP-Plumbing-v8.rvt`
   - Verify IFC export: `Coordination-Model-v5.ifc`
6. **Switch to Issues Tab**
7. **Review Open Issues**:
   - 15 high-priority clashes
   - 8 medium-priority design queries
   - 3 low-priority RFIs
8. **Switch to Users Tab**
9. **Identify Key Contacts**:
   - Project Manager: john.doe@abc.com
   - MEP Lead: jane.smith@mep-contractor.com
   - Architect: bob.wilson@architects.com

## Common Model File Extensions

The system automatically identifies these as model files:

| Extension | Description |
|-----------|-------------|
| `.rvt` | Revit models |
| `.rfa` | Revit families |
| `.ifc` | IFC models (open BIM standard) |
| `.dwg` | AutoCAD drawings |
| `.dwf` | Design Web Format |
| `.nwd` | Navisworks models |
| `.nwc` | Navisworks cache files |
| `.skp` | SketchUp models |
| `.3dm` | Rhino 3D models |
| `.dgn` | MicroStation files |

## Troubleshooting

### "No hubs returned"

**Causes**:
- Not authenticated yet
- User doesn't have access to any hubs
- Token expired

**Solutions**:
1. Click "Authenticate" again
2. Verify your Autodesk account has access to ACC projects
3. Check browser console for errors

### "Failed to fetch projects"

**Causes**:
- Invalid hub ID
- User doesn't have project access
- Network timeout

**Solutions**:
1. Verify hub ID is correct
2. Check user permissions in Autodesk Construction Cloud
3. Try refreshing the hubs list

### "Issues API returns 404"

**Causes**:
- Issues module not enabled in ACC project
- Project doesn't have any issues
- Insufficient permissions

**Solutions**:
1. Verify Issues module is enabled in ACC project settings
2. Check if user has permission to view issues
3. Try with a different project

### "Users API returns 403"

**Causes**:
- User doesn't have admin rights
- Insufficient permissions to view team members

**Solutions**:
1. Request admin access from project administrator
2. Try with app-level token (automatic fallback)
3. Contact Autodesk support if issue persists

## Authentication Methods

The system supports two authentication methods with automatic fallback:

### **User Token (3-Legged OAuth)** - Recommended
- Full access to user's hubs and projects
- Can access private/restricted projects
- Respects user permissions
- **How to use**: Click "Authenticate" button

### **App Token (2-Legged OAuth)** - Fallback
- Limited to publicly accessible projects
- May not see all hubs
- Automatic fallback when user token fails
- **When used**: System automatically tries this if user token fails

## API Response Times

Typical response times for various operations:

| Operation | Time | Notes |
|-----------|------|-------|
| Authentication | 2-5 seconds | Opens browser window |
| Load hubs | 1-3 seconds | Depends on hub count |
| Load projects | 2-5 seconds | Depends on project count |
| Project details | 3-8 seconds | Includes folder/file stats |
| Load files | 5-15 seconds | Depends on file count |
| Load issues | 2-10 seconds | Depends on issue count |
| Load users | 1-3 seconds | Usually fast |

## Data Limitations

Current limitations (as of this implementation):

- **Files**: First 50 model files displayed (out of potentially thousands)
- **Issues**: First 25 issues displayed per page
- **Users**: All users displayed (typically < 100)
- **Folders**: Top-level folders only (no deep navigation yet)
- **Persistence**: Data not saved to database yet (in-session only)

## Next Steps

To take this further:

1. **Database Integration**: Save synced data to SQL Server tables
2. **Project Mapping**: Link ACC projects to internal projects
3. **Scheduled Sync**: Automatically sync data daily/weekly
4. **Issue Tracking**: Import ACC issues into internal system
5. **User Mapping**: Match ACC users to internal users
6. **Model Versioning**: Track model changes over time
7. **Clash Detection**: Compare models for conflicts
8. **Reporting**: Generate reports from ACC data

Refer to the [ACC Sync Implementation Guide](./ACC_SYNC_IMPLEMENTATION_GUIDE.md) for detailed implementation instructions for these features.

## Security Notes

⚠️ **Important**: 
- Tokens are stored server-side in the aps-auth-demo service
- Tokens expire after 1 hour (automatically refreshed)
- Always use HTTPS in production
- Never commit credentials to version control
- Limit scope to only required permissions

## Support Resources

- [Autodesk Platform Services Documentation](https://aps.autodesk.com/en/docs/)
- [ACC API Reference](https://aps.autodesk.com/en/docs/acc/v1/overview/)
- [APS Community Forums](https://forums.autodesk.com/t5/platform-services/ct-p/aec-platform-services)
- [GitHub Issues](https://github.com/RStrinati/BIMProjMgmt/issues) (for this project)

## FAQ

**Q: Can I use this without an Autodesk account?**  
A: No, you need a valid Autodesk account with access to ACC projects.

**Q: Does this work with BIM 360?**  
A: Yes, BIM 360 Team and Docs use the same API, so it should work.

**Q: Can I download models?**  
A: Not yet. Currently view-only. Model download requires additional permissions and implementation.

**Q: Does this replace the existing ACC import feature?**  
A: No, this complements it. The existing feature imports issues from ZIP files. This one provides real-time API access.

**Q: How often should I sync?**  
A: Depends on your needs. Daily sync is typical for active projects. Weekly for monitoring only.

**Q: Can I sync multiple projects at once?**  
A: Not yet. Currently one project at a time. Batch sync coming in future updates.

## Feedback

Found a bug or have a suggestion? Please:
1. Check existing issues on GitHub
2. Create a new issue with details
3. Tag it with `acc-sync` label
4. Include error messages and screenshots

---

**Last Updated**: January 7, 2026  
**Version**: 1.0.0  
**Author**: GitHub Copilot with Claude Sonnet 4.5
