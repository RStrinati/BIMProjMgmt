require('dotenv').config();
const express = require('express');
const axios = require('axios');
const session = require('express-session');
const app = express();

app.use(express.json());
app.use(session({
    secret: process.env.SESSION_SECRET || 'dev-secret-change-me',
    resave: false,
    saveUninitialized: false
}));

// Root route for instructions
app.get('/', (req, res) => {
    res.send(`
        <h2>APS OAuth Demo</h2>
        <p>Welcome! Use the following endpoints:</p>
        <ul>
            <li><a href="/login-2legged">/login-2legged</a> - ✅ Get app token (2-legged OAuth - WORKING!)</li>
            <li><a href="/test-token">/test-token</a> - 🧪 Test if your token works (fixed for 2-legged)</li>
            <li><a href="/hubs">/hubs</a> - 🏢 Get your ACC hubs</li>
            <li>/projects/{hubId} - 📁 Get projects in a specific hub</li>
            <li>/project-nav/{hubId}/{projectId} - 🧭 Complete navigation dashboard</li>
            <li>/project-details/{hubId}/{projectId} - 📊 Comprehensive project analysis</li>
            <li>/project-users/{hubId}/{projectId} - 👥 Project team members</li>
            <li>/project-issues/{hubId}/{projectId} - 🐛 Project issues</li>
            <li>/project-files/{hubId}/{projectId} - 📄 Project files and models</li>
            <li><a href="/login">/login</a> - Start user authentication (3-legged OAuth)</li>
            <li><a href="/diagnose">/diagnose</a> - 🚨 Diagnostic information</li>
        </ul>
        <p><strong>✅ Full ACC Integration Ready! Start: /login-2legged → /hubs → /projects/{hubId} → /project-nav/{hubId}/{projectId}</strong></p>
    `);
});

const CLIENT_ID = process.env.APS_CLIENT_ID;
const CLIENT_SECRET = process.env.APS_CLIENT_SECRET;
const REDIRECT_URI = process.env.APS_REDIRECT_URI || 'http://localhost:3000/callback';
const AECDM_REGION = process.env.AECDM_REGION || 'AUS';
const PORT = 3000;

let client_credentials_token = null;

function getUserToken(req) {
    return req.session?.aps3l?.access_token || null;
}

function getAppToken() {
    return client_credentials_token || null;
}

function getPreferredToken(req) {
    return getUserToken(req) || getAppToken();
}

function require3Legged(req, res, next) {
    if (!getUserToken(req)) {
        return res.status(401).json({ error: 'Login required (/login)' });
    }
    next();
}

function getFileExtension(item) {
    const extType = item?.attributes?.extension?.type;
    if (extType) {
        const norm = String(extType).toLowerCase();
        if (norm.includes('c4rmodel')) return 'rvt';
        if (norm.includes('ifc')) return 'ifc';
        if (norm.includes('dwg')) return 'dwg';
        if (norm.includes('nwd')) return 'nwd';
        if (norm.includes('nwc')) return 'nwc';
        if (norm.includes('skp')) return 'skp';
        if (norm.includes('rfa')) return 'rfa';
        if (norm.includes('rte')) return 'rte';
        if (norm.includes('nwf')) return 'nwf';
        if (norm.includes('file')) {
            const src = item?.attributes?.extension?.data?.sourceFileName;
            if (src && src.includes('.')) {
                const i = src.lastIndexOf('.');
                return src.slice(i + 1).toLowerCase();
            }
        }
    }
    const name = item?.attributes?.displayName || '';
    const idx = name.lastIndexOf('.');
    if (idx === -1) return null;
    return name.slice(idx + 1).toLowerCase();
}

async function dmGet(url, token) {
    return axios.get(url, { headers: { Authorization: `Bearer ${token}` } });
}

async function dmGetFolderContents(projectId, folderId, token) {
    const encodedId = encodeURIComponent(folderId);
    const headers = { Authorization: `Bearer ${token}` };
    try {
        return await axios.get(`https://developer.api.autodesk.com/data/v1/projects/${projectId}/folders/${encodedId}/contents`, { headers });
    } catch (err) {
        if (err.response?.status === 404) {
            return await axios.get(`https://developer.api.autodesk.com/data/v1/projects/${projectId}/items/${encodedId}/children`, { headers });
        }
        throw err;
    }
}

