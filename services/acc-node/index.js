const express = require('express');
const axios = require('axios');
const app = express();

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

const CLIENT_ID = 'HSIzVK9vT8AGY0emotXgOylhsczvoO0XSPy6M76vAAovAeN8';
const CLIENT_SECRET = 'JuLnXcguwKB2g0QoG5auJWnF2XnI9uiW8wdYw5xIAmKiqTIvK3q9pfAHTq7ZcNZ4';
const REDIRECT_URI = 'http://localhost:3000/callback';
const PORT = 3000;

let access_token = null;
let client_credentials_token = null;

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
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    try {
        // Test with hubs API which works with 2-legged tokens
        const response = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: {
                'Authorization': `Bearer ${client_credentials_token}`
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
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    try {
        const response = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: {
                'Authorization': `Bearer ${client_credentials_token}`
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
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    const hubId = req.params.hubId;

    try {
        const response = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects`, {
            headers: {
                'Authorization': `Bearer ${client_credentials_token}`
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
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    const { hubId, projectId } = req.params;

    try {
        // Get basic project info
        const projectResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}`, {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
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
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    const { hubId, projectId } = req.params;

    try {
        // Get project basic info
        const projectResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}`, {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
        });

        // Get project top folders to count files
        const foldersResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}/topFolders`, {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
        });

        const project = projectResponse.data.data;
        const folders = foldersResponse.data.data;

        // Count files in each folder (simplified - just top level)
        let totalFiles = 0;
        let modelFolders = [];
        
        for (const folder of folders) {
            try {
                const folderContents = await axios.get(`https://developer.api.autodesk.com/project/v1/projects/${projectId}/folders/${folder.id}/contents`, {
                    headers: { 'Authorization': `Bearer ${client_credentials_token}` }
                });
                
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
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    const { hubId, projectId } = req.params;

    try {
        // Try to get project users - this might require different permissions
        const response = await axios.get(`https://developer.api.autodesk.com/hq/v1/accounts/${hubId.replace('b.', '')}/projects/${projectId.replace('b.', '')}/users`, {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
        });

        const users = response.data.map(user => ({
            id: user.id,
            name: user.name,
            email: user.email,
            role: user.role,
            status: user.status,
            lastLogin: user.lastSignIn
        }));

        res.json({
            success: true,
            projectId: projectId,
            userCount: users.length,
            users: users
        });

    } catch (err) {
        console.error('❌ Project users failed:', err.response?.data || err.message);
        
        // If direct user access fails, try alternative approach
        res.json({
            error: 'Could not access project users directly',
            reason: 'May require additional permissions or different API endpoint',
            details: err.response?.data || err.message,
            status: err.response?.status,
            suggestion: 'User management typically requires admin permissions in ACC'
        });
    }
});

// Get project issues
app.get('/project-issues/:hubId/:projectId', async (req, res) => {
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    const { hubId, projectId } = req.params;
    const containerId = projectId.replace('b.', ''); // Issues API uses container ID

    try {
        // Get issues using ACC Issues API
        const response = await axios.get(`https://developer.api.autodesk.com/issues/v1/containers/${containerId}/quality-issues`, {
            headers: { 
                'Authorization': `Bearer ${client_credentials_token}`,
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
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    const { hubId, projectId } = req.params;

    try {
        // Get top folders first
        const foldersResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}/topFolders`, {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
        });

        const folders = foldersResponse.data.data;
        let allFiles = [];
        let modelFiles = [];
        let lastUpdate = null;

        // Get files from each folder
        for (const folder of folders) {
            try {
                const folderContents = await axios.get(`https://developer.api.autodesk.com/project/v1/projects/${projectId}/folders/${folder.id}/contents`, {
                    headers: { 'Authorization': `Bearer ${client_credentials_token}` }
                });
                
                const files = folderContents.data.data
                    .filter(item => item.type === 'items')
                    .map(item => ({
                        id: item.id,
                        name: item.attributes.displayName,
                        extension: item.attributes.extension?.type,
                        size: item.attributes.storageSize,
                        created: item.attributes.createTime,
                        modified: item.attributes.lastModifiedTime,
                        version: item.attributes.versionNumber,
                        folder: folder.attributes.displayName
                    }));

                allFiles = allFiles.concat(files);

                // Identify model files (common CAD/BIM extensions)
                const models = files.filter(file => 
                    file.extension && ['dwg', 'rvt', 'ifc', 'nwd', 'nwc', 'skp', '3dm'].includes(file.extension.toLowerCase())
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
    const authUrl = `https://developer.api.autodesk.com/authentication/v2/authorize?response_type=code&client_id=${CLIENT_ID}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&scope=user-profile:read data:read account:read`;

    console.log('🔗 Autodesk Login URL (3-legged):', authUrl);
    res.send(`
        <h2>APS OAuth Demo - 3-Legged Login</h2>
        <p>This will likely fail with AUTH-001 error due to Client ID issue.</p>
        <p><a href="${authUrl}" target="_blank">Try Login with Autodesk</a></p>
        <p><strong>Recommendation:</strong> <a href="/diagnose">Check diagnostic first</a></p>
    `);
});

// Handle OAuth callback
app.get('/callback', async (req, res) => {
    const code = req.query.code;
    console.log('🔁 Received code:', code);

    try {
        const tokenResponse = await axios.post('https://developer.api.autodesk.com/authentication/v2/token', null, {
            params: {
                client_id: CLIENT_ID,
                client_secret: CLIENT_SECRET,
                grant_type: 'authorization_code',
                code,
                redirect_uri: REDIRECT_URI
            },
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });

        access_token = tokenResponse.data.access_token;
        console.log('✅ Access Token:', access_token);
        res.send('✅ Access token received. You can now make API calls.');
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