async function getProjectUsers(projectId, token, region) {
    const cleanProjectId = projectId.startsWith('b.') ? projectId.slice(2) : projectId;
    const headers = { Authorization: `Bearer ${token}` };
    if (region) {
        const regionValue = region.toUpperCase();
        headers['x-ads-region'] = regionValue;
        headers['Region'] = regionValue;
    }
    const urls = [
        `https://developer.api.autodesk.com/construction/admin/v1/projects/${cleanProjectId}/users`,
        `https://developer.api.autodesk.com/bim360/admin/v1/projects/${cleanProjectId}/users`
    ];

    let lastErr = null;
    for (const url of urls) {
        try {
            return await axios.get(url, { headers });
        } catch (err) {
            if (err.response?.status === 404) {
                lastErr = err;
                continue;
            }
            throw err;
        }
    }
    throw lastErr || new Error('Project users endpoint not found');
}

function normalizeUser(user) {
    const first = user.first_name || user.firstname || '';
    const last = user.last_name || user.lastname || '';
    const name = user.name || `${first} ${last}`.trim() || user.email || 'N/A';
    const role =
        user.role ||
        user.role_name ||
        user.access_level ||
        user.job_title ||
        user.roles?.[0]?.name ||
        user.roles?.[0]?.role ||
        'N/A';
    const company =
        user.company_name ||
        user.company?.name ||
        user.company?.company_name ||
        user.company?.title ||
        user.companyName ||
        user.company ||
        user.account_name ||
        user.organization ||
        user.org_name ||
        'N/A';
    const accessLevelRaw =
        user.access_level ||
        user.accessLevel ||
        user.project_access ||
        user.project_role ||
        user.projectRole ||
        user.accessLevels ||
        null;
    const productsRaw =
        user.services ||
        user.products ||
        user.modules ||
        user.product_access ||
        user.permissions?.products ||
        [];
    const permissionsRaw =
        user.permissions ||
        user.role_permissions ||
        user.project_permissions ||
        user.service_permissions ||
        [];
    const accessLevel = formatAccessLevel(accessLevelRaw);
    const products = formatProducts(productsRaw);
    const permissions = formatPermissions(permissionsRaw);
    return {
        id: user.id || user.user_id || user.autodesk_id,
        name,
        email: user.email || 'N/A',
        role,
        status: user.status || 'active',
        lastLogin: user.lastSignIn,
        company,
        accessLevel,
        products,
        permissions
    };
}

function formatAccessLevel(raw) {
    if (!raw) return 'N/A';
    if (typeof raw === 'string') return raw;
    if (typeof raw === 'object') {
        const flags = [];
        if (raw.accountAdmin) flags.push('Account Admin');
        if (raw.projectAdmin) flags.push('Project Admin');
        if (raw.executive) flags.push('Executive');
        if (raw.accountStandardsAdministrator) flags.push('Account Standards Admin');
        return flags.length > 0 ? flags.join(', ') : 'Member';
    }
    return 'N/A';
}

function formatProducts(raw) {
    if (!raw || (Array.isArray(raw) && raw.length === 0)) return 'None';
    if (typeof raw === 'string') return raw;
    if (Array.isArray(raw)) {
        const enabled = raw
            .filter(p => p && (p.access === 'member' || p.access === 'admin' || p.access === true))
            .map(p => p.key || p.name || p.product || p.service)
            .filter(Boolean);
        return enabled.length > 0 ? enabled.join(', ') : 'None';
    }
    return 'None';
}

function formatPermissions(raw) {
    if (!raw || (Array.isArray(raw) && raw.length === 0)) return 'None';
    if (typeof raw === 'string') return raw;
    if (Array.isArray(raw)) return raw.map(String).join(', ');
    if (typeof raw === 'object') {
        return Object.entries(raw)
            .filter(([, v]) => !!v)
            .map(([k]) => k)
            .join(', ') || 'None';
    }
    return 'None';
}

async function getDerivativesUrn(projectId, versionId, token) {
    const v = await dmGet(`https://developer.api.autodesk.com/data/v1/projects/${projectId}/versions/${versionId}`, token);
    const rel = v.data?.data?.relationships?.derivatives?.data?.id;
    if (rel) return rel.startsWith('urn:') ? rel : `urn:${rel}`;

    const refs = await dmGet(`https://developer.api.autodesk.com/data/v1/projects/${projectId}/versions/${versionId}/relationships/refs`, token);
    const included = refs.data?.included || [];
    const deriv = included.find(x => x?.type === 'derivatives');
    const id = deriv?.id;
    if (!id) throw new Error('No derivatives URN found for version');
    return id.startsWith('urn:') ? id : `urn:${id}`;
}

// Comprehensive diagnostic endpoint
app.get('/diagnose', (req, res) => {
    res.json({
        problem: "AUTH-001: The client_id specified does not have access to the api product",
        currentClientId: CLIENT_ID,
        explanation: "This error means the Client ID does not exist in your Autodesk Developer Console account",
        causes: [
            "1. App doesn't exist in your account",
            "2. This app belongs to a different Autodesk account", 
            "3. App is inactive/suspended",
            "4. Wrong callback URL configured"
        ],
        solutions: [
            "Option 1: Check https://aps.autodesk.com/myapps/ for this Client ID",
            "Option 2: Create a new app with YOUR Autodesk account (RECOMMENDED)",
            "Option 3: Get access to existing app if it belongs to your organization"
        ],
        createNewApp: {
            url: "https://aps.autodesk.com/myapps/",
            steps: [
                "1. Click 'Create App'",
                "2. Choose 'Web App'",
                "3. Set callback URL: http://localhost:3000/callback",
                "4. Enable: Data Management API, Construction Cloud API, User Profile API",
                "5. Copy new Client ID and Secret",
                "6. Replace CLIENT_ID and CLIENT_SECRET in index.js"
            ]
        },
        criticalAction: "You MUST create a new app or get access to the existing one. Current credentials will NOT work."
    });
});

// 2-Legged OAuth (Client Credentials) - for app-only access
app.get('/login-2legged', async (req, res) => {
    try {
        console.log('🔑 Attempting 2-legged OAuth (Client Credentials)...');
        
        const response = await axios.post('https://developer.api.autodesk.com/authentication/v2/token',
            'grant_type=client_credentials&scope=data:read account:read', {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `Basic ${Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64')}`
            }
        });

        client_credentials_token = response.data.access_token;
        console.log('✅ 2-Legged Token received:', client_credentials_token.substring(0, 20) + '...');
        
        res.json({
            success: true,
            message: '✅ 2-legged OAuth successful! App can now access Autodesk APIs.',
            tokenInfo: {
                token_type: response.data.token_type,
                expires_in: response.data.expires_in,
                scope: response.data.scope
            }
        });
        
    } catch (err) {
        console.error('❌ 2-Legged OAuth Error:', err.response?.data || err.message);
        
        res.status(500).json({
            error: 'Failed to get 2-legged token',
            details: err.response?.data || err.message,
            status: err.response?.status,
            explanation: 'Same AUTH-001 error - the Client ID does not exist or is not accessible'
        });
    }
});

// Test endpoint to verify token works
app.get('/test-token', async (req, res) => {
    if (!getAppToken()) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    try {
        // Test with hubs API which works with 2-legged tokens
        const token = getAppToken();
        const response = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        res.json({
            success: true,
            message: '✅ 2-legged token is working perfectly!',
            tokenInfo: {
                tokenType: '2-legged (app-only)',
                access: 'Can access ACC hubs, projects, and data',
                cannotAccess: 'User profile (requires 3-legged token)'
            },
            hubsFound: response.data.data.length,
            firstHub: response.data.data[0] || 'No hubs available'
        });
        
    } catch (err) {
        console.error('❌ Token test failed:', err.response?.data || err.message);
        res.status(500).json({
            error: 'Token test failed',
            details: err.response?.data || err.message,
            status: err.response?.status
        });
    }
});

// Get user's hubs (ACC hubs)
app.get('/hubs', async (req, res) => {
    const token = getPreferredToken(req);
    if (!token) {
        return res.json({
            error: 'No token available',
            action: 'Visit /login-2legged or /login first'
        });
    }

    try {
        const response = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const hubs = response.data.data.map(hub => ({
            id: hub.id,
            name: hub.attributes.name,
            region: hub.attributes.region,
            projectsLink: `http://localhost:3000/projects/${hub.id}`,
            // Quick navigation helpers
            quickActions: {
                viewProjects: `http://localhost:3000/projects/${hub.id}`,
                hubInfo: {
                    id: hub.id,
                    displayName: hub.attributes.name,
                    region: hub.attributes.region
                }
            }
        }));

        res.json({
            success: true,
            hubCount: hubs.length,
            hubs: hubs,
            nextStep: 'Click on a projectsLink to see projects in that hub'
        });
        
    } catch (err) {
        console.error('❌ Hubs request failed:', err.response?.data || err.message);
        res.status(500).json({
            error: 'Failed to get hubs',
            details: err.response?.data || err.message,
            status: err.response?.status
        });
    }
});

// Get projects in a specific hub
app.get('/projects/:hubId', async (req, res) => {
    const token = getPreferredToken(req);
    if (!token) {
        return res.json({
            error: 'No token available',
            action: 'Visit /login-2legged or /login first'
        });
    }

    const hubId = req.params.hubId;

    try {
        const response = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const projects = response.data.data.map(project => ({
            id: project.id,
            name: project.attributes.name,
            status: project.attributes.status,
            created: project.attributes.createdAt,
            updated: project.attributes.updatedAt,
            // Direct action links
            detailsLink: `http://localhost:3000/project-details/${hubId}/${project.id}`,
            usersLink: `http://localhost:3000/project-users/${hubId}/${project.id}`,
            issuesLink: `http://localhost:3000/project-issues/${hubId}/${project.id}`,
            filesLink: `http://localhost:3000/project-files/${hubId}/${project.id}`,
            navDashboard: `http://localhost:3000/project-nav/${hubId}/${project.id}`,
            // Complete navigation structure
            navigation: {
                hubId: hubId,
                projectId: project.id,
                projectName: project.attributes.name,
                allEndpoints: {
                    overview: `http://localhost:3000/project-details/${hubId}/${project.id}`,
                    team: `http://localhost:3000/project-users/${hubId}/${project.id}`,
                    issues: `http://localhost:3000/project-issues/${hubId}/${project.id}`,
                    files: `http://localhost:3000/project-files/${hubId}/${project.id}`
                }
            }
        }));

        res.json({
            success: true,
            hubId: hubId,
            projectCount: projects.length,
            projects: projects,
            nextSteps: [
                'Click navDashboard for complete project navigation hub',
                'Click detailsLink for comprehensive project info',
                'Click usersLink for project team members',
                'Click issuesLink for project issues',
                'Click filesLink for project files and models'
            ]
        });
        
    } catch (err) {
        console.error('❌ Projects request failed:', err.response?.data || err.message);
        res.status(500).json({
            error: 'Failed to get projects',
            details: err.response?.data || err.message,
            status: err.response?.status
        });
    }
});

// Project navigation dashboard - provides all links and IDs in one place
app.get('/project-nav/:hubId/:projectId', async (req, res) => {
    const token = getPreferredToken(req);
    if (!token) {
        return res.json({
            error: 'No token available',
            action: 'Visit /login-2legged or /login first'
        });
    }

    const { hubId, projectId } = req.params;

    try {
        // Get basic project info
        const projectResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const project = projectResponse.data.data;

        res.json({
            success: true,
            projectInfo: {
                hubId: hubId,
                projectId: projectId,
                name: project.attributes.name,
                status: project.attributes.status,
                created: project.attributes.createdAt,
                updated: project.attributes.updatedAt
            },
            quickLinks: {
                overview: `http://localhost:3000/project-details/${hubId}/${projectId}`,
                team: `http://localhost:3000/project-users/${hubId}/${projectId}`,
                issues: `http://localhost:3000/project-issues/${hubId}/${projectId}`,
                files: `http://localhost:3000/project-files/${hubId}/${projectId}`,
                navigation: `http://localhost:3000/project-nav/${hubId}/${projectId}`
            },
            copyPasteUrls: {
                curlExamples: {
                    getDetails: `curl "http://localhost:3000/project-details/${hubId}/${projectId}"`,
                    getIssues: `curl "http://localhost:3000/project-issues/${hubId}/${projectId}"`,
                    getFiles: `curl "http://localhost:3000/project-files/${hubId}/${projectId}"`
                }
            },
            identifiers: {
                hubIdOnly: hubId,
                projectIdOnly: projectId,
                containerIdForIssues: projectId.replace('b.', ''),
                accountIdForUsers: hubId.replace('b.', '')
            }
        });

    } catch (err) {
        console.error('❌ Project navigation failed:', err.response?.data || err.message);
        res.status(500).json({
            error: 'Failed to get project navigation info',
            details: err.response?.data || err.message,
            status: err.response?.status,
            providedIds: { hubId, projectId }
        });
    }
});

// Get comprehensive project details
app.get('/project-details/:hubId/:projectId', async (req, res) => {
    const token = getPreferredToken(req);
    if (!token) {
        return res.json({
            error: 'No token available',
            action: 'Visit /login-2legged or /login first'
        });
    }

    const { hubId, projectId } = req.params;

    try {
        // Get project basic info
        const projectResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        // Get project top folders to count files
        const foldersResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}/topFolders`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const project = projectResponse.data.data;
        const folders = foldersResponse.data.data;

        // Count files in each folder (simplified - just top level)
        let totalFiles = 0;
        let modelFolders = [];
        
        for (const folder of folders) {
            try {
                const folderContents = await dmGetFolderContents(projectId, folder.id, token);
                
                const files = folderContents.data.data.filter(item => item.type === 'items');
                totalFiles += files.length;
                
                if (folder.attributes.displayName === 'Project Files' || folder.attributes.displayName === 'Plans') {
                    modelFolders.push({
                        name: folder.attributes.displayName,
                        fileCount: files.length,
                        lastModified: folder.attributes.lastModifiedTime
                    });
                }
            } catch (err) {
                console.log(`Could not access folder ${folder.attributes.displayName}:`, err.response?.status);
            }
        }

        res.json({
            success: true,
            projectInfo: {
                id: project.id,
                name: project.attributes.name,
                status: project.attributes.status,
                created: project.attributes.createdAt,
                updated: project.attributes.updatedAt,
                totalTopLevelFolders: folders.length,
                totalFiles: totalFiles,
                modelFolders: modelFolders
            },
            folders: folders.map(f => ({
                id: f.id,
                name: f.attributes.displayName,
                created: f.attributes.createTime,
                modified: f.attributes.lastModifiedTime
            })),
            actions: {
                users: `http://localhost:3000/project-users/${hubId}/${projectId}`,
                issues: `http://localhost:3000/project-issues/${hubId}/${projectId}`,
                allFiles: `http://localhost:3000/project-files/${hubId}/${projectId}`
            }
        });

    } catch (err) {
        console.error('❌ Project details failed:', err.response?.data || err.message);
        res.status(500).json({
            error: 'Failed to get project details',
            details: err.response?.data || err.message,
            status: err.response?.status
        });
    }
});

// Get project users/team members
app.get('/project-users/:hubId/:projectId', async (req, res) => {
    const token = getPreferredToken(req);
    if (!token) {
        return res.json({
            error: 'No token available',
            action: 'Visit /login-2legged or /login first'
        });
    }

    const { hubId, projectId } = req.params;
    const region = req.query.region || req.headers['x-ads-region'] || req.headers['region'];

    try {
        const response = await getProjectUsers(projectId, token, region);
        const users = (response.data?.results || response.data?.data || response.data || []).map(normalizeUser);

        res.json({
            success: true,
            projectId: projectId,
            userCount: users.length,
            region: region || 'default',
            users: users
        });

    } catch (err) {
        console.error('❌ Project users failed:', err.response?.data || err.message);
        
        // If direct user access fails, try alternative approach
        res.json({
            error: 'Could not access project users directly',
            reason: 'May require additional permissions or Account Admin API access',
            details: err.response?.data || err.message,
            status: err.response?.status,
            suggestion: 'Account Admin API requires project admin permissions and custom integration access'
        });
    }
});

// Get project issues
app.get('/project-issues/:hubId/:projectId', async (req, res) => {
    const token = getPreferredToken(req);
    if (!token) {
        return res.json({
            error: 'No token available',
            action: 'Visit /login-2legged or /login first'
        });
    }

    const { hubId, projectId } = req.params;
    const containerId = projectId.replace('b.', ''); // Issues API uses container ID

    try {
        // Get issues using ACC Issues API
        const response = await axios.get(`https://developer.api.autodesk.com/issues/v1/containers/${containerId}/quality-issues`, {
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/vnd.api+json'
            },
            params: {
                'page[limit]': 50  // Limit for initial load
            }
        });

        const issues = response.data.data.map(issue => ({
            id: issue.id,
            title: issue.attributes.title,
            status: issue.attributes.status,
            priority: issue.attributes.priority,
            issueType: issue.attributes.issueType,
            created: issue.attributes.createdAt,
            updated: issue.attributes.updatedAt,
            assignedTo: issue.attributes.assignedTo,
            createdBy: issue.attributes.createdBy,
            description: issue.attributes.description?.substring(0, 200) + '...' // Truncate for overview
        }));

        // Group issues by status
        const statusCounts = issues.reduce((acc, issue) => {
            acc[issue.status] = (acc[issue.status] || 0) + 1;
            return acc;
        }, {});

        res.json({
            success: true,
            projectId: projectId,
            totalIssues: issues.length,
            statusBreakdown: statusCounts,
            recentIssues: issues.slice(0, 10), // Show 10 most recent
            allIssues: issues,
            pagination: response.data.meta || 'No pagination info'
        });

    } catch (err) {
        console.error('❌ Project issues failed:', err.response?.data || err.message);
        res.status(500).json({
            error: 'Failed to get project issues',
            details: err.response?.data || err.message,
            status: err.response?.status,
            note: 'Issues API may require specific permissions or activated Construction Cloud API'
        });
    }
});

// Get project files and models
app.get('/project-files/:hubId/:projectId', async (req, res) => {
    const token = getPreferredToken(req);
    if (!token) {
        return res.json({
            error: 'No token available',
            action: 'Visit /login-2legged or /login first'
        });
    }

    const { hubId, projectId } = req.params;

    try {
        // Get top folders first
        const foldersResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}/topFolders`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const folders = foldersResponse.data.data;
        let allFiles = [];
        let modelFiles = [];
        let lastUpdate = null;

        // Get files from each folder
        for (const folder of folders) {
            try {
                const folderContents = await dmGetFolderContents(projectId, folder.id, token);
                
                const files = folderContents.data.data
                    .filter(item => item.type === 'items')
                    .map(item => {
                        const extension = getFileExtension(item);
                        return {
                            id: item.id,
                            name: item.attributes.displayName,
                            extension: extension,
                            size: item.attributes.storageSize,
                            created: item.attributes.createTime,
                            modified: item.attributes.lastModifiedTime,
                            version: item.attributes.versionNumber,
                            folder: folder.attributes.displayName
                        };
                    });

                allFiles = allFiles.concat(files);

                // Identify model files (common CAD/BIM extensions)
                const models = files.filter(file => 
                    file.extension && ['dwg', 'rvt', 'ifc', 'nwd', 'nwc', 'skp', '3dm', 'rfa', 'rte'].includes(file.extension)
                );
                modelFiles = modelFiles.concat(models);

                // Track latest update
                files.forEach(file => {
                    if (!lastUpdate || new Date(file.modified) > new Date(lastUpdate)) {
                        lastUpdate = file.modified;
                    }
                });

            } catch (err) {
                console.log(`Could not access folder ${folder.attributes.displayName}:`, err.response?.status);
            }
        }

        // File type breakdown
        const fileTypes = allFiles.reduce((acc, file) => {
            const ext = file.extension || 'unknown';
            acc[ext] = (acc[ext] || 0) + 1;
            return acc;
        }, {});

        res.json({
            success: true,
            projectId: projectId,
            summary: {
                totalFiles: allFiles.length,
                totalModels: modelFiles.length,
                totalFolders: folders.length,
                lastFileUpdate: lastUpdate,
                fileTypes: fileTypes
            },
            modelFiles: modelFiles,
            recentFiles: allFiles
                .sort((a, b) => new Date(b.modified) - new Date(a.modified))
                .slice(0, 20), // 20 most recently modified
            folderStructure: folders.map(f => ({
                name: f.attributes.displayName,
                fileCount: allFiles.filter(file => file.folder === f.attributes.displayName).length
            }))
        });

    } catch (err) {
        console.error('❌ Project files failed:', err.response?.data || err.message);
        res.status(500).json({
            error: 'Failed to get project files',
            details: err.response?.data || err.message,
            status: err.response?.status
        });
    }
});

// 3-Legged OAuth login
app.get('/login', async (req, res) => {
    const scope = encodeURIComponent('data:read viewables:read user-profile:read');
    const authUrl =
        `https://developer.api.autodesk.com/authentication/v2/authorize` +
        `?response_type=code&client_id=${CLIENT_ID}` +
        `&redirect_uri=${encodeURIComponent(REDIRECT_URI)}` +
        `&scope=${scope}`;

    console.log('🔗 Autodesk Login URL (3-legged):', authUrl);
    res.redirect(authUrl);
});

// Handle OAuth callback
app.get('/callback', async (req, res) => {
    const code = req.query.code;
    console.log('🔁 Received code:', code);

    try {
        const tokenResponse = await axios.post(
            'https://developer.api.autodesk.com/authentication/v2/token',
            new URLSearchParams({
                client_id: CLIENT_ID,
                client_secret: CLIENT_SECRET,
                grant_type: 'authorization_code',
                code,
                redirect_uri: REDIRECT_URI
            }).toString(),
            { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
        );

        req.session.aps3l = {
            access_token: tokenResponse.data.access_token,
            refresh_token: tokenResponse.data.refresh_token,
            expires_in: tokenResponse.data.expires_in,
            scope: tokenResponse.data.scope,
            obtained_at: Date.now()
        };

        res.send('3-legged token stored. You can now use /viewer and /api/aecdm/graphql.');
    } catch (err) {
        console.error('❌ Token Error:', err.response?.data || err.message);
        res.status(500).json({
            error: 'Failed to retrieve token',
            details: err.response?.data || err.message,
            status: err.response?.status,
            recommendation: 'Check /diagnose for solution'
        });
    }
});

app.get('/api/viewer/token', require3Legged, (req, res) => {
    const t = req.session.aps3l;
    res.json({ access_token: t.access_token, expires_in: t.expires_in });
});

app.get('/api/viewer/urn', require3Legged, async (req, res) => {
    const { projectId, itemId } = req.query;
    const token = getUserToken(req);

    try {
        const item = await dmGet(`https://developer.api.autodesk.com/data/v1/projects/${projectId}/items/${itemId}`, token);
        const tipVersionId = item.data?.data?.relationships?.tip?.data?.id;
        if (!tipVersionId) {
            return res.status(400).json({ error: 'Could not determine tip version for item' });
        }

        const urn = await getDerivativesUrn(projectId, tipVersionId, token);
        res.json({ urn, versionId: tipVersionId });
    } catch (err) {
        res.status(err.response?.status || 500).json({
            error: 'Failed to resolve viewer URN',
            details: err.response?.data || err.message
        });
    }
});

app.post('/api/aecdm/graphql', require3Legged, async (req, res) => {
    const token = getUserToken(req);
    try {
        const r = await axios.post(
            'https://developer.api.autodesk.com/aec/graphql',
            req.body,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    'x-ads-region': AECDM_REGION
                }
            }
        );
        res.json(r.data);
    } catch (err) {
        res.status(err.response?.status || 500).json({
            error: 'AECDM GraphQL request failed',
            details: err.response?.data || err.message,
            regionUsed: AECDM_REGION
        });
    }
});

app.listen(PORT, () => {
    console.log(`🔑 APS OAuth app running at http://localhost:${PORT}`);
    console.log(`✅ 2-legged OAuth is working! Try these endpoints:`);
    console.log(`   📋 /test-token - Verify your token works`);
    console.log(`   🏢 /hubs - Get your ACC hubs`);
    console.log(`   📁 /projects/{hubId} - Get projects with detailed links`);
    console.log(`   🧭 /project-nav/{hubId}/{projectId} - Complete navigation dashboard`);
    console.log(`   📊 /project-details/{hubId}/{projectId} - Full project analysis`);
    console.log(`   👥 /project-users/{hubId}/{projectId} - Project team`);
    console.log(`   🐛 /project-issues/{hubId}/{projectId} - Project issues`);
    console.log(`   📄 /project-files/{hubId}/{projectId} - Files and models`);
});
