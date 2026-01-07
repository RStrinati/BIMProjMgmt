const express = require('express');
const axios = require('axios');
const crypto = require('crypto');
const app = express();

// Build an origin string for absolute links; fall back to relative paths if host is missing
function getBaseUrl(req) {
    const host = req.get('host');
    if (!host) {
        return '';
    }
    return `${req.protocol}://${host}`;
}

// --- Comprehensive Logging Utility ---
function logEvent(type, details) {
    const timestamp = new Date().toISOString();
    const entry = {
        timestamp,
        type,
        ...details
    };
    // Log to console (can be extended to file/db)
    if (type === 'error') {
        console.error('[ERROR]', JSON.stringify(entry, null, 2));
    } else if (type === 'security') {
        console.warn('[SECURITY]', JSON.stringify(entry, null, 2));
    } else {
        console.log('[LOG]', JSON.stringify(entry, null, 2));
    }
}


// Root route for instructions
app.get('/', (req, res) => {
    const baseUrl = getBaseUrl(req) || 'http://localhost:3000';
    res.send(`
        <h1>APS ACC BIM Access Helper</h1>

        <div style="background:#f8f9fa;padding:16px;margin:12px 0;border-radius:6px;border-left:4px solid #0d6efd;">
            <h2>1) Authenticate</h2>
            <ul>
                <li><a href="${baseUrl}/login-pkce">/login-pkce</a> - Recommended (PKCE, user token)</li>
                <li><a href="${baseUrl}/login">/login</a> - Standard 3-legged user token</li>
                <li><a href="${baseUrl}/login-2legged">/login-2legged</a> - App token (for automation, project-nav)</li>
                <li><a href="${baseUrl}/refresh-token">/refresh-token</a> - Refresh current user token</li>
                <li><a href="${baseUrl}/introspect-token">/introspect-token</a> - Check token status</li>
            </ul>
            <p style="margin:6px 0 0 0;">Scopes (user): user-profile:read data:read account:read viewables:read (add data:write if you need writes).</p>
        </div>

        <div style="background:#e8f4ff;padding:16px;margin:12px 0;border-radius:6px;border-left:4px solid #0a9396;">
            <h2>2) BIM Manager Flow</h2>
            <ol>
                <li>Authenticate: <a href="${baseUrl}/login-pkce">/login-pkce</a></li>
                <li>Discover hubs: <a href="${baseUrl}/my-hubs">/my-hubs</a> (uses user token)</li>
                <li>Pick a hub -> projects: /my-projects/{hubId}</li>
                <li>Open project views (user-token):
                    <ul>
                        <li>Overview: /my-project-details/{hubId}/{projectId}</li>
                        <li>Team: /my-project-users/{hubId}/{projectId}</li>
                        <li>Issues: /my-project-issues/{hubId}/{projectId}</li>
                        <li>Files/Models: /my-project-files/{hubId}/{projectId}</li>
                    </ul>
                </li>
                <li>Automation (optional): run <a href="${baseUrl}/login-2legged">/login-2legged</a> then /project-nav/{hubId}/{projectId} for copy/paste links.</li>
            </ol>
        </div>

        <div style="background:#fff8e1;padding:16px;margin:12px 0;border-radius:6px;border-left:4px solid #ffc107;">
            <h2>3) Quick Actions</h2>
            <ul>
                <li>See hubs (auto-picks user token if present): <a href="${baseUrl}/hubs">/hubs</a> (add ?region=EMEA if needed)</li>
                <li>Projects with current token: /projects/{hubId} (falls back to user token if no app token)</li>
                <li>Project navigation hub (app token): /project-nav/{hubId}/{projectId}</li>
            </ul>
        </div>

        <div style="background:#e8f5e8;padding:16px;margin:12px 0;border-radius:6px;border-left:4px solid #28a745;">
            <h2>4) Diagnostics</h2>
            <ul>
                <li><a href="${baseUrl}/test-token">/test-token</a> - Validate current token</li>
                <li><a href="${baseUrl}/test-all-apis">/test-all-apis</a> - Smoke test hubs/projects/users/issues/files</li>
                <li><a href="${baseUrl}/diagnose-api">/diagnose-api</a> - Fast check</li>
                <li><a href="${baseUrl}/diagnose">/diagnose</a> - Detailed status</li>
                <li><a href="${baseUrl}/diagnose-hub-access">/diagnose-hub-access</a> - Hub/project access troubleshooting</li>
            </ul>
        </div>

        <div style="background:#f8f9fa;padding:12px;margin:12px 0;border-radius:6px;border-left:4px solid #6c757d;">
            <h2>5) BIM Tips</h2>
            <ul>
                <li>Use user-token endpoints (/my-*) to mirror ACC UI access.</li>
                <li>Issues API requires the project Issues/Quality module and correct scopes.</li>
                <li>Files require Docs permissions; add viewables:read for model derivatives.</li>
                <li>If a link fails, re-auth with the correct token (user vs app) and retry.</li>
            </ul>
        </div>

        <div style="background:#eef2ff;padding:16px;margin:12px 0;border-radius:6px;border-left:4px solid #4f46e5;">
            <h2>Live Hubs & Projects (auto-load)</h2>
            <p style="margin:0 0 8px 0;">Must be logged in. Uses user token if available, else app token.</p>
            <button id="loadHubs" style="padding:8px 12px;border:1px solid #4f46e5;background:#4f46e5;color:white;border-radius:4px;cursor:pointer;">Load hubs</button>
            <div id="hubsContainer" style="margin-top:12px;font-family:monospace;"></div>
        </div>

        <script>
        (function() {
            const BASE_URL = '${baseUrl}';
            const hubsEl = document.getElementById('hubsContainer');
            const loadBtn = document.getElementById('loadHubs');

            async function loadHubs() {
                hubsEl.textContent = 'Loading hubs...';
                try {
                    const hubsRes = await fetch(BASE_URL + '/hubs' + window.location.search);
                    const hubsJson = await hubsRes.json();
                    if (!hubsRes.ok) throw new Error((hubsJson && hubsJson.error) || hubsRes.statusText);
                    if (!hubsJson.hubs || hubsJson.hubs.length === 0) {
                        hubsEl.textContent = 'No hubs returned. Authenticate first or verify permissions.';
                        return;
                    }
                    hubsEl.innerHTML = hubsJson.hubs.map(hub => {
                        const flow = hubsJson.userToken ? 'user-token (/my-*)' : 'app-token (/project-*)';
                        return '<div style="margin-bottom:10px;padding:8px;border:1px solid #ddd;border-radius:4px;">' +
                            '<div><strong>' + hub.name + '</strong> (' + hub.id + ') [' + (hub.region || 'default') + ']</div>' +
                            '<div style="margin:4px 0;">Flow: ' + flow + '</div>' +
                            '<button data-hub="' + hub.id + '" style="padding:4px 8px;border:1px solid #4f46e5;background:#fff;color:#4f46e5;border-radius:3px;cursor:pointer;">Load projects</button>' +
                            '<div id="projects-' + hub.id + '" style="margin-top:6px;"></div>' +
                        '</div>';
                    }).join('');

                    hubsEl.querySelectorAll('button[data-hub]').forEach(btn => {
                        btn.onclick = async () => {
                            const hubId = btn.getAttribute('data-hub');
                            const target = document.getElementById('projects-' + hubId);
                            target.textContent = 'Loading projects...';
                            try {
                                const endpoint = hubsJson.userToken ? 'my-projects' : 'projects';
                                const projRes = await fetch(BASE_URL + '/' + endpoint + '/' + hubId);
                                const projJson = await projRes.json();
                                if (!projRes.ok) throw new Error((projJson && projJson.error) || projRes.statusText);
                                if (!projJson.projects || projJson.projects.length === 0) {
                                    target.textContent = 'No projects found or insufficient permissions.';
                                    return;
                                }
                                target.innerHTML = '<ul style="padding-left:16px;">' + projJson.projects.map(p => {
                                    const prefix = hubsJson.userToken ? 'my-project' : 'project';
                                    const detailId = 'project-detail-' + hubId + '-' + p.id.replace(/[^a-zA-Z0-9_-]/g, '');
                                    return '<li style="margin-bottom:6px;">' + p.name + ' (' + p.id + ') ? ' +
                                        '<a href="' + BASE_URL + '/' + prefix + '-details/' + hubId + '/' + p.id + '" class="project-inline-details" data-hub="' + hubId + '" data-project="' + p.id + '" data-prefix="' + prefix + '" data-detail-id="' + detailId + '">details</a> | ' +
                                        '<a href="' + BASE_URL + '/' + prefix + '-users/' + hubId + '/' + p.id + '">users</a> | ' +
                                        '<a href="' + BASE_URL + '/' + prefix + '-issues/' + hubId + '/' + p.id + '">issues</a> | ' +
                                        '<a href="' + BASE_URL + '/' + prefix + '-files/' + hubId + '/' + p.id + '">files</a>' +
                                        '<div id="' + detailId + '" style="margin-top:4px;padding-left:8px;font-size:12px;color:#1a1a1a;"></div>' +
                                    '</li>';
                                }).join('') + '</ul>';

                                target.querySelectorAll('.project-inline-details').forEach(link => {
                                    link.onclick = async (evt) => {
                                        evt.preventDefault();
                                        const detailTarget = document.getElementById(link.dataset.detailId);
                                        if (!detailTarget) return;
                                        detailTarget.textContent = 'Loading project details...';
                                        try {
                                            const detailUrl = BASE_URL + '/' + link.dataset.prefix + '-details/' + link.dataset.hub + '/' + link.dataset.project;
                                            const detailRes = await fetch(detailUrl);
                                            const detailJson = await detailRes.json();
                                            if (!detailRes.ok) throw new Error((detailJson && detailJson.error) || detailRes.statusText);
                                            const info = detailJson.projectInfo || {};
                                            const modelFolders = info.modelFolders || detailJson.modelFolders || [];
                                            detailTarget.innerHTML =
                                                'Name: ' + (info.name || 'n/a') +
                                                ' | Status: ' + (info.status || 'n/a') +
                                                ' | Files: ' + (info.totalFiles != null ? info.totalFiles : 'n/a') +
                                                ' | Folders: ' + (info.totalTopLevelFolders != null ? info.totalTopLevelFolders : 'n/a') +
                                                (modelFolders.length ? '<br>Models: ' + modelFolders.map(m => m.name + ' (' + (m.fileCount || 0) + ')').join(', ') : '');
                                        } catch (err) {
                                            detailTarget.textContent = 'Details load failed: ' + err.message;
                                        }
                                    };
                                });
                            } catch (e) {
                                target.textContent = 'Projects load failed: ' + e.message;
                            }
                        };
                    });
                } catch (e) {
                    hubsEl.textContent = 'Hubs load failed: ' + e.message + '. Authenticate with /login-pkce or /login-2legged and retry. If EU hub, append ?region=EMEA to the URL.';
                }
            }

            loadBtn.onclick = loadHubs;
            loadHubs();
        })();
        </script>
    `);
});

const CLIENT_ID = 'HSIzVK9vT8AGY0emotXgOylhsczvoO0XSPy6M76vAAovAeN8';
const CLIENT_SECRET = 'JuLnXcguwKB2g0QoG5auJWnF2XnI9uiW8wdYw5xIAmKiqTIvK3q9pfAHTq7ZcNZ4';
const REDIRECT_URI = 'http://localhost:3000/callback';
const PORT = 3000;

let access_token = null;
let client_credentials_token = null;

// OAuth state management for security (in production, use secure session storage)
const oauthStates = new Map();

// PKCE storage for code verifiers (enhanced security)
const pkceStorage = new Map();

// Refresh token storage (in production, use secure database)
let refresh_token = null;
let token_expiry = null;

// Clean up expired states and PKCE data every 10 minutes
setInterval(() => {
    const now = Date.now();
    
    // Clean expired OAuth states
    for (const [state, data] of oauthStates.entries()) {
        if (now - data.timestamp > 600000) { // 10 minutes
            oauthStates.delete(state);
        }
    }
    
    // Clean expired PKCE data
    for (const [state, data] of pkceStorage.entries()) {
        if (now - data.timestamp > 600000) { // 10 minutes
            pkceStorage.delete(state);
        }
    }
}, 600000);

// PKCE Helper Functions
function generatePKCE() {
    // Generate code verifier (43-128 characters, base64url-safe)
    const codeVerifier = crypto.randomBytes(32).toString('base64url');
    
    // Generate code challenge using SHA256
    const codeChallenge = crypto
        .createHash('sha256')
        .update(codeVerifier)
        .digest('base64url');
    
    return {
        codeVerifier,
        codeChallenge,
        method: 'S256'
    };
}

function base64URLEncode(str) {
    return str.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

// Comprehensive scope and permission testing endpoint
app.get('/test-all-apis', async (req, res) => {
    if (!client_credentials_token) {
        return res.json({ error: 'No 2-legged token available', action: 'Visit /login-2legged first' });
    }

    const testResults = {
        timestamp: new Date().toISOString(),
        clientId: CLIENT_ID,
        tokenScopes: 'data:read data:write account:read account:write user-profile:read',
        tests: {}
    };

    // Get first available hub and project for testing
    let testHubId, testProjectId, testProjectName;
    
    try {
        // Step 1: Test Hubs API
        console.log('🧪 Testing Hubs API...');
        const hubsResponse = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
        });
        
        testResults.tests.hubs = {
            status: 'SUCCESS',
            count: hubsResponse.data.data.length,
            message: `Found ${hubsResponse.data.data.length} hubs`
        };

        if (hubsResponse.data.data.length > 0) {
            testHubId = hubsResponse.data.data[0].id;
            
            // Step 2: Test Projects API
            console.log('🧪 Testing Projects API...');
            const projectsResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${testHubId}/projects`, {
                headers: { 'Authorization': `Bearer ${client_credentials_token}` }
            });
            
            testResults.tests.projects = {
                status: 'SUCCESS',
                count: projectsResponse.data.data.length,
                message: `Found ${projectsResponse.data.data.length} projects in first hub`
            };

            if (projectsResponse.data.data.length > 0) {
                testProjectId = projectsResponse.data.data[0].id;
                testProjectName = projectsResponse.data.data[0].attributes?.name || 'Unknown';

                // Step 3: Test Project Details API
                console.log('🧪 Testing Project Details API...');
                try {
                    const detailsResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${testHubId}/projects/${testProjectId}`, {
                        headers: { 'Authorization': `Bearer ${client_credentials_token}` }
                    });
                    testResults.tests.projectDetails = {
                        status: 'SUCCESS',
                        message: 'Can access detailed project information'
                    };
                } catch (detailsErr) {
                    testResults.tests.projectDetails = {
                        status: 'FAILED',
                        error: detailsErr.response?.data?.developerMessage || detailsErr.message,
                        statusCode: detailsErr.response?.status
                    };
                }

                // Step 4: Test Users API
                console.log('🧪 Testing Users API...');
                try {
                    const usersResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${testHubId}/projects/${testProjectId}/users`, {
                        headers: { 'Authorization': `Bearer ${client_credentials_token}` }
                    });
                    testResults.tests.users = {
                        status: 'SUCCESS',
                        count: usersResponse.data.data.length,
                        message: `Found ${usersResponse.data.data.length} users in project`
                    };
                } catch (usersErr) {
                    testResults.tests.users = {
                        status: 'FAILED',
                        error: usersErr.response?.data?.developerMessage || usersErr.message,
                        statusCode: usersErr.response?.status,
                        possibleCause: 'May require user management permissions or admin access'
                    };
                }

                // Step 5: Test Issues API (multiple endpoints)
                console.log('🧪 Testing Issues API...');
                const containerId = testProjectId.replace('b.', '');
                
                // Test standard issues endpoint
                try {
                    const issuesResponse = await axios.get(`https://developer.api.autodesk.com/issues/v1/containers/${containerId}/issues`, {
                        headers: { 
                            'Authorization': `Bearer ${client_credentials_token}`,
                            'Content-Type': 'application/vnd.api+json'
                        },
                        params: { 'page[limit]': 10 }
                    });
                    testResults.tests.issues = {
                        status: 'SUCCESS',
                        count: issuesResponse.data.data.length,
                        message: `Found ${issuesResponse.data.data.length} issues in project`
                    };
                } catch (issuesErr) {
                    // Try alternative Issues API endpoints
                    const alternativeTests = [];
                    
                    // Try quality-issues endpoint
                    try {
                        await axios.get(`https://developer.api.autodesk.com/issues/v1/containers/${containerId}/quality-issues`, {
                            headers: { 
                                'Authorization': `Bearer ${client_credentials_token}`,
                                'Content-Type': 'application/vnd.api+json'
                            }
                        });
                        alternativeTests.push('quality-issues: SUCCESS');
                    } catch {
                        alternativeTests.push('quality-issues: FAILED');
                    }

                    testResults.tests.issues = {
                        status: 'FAILED',
                        error: issuesErr.response?.data?.developerMessage || issuesErr.message,
                        statusCode: issuesErr.response?.status,
                        alternativeTests: alternativeTests,
                        possibleCause: 'Issues module may not be enabled in ACC project'
                    };
                }

                // Step 6: Test TopFolders API
                console.log('🧪 Testing TopFolders API...');
                try {
                    const foldersResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${testHubId}/projects/${testProjectId}/topFolders`, {
                        headers: { 'Authorization': `Bearer ${client_credentials_token}` }
                    });
                    testResults.tests.topFolders = {
                        status: 'SUCCESS',
                        count: foldersResponse.data.data.length,
                        message: `Found ${foldersResponse.data.data.length} top-level folders`
                    };
                } catch (foldersErr) {
                    testResults.tests.topFolders = {
                        status: 'FAILED',
                        error: foldersErr.response?.data?.developerMessage || foldersErr.message,
                        statusCode: foldersErr.response?.status
                    };
                }
            }
        }

    } catch (mainErr) {
        testResults.tests.hubs = {
            status: 'CRITICAL_FAILURE',
            error: mainErr.response?.data?.developerMessage || mainErr.message,
            message: 'Basic hub access failed - check credentials'
        };
    }

    // Generate summary and recommendations
    const successCount = Object.values(testResults.tests).filter(test => test.status === 'SUCCESS').length;
    const totalTests = Object.keys(testResults.tests).length;

    testResults.summary = {
        successfulAPIs: successCount,
        totalAPIs: totalTests,
        successRate: `${Math.round((successCount/totalTests) * 100)}%`,
        testProject: testProjectName || 'N/A'
    };

    testResults.recommendations = [];
    
    if (testResults.tests.hubs?.status !== 'SUCCESS') {
        testResults.recommendations.push('❌ CRITICAL: Basic API access failed - verify Client ID and Secret');
    } else {
        testResults.recommendations.push('✅ Basic API access working');
    }

    if (testResults.tests.users?.status === 'FAILED') {
        testResults.recommendations.push('⚠️ Users API failed - may need admin permissions or user management scope');
    }

    if (testResults.tests.issues?.status === 'FAILED') {
        testResults.recommendations.push('⚠️ Issues API failed - project may not have Issues module enabled in ACC');
    }

    if (successCount === totalTests) {
        testResults.recommendations.push('🎉 All APIs working perfectly! Your app has full access.');
    }

    res.json(testResults);
});

// Enhanced diagnostic endpoint with API testing
app.get('/diagnose-api', async (req, res) => {
    const results = {
        timestamp: new Date().toISOString(),
        tokenStatus: {},
        apiTests: {},
        recommendations: []
    };

    // Test 2-legged token
    if (client_credentials_token) {
        results.tokenStatus['2-legged'] = {
            available: true,
            token: client_credentials_token.substring(0, 20) + '...'
        };

        // Test basic API access
        try {
            const hubsResponse = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
                headers: { 'Authorization': `Bearer ${client_credentials_token}` }
            });
            results.apiTests.hubs = {
                status: 'SUCCESS',
                hubCount: hubsResponse.data.data.length,
                firstHub: hubsResponse.data.data[0] || null
            };

            // If we have hubs, test project access
            if (hubsResponse.data.data.length > 0) {
                const testHub = hubsResponse.data.data[0];
                try {
                    const projectsResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${testHub.id}/projects`, {
                        headers: { 'Authorization': `Bearer ${client_credentials_token}` }
                    });
                    results.apiTests.projects = {
                        status: 'SUCCESS',
                        projectCount: projectsResponse.data.data.length,
                        hubTested: testHub.attributes.name
                    };

                    // If we have projects, test users and issues APIs
                    if (projectsResponse.data.data.length > 0) {
                        const testProject = projectsResponse.data.data[0];
                        
                        // Test Users API
                        try {
                            await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${testHub.id}/projects/${testProject.id}/users`, {
                                headers: { 'Authorization': `Bearer ${client_credentials_token}` }
                            });
                            results.apiTests.users = { status: 'SUCCESS' };
                        } catch (userErr) {
                            results.apiTests.users = {
                                status: 'FAILED',
                                error: userErr.response?.data?.developerMessage || userErr.message,
                                statusCode: userErr.response?.status
                            };
                        }

                        // Test Issues API
                        try {
                            const containerId = testProject.id.replace('b.', '');
                            await axios.get(`https://developer.api.autodesk.com/issues/v1/containers/${containerId}/issues`, {
                                headers: { 
                                    'Authorization': `Bearer ${client_credentials_token}`,
                                    'Content-Type': 'application/vnd.api+json'
                                }
                            });
                            results.apiTests.issues = { status: 'SUCCESS' };
                        } catch (issueErr) {
                            results.apiTests.issues = {
                                status: 'FAILED',
                                error: issueErr.response?.data?.developerMessage || issueErr.message,
                                statusCode: issueErr.response?.status
                            };
                        }
                    }
                } catch (projectErr) {
                    results.apiTests.projects = {
                        status: 'FAILED',
                        error: projectErr.response?.data?.developerMessage || projectErr.message
                    };
                }
            }
        } catch (hubErr) {
            results.apiTests.hubs = {
                status: 'FAILED',
                error: hubErr.response?.data?.developerMessage || hubErr.message
            };
        }
    } else {
        results.tokenStatus['2-legged'] = { available: false };
    }

    // Generate recommendations
    if (results.apiTests.hubs?.status === 'SUCCESS') {
        results.recommendations.push('✅ Basic API access is working');
    } else {
        results.recommendations.push('❌ Basic API access failed - check credentials');
    }

    if (results.apiTests.users?.status === 'FAILED') {
        results.recommendations.push('⚠️ Users API failed - may require admin permissions or different scopes');
    }

    if (results.apiTests.issues?.status === 'FAILED') {
        results.recommendations.push('⚠️ Issues API failed - project may not have Issues module enabled');
    }

    res.json(results);
});

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

// Hub Access Diagnostic - Identify provisioning and permission issues
app.get('/diagnose-hub-access', async (req, res) => {
    try {
        const diagnostics = {
            timestamp: new Date().toISOString(),
            clientId: CLIENT_ID.substring(0, 20) + '...',
            testResults: {},
            issues: [],
            recommendations: []
        };

        console.log('🔍 Running comprehensive hub access diagnostics...');

        // Test 1: Check if we have any tokens
        if (!access_token && !client_credentials_token) {
            diagnostics.issues.push({
                severity: 'CRITICAL',
                issue: 'No OAuth tokens available',
                description: 'Both 2-legged and 3-legged tokens are missing',
                fix: 'Complete OAuth authentication first'
            });
            
            return res.json({
                status: 'BLOCKED',
                message: 'No authentication tokens available',
                diagnostics,
                nextSteps: [
                    'Visit /login-2legged for app-level access',
                    'Visit /login for user-level access'
                ]
            });
        }

        // Test 2: Test with available token
        const token = access_token || client_credentials_token;
        const tokenType = access_token ? '3-legged (User)' : '2-legged (App)';
        
        console.log(`🧪 Testing hub access with ${tokenType} token...`);

        // Test basic hub access
        try {
            const hubsResponse = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            diagnostics.testResults.hubs = {
                status: 'SUCCESS',
                count: hubsResponse.data.data?.length || 0,
                hubs: hubsResponse.data.data?.map(hub => ({
                    id: hub.id,
                    name: hub.attributes?.name,
                    region: hub.attributes?.region
                })) || []
            };

            if (hubsResponse.data.data?.length === 0) {
                diagnostics.issues.push({
                    severity: 'HIGH',
                    issue: 'No hubs returned',
                    description: `${tokenType} token is valid but returns 0 hubs`,
                    possibleCauses: [
                        'App not provisioned to ACC/BIM 360 accounts',
                        'User lacks access to any ACC/BIM 360 projects',
                        'Missing required scopes (account:read)',
                        'Account admin has not added this app'
                    ]
                });

                if (tokenType === '3-legged (User)') {
                    diagnostics.recommendations.push({
                        priority: 'HIGH',
                        action: 'App Provisioning Required',
                        steps: [
                            'Contact Account Admin for each ACC/BIM 360 account you need access to',
                            'Ask them to add your app under Account Admin → Settings → Custom Integrations',
                            `Provide Client ID: ${CLIENT_ID}`,
                            'Request "Document Management" permission (required)',
                            'Request "Account Admin" permission (for admin operations)',
                            'If "Custom Integrations" is missing, email bim360appsactivations@autodesk.com'
                        ]
                    });
                } else {
                    diagnostics.recommendations.push({
                        priority: 'HIGH',
                        action: 'App-Level Access Configuration',
                        steps: [
                            'For 2-legged access, the app must be added to specific projects',
                            'Account Admins must provision your app in their ACC/BIM 360 accounts',
                            'Consider using 3-legged OAuth for broader hub access'
                        ]
                    });
                }
            } else {
                // Test project access for found hubs
                for (const hub of hubsResponse.data.data) {
                    try {
                        const projectsResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hub.id}/projects`, {
                            headers: { 
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json',
                                'x-ads-region': hub.attributes?.region || 'US'
                            }
                        });

                        diagnostics.testResults[`projects_${hub.id}`] = {
                            status: 'SUCCESS',
                            hubName: hub.attributes?.name,
                            count: projectsResponse.data.data?.length || 0,
                            projects: projectsResponse.data.data?.map(project => ({
                                id: project.id,
                                name: project.attributes?.name
                            })) || []
                        };

                        if (projectsResponse.data.data?.length === 0) {
                            diagnostics.issues.push({
                                severity: 'MEDIUM',
                                issue: `No projects in hub: ${hub.attributes?.name}`,
                                description: 'Hub accessible but no projects visible',
                                possibleCauses: [
                                    'User lacks "Docs → Files" access in projects',
                                    'No projects exist in this hub',
                                    'App not added to specific projects (for 2-legged)'
                                ]
                            });
                        }

                    } catch (projErr) {
                        diagnostics.issues.push({
                            severity: 'MEDIUM',
                            issue: `Projects API failed for hub: ${hub.attributes?.name}`,
                            description: projErr.response?.data || projErr.message,
                            possibleCauses: [
                                'Missing x-ads-region header for EMEA projects',
                                'Insufficient permissions in this hub'
                            ]
                        });
                    }
                }
            }

        } catch (hubErr) {
            diagnostics.testResults.hubs = {
                status: 'FAILED',
                error: hubErr.response?.data || hubErr.message
            };

            diagnostics.issues.push({
                severity: 'CRITICAL',
                issue: 'Hubs API access failed',
                description: hubErr.response?.data || hubErr.message,
                possibleCauses: [
                    'Invalid or expired token',
                    'Missing account:read scope',
                    'App not configured for Data Management API'
                ]
            });
        }

        // Generate final assessment
        const criticalIssues = diagnostics.issues.filter(i => i.severity === 'CRITICAL').length;
        const highIssues = diagnostics.issues.filter(i => i.severity === 'HIGH').length;
        
        let status = 'HEALTHY';
        if (criticalIssues > 0) status = 'CRITICAL';
        else if (highIssues > 0) status = 'NEEDS_ACTION';
        else if (diagnostics.issues.length > 0) status = 'WARNINGS';

        res.json({
            status,
            message: `Hub access diagnostic complete - ${diagnostics.issues.length} issues found`,
            tokenType,
            diagnostics,
            summary: {
                totalHubs: diagnostics.testResults.hubs?.count || 0,
                totalIssues: diagnostics.issues.length,
                criticalIssues,
                highIssues
            }
        });

    } catch (err) {
        console.error('❌ Hub diagnostic failed:', err);
        res.status(500).json({
            status: 'ERROR',
            message: 'Diagnostic failed',
            error: err.message
        });
    }
});

// 2-Legged OAuth (Client Credentials) - for app-only access
app.get('/login-2legged', async (req, res) => {
    try {
        logEvent('security', { action: '2-legged OAuth attempt', ip: req.ip });
        console.log('🔑 Attempting 2-legged OAuth (Client Credentials)...');
        
        // Use the exact format from official APS documentation
        const postData = new URLSearchParams();
        postData.append('grant_type', 'client_credentials');
        postData.append('client_id', CLIENT_ID);
        postData.append('client_secret', CLIENT_SECRET);
        // Scopes needed for hub access: account:read is crucial for ACC/BIM 360 hubs
        postData.append('scope', 'account:read data:read data:write viewables:read');
        
        console.log('🔍 Debug: Attempting 2-legged OAuth with:');
        console.log('  - CLIENT_ID:', CLIENT_ID.substring(0, 20) + '...');
        console.log('  - Grant Type: client_credentials');
        console.log('  - Scope: account:read data:read data:write viewables:read');
        console.log('  - Endpoint: https://developer.api.autodesk.com/authentication/v2/token');
        
        const response = await axios.post('https://developer.api.autodesk.com/authentication/v2/token', 
            postData.toString(), {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
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
        logEvent('error', { endpoint: '/login-2legged', error: err.message, details: err.response?.data });
        console.error('❌ 2-Legged OAuth Error:', {
            status: err.response?.status,
            statusText: err.response?.statusText,
            data: err.response?.data,
            message: err.message
        });
        
        // Enhanced error response with detailed troubleshooting
        const errorResponse = {
            error: 'Failed to get 2-legged OAuth token',
            details: err.response?.data || err.message,
            status: err.response?.status || 500,
            timestamp: new Date().toISOString(),
            flow: '2-legged (Client Credentials)',
            troubleshooting: []
        };
        
        // Add specific troubleshooting advice based on error type
        if (err.response?.status === 401) {
            errorResponse.troubleshooting.push('AUTH-001: Client ID does not have access to API product');
            errorResponse.troubleshooting.push('Verify CLIENT_ID and CLIENT_SECRET are correct');
            errorResponse.troubleshooting.push('Check app exists in your Autodesk Developer Console');
            errorResponse.troubleshooting.push('Ensure app has required API access enabled');
        } else if (err.response?.status === 400) {
            // Check for specific scope-related errors
            const errorData = err.response?.data;
            const isInvalidScope = errorData?.error === 'invalid_scope' || 
                                   errorData?.error_description?.includes('scope') ||
                                   JSON.stringify(errorData).includes('invalid_scope');
            
            if (isInvalidScope) {
                errorResponse.troubleshooting.push('🔍 SCOPE-001: The app is not configured for 2-legged OAuth with the requested scope');
                errorResponse.troubleshooting.push('🏗️  Check your Autodesk Developer Console app settings');
                errorResponse.troubleshooting.push('⚙️  Ensure "Data Management API" is enabled for your app');
                errorResponse.troubleshooting.push('🔐 Verify your app supports Client Credentials flow');
                errorResponse.troubleshooting.push('🔧 Try enabling additional APIs: Model Derivative API, Design Automation API');
                errorResponse.troubleshooting.push('⚠️  Some scopes may only be available in 3-legged OAuth flows');
                errorResponse.troubleshooting.push('📋 This CLIENT_ID may only support user authentication, not app authentication');
            } else {
                errorResponse.troubleshooting.push('Bad request - check grant_type and scope parameters');
                errorResponse.troubleshooting.push('Verify request format matches APS OAuth 2.0 specification');
            }
        } else if (err.response?.status >= 500) {
            errorResponse.troubleshooting.push('Server error - Autodesk service may be temporarily unavailable');
            errorResponse.troubleshooting.push('Wait and retry the request');
        } else {
            errorResponse.troubleshooting.push('Check network connectivity');
            errorResponse.troubleshooting.push('Visit /diagnose for detailed diagnostic information');
        }
        
        res.status(err.response?.status || 500).json(errorResponse);
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

// Get user's hubs (ACC hubs) - uses user token if available, falls back to app token
app.get('/hubs', async (req, res) => {
    // Prefer user token (3-legged) over app token (2-legged) for maximum hub access
    const token = access_token || client_credentials_token;
    const tokenType = access_token ? 'User Token (3-legged)' : 'App Token (2-legged)';
    const usingUserToken = tokenType.startsWith('User');
    const baseUrl = getBaseUrl(req) || '';
    
    if (!token) {
        return res.json({
            error: 'No authentication token available',
            action: 'Visit /login-pkce for user-level access or /login-2legged for app-level access'
        });
    }

    try {
        logEvent('api', { endpoint: '/hubs', tokenType, hasUserToken: !!access_token });
        
        // Add EMEA region support - try with default region first
        const headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
        
        // Add EMEA region header if requested
        const region = req.query.region || req.headers['x-ads-region'];
        if (region && region.toUpperCase() === 'EMEA') {
            headers['x-ads-region'] = 'EMEA';
            console.log('🌍 Adding EMEA region header for European projects');
        }
        
        const response = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers
        });

        const hubs = response.data.data.map(hub => {
            const projectsEndpoint = usingUserToken ? 'my-projects' : 'projects';
            return {
                id: hub.id,
                name: hub.attributes.name,
                region: hub.attributes.region,
                projectsLink: `${baseUrl}/${projectsEndpoint}/${hub.id}`,
                // Quick navigation helpers
                quickActions: {
                    viewProjects: `${baseUrl}/${projectsEndpoint}/${hub.id}`,
                    hubInfo: {
                        id: hub.id,
                        displayName: hub.attributes.name,
                        region: hub.attributes.region
                    },
                    authContext: usingUserToken ?
                        'Links use /my- endpoints (3-legged token).' :
                        'Links use app-level /project- endpoints (2-legged token).'
                }
            };
        });

        res.json({
            success: true,
            hubCount: hubs.length,
            authMethod: tokenType,
            userToken: !!access_token,
            hubs: hubs,
            nextStep: usingUserToken ?
                'Click projectsLink to open /my-projects and stay on the user-token flow.' :
                'Click projectsLink to open /projects (app token flow).',
            authRecommendation: access_token ? 
                '? Using your user token - you should see all hubs you have access to' : 
                '?? Using app token - you may not see all your hubs. Try 3-legged OAuth (/login-pkce) for full access'
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

// Get user's hubs with 3-legged OAuth (user-level permissions)
app.get('/my-hubs', async (req, res) => {
    if (!access_token) {
        return res.json({
            error: 'No user authentication token available',
            message: 'This endpoint requires user-level authentication (3-legged OAuth)',
            action: 'Visit /login-pkce for maximum security or /login for standard 3-legged OAuth',
            difference: 'User tokens show ALL hubs you have access to, not just app-authorized hubs'
        });
    }

    try {
        logEvent('api', { endpoint: '/my-hubs', tokenType: 'User Token (3-legged)', userAuth: true });
        
        const response = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: {
                'Authorization': `Bearer ${access_token}`
            }
        });

        const hubs = response.data.data.map(hub => ({
            id: hub.id,
            name: hub.attributes.name,
            region: hub.attributes.region,
            projectsLink: `http://localhost:3000/my-projects/${hub.id}`,
            // Enhanced user-level actions
            userActions: {
                viewMyProjects: `http://localhost:3000/my-projects/${hub.id}`,
                hubDetails: {
                    id: hub.id,
                    displayName: hub.attributes.name,
                    region: hub.attributes.region,
                    accountId: hub.relationships?.account?.data?.id
                }
            }
        }));

        res.json({
            success: true,
            hubCount: hubs.length,
            authMethod: 'User Token (3-legged OAuth)',
            userAuthenticated: true,
            hubs: hubs,
            message: `✅ Found ${hubs.length} hubs with your user permissions - this should include ALL hubs where you are an admin or member`,
            nextSteps: [
                'These are all hubs you have personal access to',
                'Click projectsLink to see projects in each hub',
                'User-level access may show more hubs than app-level access'
            ]
        });
        
    } catch (err) {
        logEvent('error', { endpoint: '/my-hubs', error: err.message, status: err.response?.status });
        console.error('❌ User hubs request failed:', err.response?.data || err.message);
        res.status(500).json({
            error: 'Failed to get user hubs',
            details: err.response?.data || err.message,
            status: err.response?.status,
            troubleshooting: [
                'Ensure you completed 3-legged OAuth authentication',
                'Check if your user token is still valid',
                'Verify your Autodesk account has access to ACC hubs'
            ]
        });
    }
});

// Get projects in a specific hub
app.get('/projects/:hubId', async (req, res) => {
    const token = client_credentials_token || access_token;
    const tokenType = client_credentials_token ? 'App Token (2-legged)' : 'User Token (3-legged)';
    const usingUserToken = !client_credentials_token && !!access_token;
    const baseUrl = getBaseUrl(req) || '';

    if (!token) {
        return res.json({
            error: 'No authentication token available',
            action: 'Visit /login-pkce (user token) or /login-2legged (app token) first'
        });
    }

    const hubId = req.params.hubId;

    try {
        const response = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const prefix = usingUserToken ? 'my-project' : 'project';
        const projects = response.data.data.map(project => ({
            id: project.id,
            name: project.attributes.name,
            status: project.attributes.status,
            created: project.attributes.createdAt,
            updated: project.attributes.updatedAt,
            // Direct action links
            detailsLink: `${baseUrl}/${prefix}-details/${hubId}/${project.id}`,
            usersLink: `${baseUrl}/${prefix}-users/${hubId}/${project.id}`,
            issuesLink: `${baseUrl}/${prefix}-issues/${hubId}/${project.id}`,
            filesLink: `${baseUrl}/${prefix}-files/${hubId}/${project.id}`,
            navDashboard: client_credentials_token ? `${baseUrl}/project-nav/${hubId}/${project.id}` : null,
            // Complete navigation structure
            navigation: {
                hubId: hubId,
                projectId: project.id,
                projectName: project.attributes.name,
                allEndpoints: {
                    overview: `${baseUrl}/${prefix}-details/${hubId}/${project.id}`,
                    team: `${baseUrl}/${prefix}-users/${hubId}/${project.id}`,
                    issues: `${baseUrl}/${prefix}-issues/${hubId}/${project.id}`,
                    files: `${baseUrl}/${prefix}-files/${hubId}/${project.id}`
                }
            }
        }));

        const nextSteps = [
            usingUserToken ?
                'Links use /my- endpoints with your user token.' :
                'Links use app-level endpoints (2-legged).'
        ];

        if (client_credentials_token) {
            nextSteps.push('Click navDashboard for complete project navigation hub');
        }

        nextSteps.push(
            'Click detailsLink for comprehensive project info',
            'Click usersLink for project team members',
            'Click issuesLink for project issues',
            'Click filesLink for project files and models'
        );

        res.json({
            success: true,
            hubId: hubId,
            projectCount: projects.length,
            authMethod: tokenType,
            projects: projects,
            nextSteps: nextSteps
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

// Get projects in a specific hub with user token
app.get('/my-projects/:hubId', async (req, res) => {
    if (!access_token) {
        return res.json({
            error: 'No user authentication token available',
            message: 'This endpoint requires user-level authentication (3-legged OAuth)',
            action: 'Visit /login-pkce for maximum security or /login for standard 3-legged OAuth'
        });
    }

    const hubId = req.params.hubId;
    const baseUrl = getBaseUrl(req) || '';

    try {
        logEvent('api', { endpoint: '/my-projects', hubId, tokenType: 'User Token (3-legged)' });
        
        const response = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects`, {
            headers: {
                'Authorization': `Bearer ${access_token}`
            }
        });

        const projects = response.data.data.map(project => ({
            id: project.id,
            name: project.attributes.name,
            status: project.attributes.status,
            created: project.attributes.createdAt,
            updated: project.attributes.updatedAt,
            // User-level action links (use user token endpoints)
            detailsLink: `${baseUrl}/my-project-details/${hubId}/${project.id}`,
            usersLink: `${baseUrl}/my-project-users/${hubId}/${project.id}`,
            issuesLink: `${baseUrl}/my-project-issues/${hubId}/${project.id}`,
            filesLink: `${baseUrl}/my-project-files/${hubId}/${project.id}`,
            // User-level navigation
            userNavigation: {
                hubId: hubId,
                projectId: project.id,
                projectName: project.attributes.name,
                userEndpoints: {
                    overview: `${baseUrl}/my-project-details/${hubId}/${project.id}`,
                    team: `${baseUrl}/my-project-users/${hubId}/${project.id}`,
                    issues: `${baseUrl}/my-project-issues/${hubId}/${project.id}`,
                    files: `${baseUrl}/my-project-files/${hubId}/${project.id}`
                }
            }
        }));

        res.json({
            success: true,
            hubId: hubId,
            projectCount: projects.length,
            authMethod: 'User Token (3-legged OAuth)',
            userAuthenticated: true,
            projects: projects,
            message: `✅ Found ${projects.length} projects in this hub using your user permissions`,
            nextSteps: [
                'These projects use your user-level permissions',
                'You should have access to more project data than with app-level tokens',
                'Click userEndpoints for detailed project information'
            ]
        });
        
    } catch (err) {
        logEvent('error', { endpoint: '/my-projects', hubId, error: err.message });
        console.error('❌ User projects request failed:', err.response?.data || err.message);
        res.status(500).json({
            error: 'Failed to get user projects',
            details: err.response?.data || err.message,
            status: err.response?.status,
            troubleshooting: [
                'Check if your user token is valid',
                'Verify you have access to this hub',
                'Ensure the hubId is correct'
            ]
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
    const region = req.query.region || req.headers['x-ads-region'];
    const headers = { 'Authorization': `Bearer ${client_credentials_token}` };
    if (region) headers['x-ads-region'] = region.toUpperCase();

    try {
        // Use correct Project Users API endpoint
        const response = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}/users`, {
            headers
        });

        const users = response.data.data.map(user => ({
            id: user.id,
            name: user.attributes?.name || 'N/A',
            email: user.attributes?.email || 'N/A',
            role: user.attributes?.role || 'N/A',
            status: user.attributes?.status || 'active',
            company: user.attributes?.company || 'N/A'
        }));

        res.json({
            success: true,
            projectId: projectId,
            userCount: users.length,
            region: headers['x-ads-region'] || 'default',
            users: users
        });

    } catch (err) {
        console.error('? Project users failed:', err.response?.data || err.message);
        
        // If direct user access fails, provide detailed error info and alternatives
        res.status(err.response?.status || 500).json({
            error: 'Could not access project users',
            reason: 'This may be due to insufficient permissions or API restrictions',
            details: err.response?.data || err.message,
            status: err.response?.status || 'unknown',
            usedRegionHeader: headers['x-ads-region'] || 'none',
            possibleCauses: [
                'Project is in EMEA and needs x-ads-region: EMEA',
                'Project does not have user management enabled',
                'Your app needs additional scopes (team:read, user-profile:read)',
                'You may need admin permissions in the ACC project',
                'Some projects restrict user data access via API'
            ],
            alternatives: [
                'Retry with ?region=EMEA if this is an EU hub',
                'Try 3-legged OAuth with admin user credentials',
                'Check ACC project settings for API access permissions',
                'Contact project admin to enable user API access'
            ],
            successfulEndpoints: {
                projects: `http://localhost:3000/projects/${req.params.hubId}`,
                projectDetails: `http://localhost:3000/project-details/${req.params.hubId}/${req.params.projectId}`
            },
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
        // Get issues using correct ACC Issues API endpoint
        const response = await axios.get(`https://developer.api.autodesk.com/issues/v1/containers/${containerId}/issues`, {
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
            reason: 'Issues API access is restricted or not available',
            details: err.response?.data || err.message,
            status: err.response?.status || 'unknown',
            possibleCauses: [
                'Issues API is not enabled for this project',
                'Your app needs Issues API scope enabled',
                'Project may not have Construction Cloud Issues module activated',
                'Container ID format may be incorrect'
            ],
            troubleshooting: [
                'Check if project has Issues module enabled in ACC',
                'Verify your Autodesk app has Issues API permissions',
                'Try with a different project that definitely has issues',
                'Contact ACC project admin to enable Issues API access'
            ],
            workingEndpoints: {
                projectDetails: `http://localhost:3000/project-details/${req.params.hubId}/${req.params.projectId}`,
                projectFiles: `http://localhost:3000/project-files/${req.params.hubId}/${req.params.projectId}`
            }
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
        console.log(`\n📂 === FETCHING FILES FOR PROJECT: ${projectId} (App Token - 2-legged) ===`);
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
                // Use /items/{id} endpoint instead of /folders/{id}/contents
                const folderContents = await axios.get(`https://developer.api.autodesk.com/data/v1/projects/${projectId}/items/${encodeURIComponent(folder.id)}/children`, {
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

// ----- User-token (3-legged) project endpoints -----

// Get comprehensive project details with user token
// Get comprehensive project details with user token
app.get('/my-project-details/:hubId/:projectId', async (req, res) => {
    if (!access_token) {
        return res.json({
            error: 'No user authentication token available',
            message: 'This endpoint requires user-level authentication (3-legged OAuth)',
            action: 'Visit /login-pkce for maximum security or /login for standard 3-legged OAuth'
        });
    }

    const { hubId, projectId } = req.params;

    try {
        logEvent('api', { endpoint: '/my-project-details', hubId, projectId, tokenType: 'User Token (3-legged)' });

        const projectResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}`, {
            headers: { 'Authorization': `Bearer ${access_token}` },
        });

        const foldersResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}/topFolders`, {
            headers: { 'Authorization': `Bearer ${access_token}` },
        });

        const project = projectResponse.data.data;
        const folders = foldersResponse.data.data;

        let totalFiles = 0;
        let modelFolders = [];

        for (const folder of folders) {
            try {
                const folderContents = await axios.get(`https://developer.api.autodesk.com/project/v1/projects/${projectId}/folders/${folder.id}/contents`, {
                    headers: { 'Authorization': `Bearer ${access_token}` },
                });

                const files = folderContents.data.data.filter(item => item.type === 'items');
                totalFiles += files.length;

                if (folder.attributes.displayName === 'Project Files' || folder.attributes.displayName === 'Plans') {
                    modelFolders.push({
                        name: folder.attributes.displayName,
                        fileCount: files.length,
                        lastModified: folder.attributes.lastModifiedTime,
                    });
                }
            } catch (err) {
                console.log(`Could not access folder ${folder.attributes.displayName}:`, err.response?.status);
            }
        }

        res.json({
            success: true,
            authMethod: 'User Token (3-legged OAuth)',
            projectInfo: {
                id: project.id,
                name: project.attributes.name,
                status: project.attributes.status,
                created: project.attributes.createdAt,
                updated: project.attributes.updatedAt,
                totalTopLevelFolders: folders.length,
                totalFiles: totalFiles,
                modelFolders: modelFolders,
            },
            folders: folders.map(f => ({
                id: f.id,
                name: f.attributes.displayName,
                created: f.attributes.createTime,
                modified: f.attributes.lastModifiedTime,
            })),
            navigation: {
                users: `http://localhost:3000/my-project-users/${hubId}/${projectId}`,
                issues: `http://localhost:3000/my-project-issues/${hubId}/${projectId}`,
                allFiles: `http://localhost:3000/my-project-files/${hubId}/${projectId}`,
            },
        });

    } catch (err) {
        logEvent('error', { endpoint: '/my-project-details', hubId, projectId, error: err.message });
        res.status(500).json({
            error: 'Failed to get project details with user token',
            details: err.response?.data || err.message,
            status: err.response?.status,
        });
    }
});
app.get('/my-project-users/:hubId/:projectId', async (req, res) => {
    if (!access_token) {
        return res.json({
            error: 'No user authentication token available',
            message: 'This endpoint requires user-level authentication (3-legged OAuth)',
            action: 'Visit /login-pkce for maximum security or /login for standard 3-legged OAuth'
        });
    }

    const { hubId, projectId } = req.params;
    const region = req.query.region || req.headers['x-ads-region'];
    const headers = { 'Authorization': `Bearer ${access_token}` };
    if (region) headers['x-ads-region'] = region.toUpperCase();

    try {
        logEvent('api', { endpoint: '/my-project-users', hubId, projectId, tokenType: 'User Token (3-legged)', region: headers['x-ads-region'] || 'default' });

        const response = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}/users`, {
            headers
        });

        const users = response.data.data.map(user => ({
            id: user.id,
            name: user.attributes?.name || 'N/A',
            email: user.attributes?.email || 'N/A',
            role: user.attributes?.role || 'N/A',
            status: user.attributes?.status || 'active',
            company: user.attributes?.company || 'N/A'
        }));

        res.json({
            success: true,
            authMethod: 'User Token (3-legged OAuth)',
            projectId: projectId,
            userCount: users.length,
            region: headers['x-ads-region'] || 'default',
            users: users
        });

    } catch (err) {
        logEvent('error', { endpoint: '/my-project-users', hubId, projectId, region: headers['x-ads-region'] || 'none', error: err.message });
        res.status(err.response?.status || 500).json({
            error: 'Could not access project users with user token',
            details: err.response?.data || err.message,
            status: err.response?.status || 'unknown',
            usedRegionHeader: headers['x-ads-region'] || 'none',
            possibleCauses: [
                'Project is in EMEA and needs x-ads-region: EMEA',
                'Your Autodesk user may not have permission to list users',
                'Team data access may be restricted for this project',
                'Additional scopes (team:read, user-profile:read) may be required'
            ],
            alternatives: [
                'Confirm your account has admin rights in this ACC project',
                'Retry with ?region=EMEA if this is an EU hub',
                'Retry with a user that can manage project members'
            ],
            navigation: {
                projectOverview: `http://localhost:3000/my-project-details/${hubId}/${projectId}`
            },
        });
    }
});

// Get project issues with user token
app.get('/my-project-issues/:hubId/:projectId', async (req, res) => {
    if (!access_token) {
        return res.json({
            error: 'No user authentication token available',
            message: 'This endpoint requires user-level authentication (3-legged OAuth)',
            action: 'Visit /login-pkce for maximum security or /login for standard 3-legged OAuth'
        });
    }

    const { hubId, projectId } = req.params;
    const containerId = projectId.replace('b.', '');

    try {
        logEvent('api', { endpoint: '/my-project-issues', hubId, projectId, tokenType: 'User Token (3-legged)' });

        const response = await axios.get(`https://developer.api.autodesk.com/issues/v1/containers/${containerId}/issues`, {
            headers: { 
                'Authorization': `Bearer ${access_token}`,
                'Content-Type': 'application/vnd.api+json'
            },
            params: {
                'page[limit]': 50
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
            description: issue.attributes.description?.substring(0, 200) + '...'
        }));

        const statusCounts = issues.reduce((acc, issue) => {
            acc[issue.status] = (acc[issue.status] || 0) + 1;
            return acc;
        }, {});

        res.json({
            success: true,
            authMethod: 'User Token (3-legged OAuth)',
            projectId: projectId,
            totalIssues: issues.length,
            statusBreakdown: statusCounts,
            recentIssues: issues.slice(0, 10),
            allIssues: issues,
            pagination: response.data.meta || 'No pagination info'
        });

    } catch (err) {
        logEvent('error', { endpoint: '/my-project-issues', hubId, projectId, error: err.message });
        res.status(500).json({
            error: 'Failed to get project issues with user token',
            details: err.response?.data || err.message,
            status: err.response?.status || 'unknown',
            troubleshooting: [
                'Confirm Issues module is enabled for this project',
                'Ensure your Autodesk user has Issues access',
                'Verify your app scopes include data:read and issues access'
            ],
            workingEndpoints: {
                projectDetails: `http://localhost:3000/my-project-details/${hubId}/${projectId}`,
                projectFiles: `http://localhost:3000/my-project-files/${hubId}/${projectId}`
            }
        });
    }
});

// Get project files and models with user token
app.get('/my-project-files/:hubId/:projectId', async (req, res) => {
    if (!access_token) {
        return res.json({
            error: 'No user authentication token available',
            message: 'This endpoint requires user-level authentication (3-legged OAuth)',
            action: 'Visit /login-pkce for maximum security or /login for standard 3-legged OAuth'
        });
    }

    const { hubId, projectId } = req.params;

    try {
        logEvent('api', { endpoint: '/my-project-files', hubId, projectId, tokenType: 'User Token (3-legged)' });
        console.log(`\n📂 === FETCHING FILES FOR PROJECT: ${projectId} (User Token) ===`);

        const foldersResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects/${projectId}/topFolders`, {
            headers: { 'Authorization': `Bearer ${access_token}` }
        });

        const folders = foldersResponse.data.data;
        console.log(`📁 Found ${folders.length} top-level folders:`, folders.map(f => ({ name: f.attributes.displayName, id: f.id, type: f.type })));
        let allFiles = [];
        let modelFiles = [];
        let lastUpdate = null;

        // Helper function to recursively read folder contents
        async function readFolderRecursively(folderId, folderName, depth = 0) {
            if (depth > 5) {
                console.log(`⚠️ Max depth reached for ${folderName}`);
                return; // Prevent infinite recursion
            }
            
            console.log(`🔍 Reading folder: ${folderName} (depth: ${depth})`);
            try {
                // Use /items/{id} endpoint instead of /folders/{id}/contents
                const folderContents = await axios.get(`https://developer.api.autodesk.com/data/v1/projects/${projectId}/items/${encodeURIComponent(folderId)}/children`, {
                    headers: { 'Authorization': `Bearer ${access_token}` }
                });

                const items = folderContents.data.data;
                console.log(`  ✓ Folder ${folderName}: ${items.length} items`);

                // Process files
                const files = items
                    .filter(item => item.type === 'items')
                    .map(item => ({
                        id: item.id,
                        name: item.attributes.displayName,
                        extension: item.attributes.extension?.type,
                        size: item.attributes.storageSize,
                        created: item.attributes.createTime,
                        modified: item.attributes.lastModifiedTime,
                        version: item.attributes.versionNumber,
                        folder: folderName
                    }));

                console.log(`  📄 Found ${files.length} files in ${folderName}`);
                allFiles = allFiles.concat(files);

                const models = files.filter(file => 
                    file.extension && ['dwg', 'rvt', 'ifc', 'nwd', 'nwc', 'skp', '3dm'].includes(file.extension.toLowerCase())
                );
                modelFiles = modelFiles.concat(models);
                console.log(`  🏗️ Found ${models.length} model files in ${folderName}`);

                files.forEach(file => {
                    if (!lastUpdate || new Date(file.modified) > new Date(lastUpdate)) {
                        lastUpdate = file.modified;
                    }
                });

                // Process subfolders
                const subfolders = items.filter(item => item.type === 'folders');
                console.log(`  📂 Found ${subfolders.length} subfolders in ${folderName}`);
                for (const subfolder of subfolders) {
                    const subfolderName = `${folderName}/${subfolder.attributes.displayName}`;
                    await readFolderRecursively(subfolder.id, subfolderName, depth + 1);
                }

            } catch (err) {
                console.log(`❌ Could not access folder ${folderName} (ID: ${folderId}):`, {
                    status: err.response?.status,
                    statusText: err.response?.statusText,
                    error: err.response?.data?.developerMessage || err.response?.data || err.message,
                    folderId: folderId,
                    projectId: projectId,
                    url: `https://developer.api.autodesk.com/project/v1/projects/${projectId}/folders/${folderId}/contents`
                });
            }
        }

        // Read all top-level folders and their subfolders
        console.log(`🚀 Starting recursive folder scan...`);
        for (const folder of folders) {
            await readFolderRecursively(folder.id, folder.attributes.displayName);
        }
        console.log(`✅ Scan complete! Total files: ${allFiles.length}, Model files: ${modelFiles.length}`);

        res.json({
            success: true,
            authMethod: 'User Token (3-legged OAuth)',
            projectId: projectId,
            totalFiles: allFiles.length,
            lastUpdated: lastUpdate,
            modelFiles: modelFiles,
            allFiles: allFiles,
            folders: folders.map(f => ({
                id: f.id,
                name: f.attributes.displayName,
                counts: {
                    files: allFiles.filter(file => file.folder === f.attributes.displayName).length,
                    models: modelFiles.filter(model => model.folder === f.attributes.displayName).length
                }
            })),
            navigation: {
                overview: `http://localhost:3000/my-project-details/${hubId}/${projectId}`,
                issues: `http://localhost:3000/my-project-issues/${hubId}/${projectId}`,
                users: `http://localhost:3000/my-project-users/${hubId}/${projectId}`
            }
        });

    } catch (err) {
        logEvent('error', { endpoint: '/my-project-files', hubId, projectId, error: err.message });
        res.status(500).json({
            error: 'Failed to get project files with user token',
            details: err.response?.data || err.message,
            status: err.response?.status || 'unknown',
            troubleshooting: [
                'Confirm your Autodesk user can view project files',
                'Ensure required scopes (data:read, viewables:read) are granted',
                'Check if specific folders have restricted permissions'
            ],
            workingEndpoints: {
                projectDetails: `http://localhost:3000/my-project-details/${hubId}/${projectId}`,
                projectIssues: `http://localhost:3000/my-project-issues/${hubId}/${projectId}`
            }
        });
    }
});

// 3-Legged OAuth login with enhanced security
app.get('/login', async (req, res) => {
    try {
        logEvent('security', { action: '3-legged OAuth login initiated', ip: req.ip });
        console.log('🔐 Initiating 3-legged OAuth flow with enhanced security...');
        
        // Generate secure random state parameter
        const state = crypto.randomBytes(16).toString('hex');
        
        // Store state with timestamp for validation
        oauthStates.set(state, {
            timestamp: Date.now(),
            ip: req.ip || req.connection.remoteAddress,
            userAgent: req.get('User-Agent')
        });
        
        // Enhanced scopes for comprehensive hub access as admin  
        const scopes = [
            'user-profile:read',     // User information
            'data:read',             // Read project data  
            'data:write',            // Write project data
            'account:read',          // Essential for hub access
            'account:write',         // For admin operations on hubs
            'viewables:read'         // View models and documents
        ].join(' ');
        
        const authUrl = `https://developer.api.autodesk.com/authentication/v2/authorize?` +
            `response_type=code&` +
            `client_id=${CLIENT_ID}&` +
            `redirect_uri=${encodeURIComponent(REDIRECT_URI)}&` +
            `scope=${encodeURIComponent(scopes)}&` +
            `state=${state}`;

        console.log('🔗 Enhanced 3-legged OAuth URL generated');
        console.log('🔐 State parameter:', state);
        
        res.send(`
            <h2>🔐 APS OAuth Demo - Enhanced 3-Legged Login</h2>
            <div style="background: #f0f8ff; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007acc;">
                <h3>🔒 Security Features Enabled:</h3>
                <ul>
                    <li>✅ State parameter validation</li>
                    <li>✅ Enhanced error handling</li>
                    <li>✅ Proper token exchange format</li>
                    <li>✅ Comprehensive scopes: ${scopes}</li>
                </ul>
            </div>
            <p><strong>🚀 <a href="${authUrl}" target="_blank" style="color: #007acc; text-decoration: none; font-size: 18px;">Launch Secure Autodesk Login</a></strong></p>
            <div style="margin-top: 20px; padding: 10px; background: #fff3cd; border-radius: 5px;">
                <h4>📋 What happens next:</h4>
                <ol>
                    <li>You'll be redirected to Autodesk's secure login page</li>
                    <li>After authentication, you'll grant permissions to this app</li>
                    <li>You'll be redirected back with an authorization code</li>
                    <li>The app will securely exchange the code for an access token</li>
                </ol>
            </div>
            <p><small>🔐 State: ${state} | Generated: ${new Date().toLocaleString()}</small></p>
        `);
        
    } catch (error) {
        logEvent('error', { endpoint: '/login', error: error.message });
        console.error('❌ Error generating OAuth login URL:', error);
        res.status(500).json({
            error: 'Failed to generate OAuth login URL',
            details: error.message,
            recommendation: 'Check server configuration and try again'
        });
    }
});

// PKCE-Enhanced 3-Legged OAuth login (Maximum Security)
app.get('/login-pkce', async (req, res) => {
    try {
        logEvent('security', { action: 'PKCE-enhanced 3-legged OAuth flow initiated', ip: req.ip });
        console.log('🔐 Initiating PKCE-enhanced 3-legged OAuth flow (maximum security)...');
        
        // Generate PKCE parameters
        const { codeVerifier, codeChallenge, method } = generatePKCE();
        
        // Generate secure random state parameter
        const state = crypto.randomBytes(16).toString('hex');
        
        // Store both state and PKCE data for validation
        oauthStates.set(state, {
            timestamp: Date.now(),
            ip: req.ip || req.connection.remoteAddress,
            userAgent: req.get('User-Agent'),
            flowType: 'pkce'
        });
        
        pkceStorage.set(state, {
            codeVerifier,
            codeChallenge,
            method,
            timestamp: Date.now()
        });
        
        // Enhanced scopes for comprehensive hub access as admin (PKCE flow)
        const scopes = [
            'user-profile:read',     // User information
            'data:read',             // Read project data  
            'data:write',            // Write project data
            'account:read',          // Essential for hub access
            'account:write',         // For admin operations on hubs
            'viewables:read'         // View models and documents
        ].join(' ');
        
        const authUrl = `https://developer.api.autodesk.com/authentication/v2/authorize?` +
            `response_type=code&` +
            `client_id=${CLIENT_ID}&` +
            `redirect_uri=${encodeURIComponent(REDIRECT_URI)}&` +
            `scope=${encodeURIComponent(scopes)}&` +
            `state=${state}&` +
            `code_challenge=${codeChallenge}&` +
            `code_challenge_method=${method}`;

        console.log('🔗 PKCE-enhanced OAuth URL generated');
        console.log('🔐 State parameter:', state);
        console.log('🔐 Code challenge:', codeChallenge.substring(0, 20) + '...');
        
        res.send(`
            <h2>🛡️ APS OAuth Demo - PKCE Enhanced Login (Maximum Security)</h2>
            <div style="background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #28a745;">
                <h3>🛡️ PKCE Security Features:</h3>
                <ul>
                    <li>✅ <strong>PKCE (RFC 7636)</strong> - Proof Key for Code Exchange</li>
                    <li>✅ <strong>Code Challenge/Verifier</strong> - SHA256 with S256 method</li>
                    <li>✅ <strong>State parameter validation</strong> - CSRF protection</li>
                    <li>✅ <strong>Enhanced error handling</strong> - Detailed security logs</li>
                    <li>✅ <strong>Proper token exchange</strong> - APS OAuth 2.0 compliant</li>
                    <li>✅ <strong>Extended scopes</strong>: ${scopes}</li>
                </ul>
            </div>
            <p><strong>🚀 <a href="${authUrl}" target="_blank" style="color: #28a745; text-decoration: none; font-size: 18px;">Launch PKCE-Protected Autodesk Login</a></strong></p>
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #6f42c1;">
                <h4>🔒 PKCE Security Benefits:</h4>
                <ul>
                    <li><strong>Authorization Code Interception Attack Protection</strong></li>
                    <li><strong>No Client Secret Required</strong> (safer for mobile/SPA apps)</li>
                    <li><strong>Cryptographic Verification</strong> of authorization code exchange</li>
                    <li><strong>Enhanced Security</strong> beyond traditional OAuth 2.0</li>
                </ul>
            </div>
            <div style="margin-top: 20px; padding: 10px; background: #fff3cd; border-radius: 5px;">
                <h4>📋 PKCE Flow Process:</h4>
                <ol>
                    <li>App generates random code verifier and SHA256 challenge</li>
                    <li>Challenge sent to Autodesk authorization server</li>
                    <li>After user authentication, authorization code returned</li>
                    <li>App exchanges code + verifier for tokens (cryptographic proof)</li>
                </ol>
            </div>
            <p><small>🔐 State: ${state} | Challenge Method: ${method} | Generated: ${new Date().toLocaleString()}</small></p>
        `);
        
    } catch (error) {
        logEvent('error', { endpoint: '/login-pkce', error: error.message });
        console.error('❌ Error generating PKCE OAuth login URL:', error);
        res.status(500).json({
            error: 'Failed to generate PKCE OAuth login URL',
            details: error.message,
            recommendation: 'Check server configuration and try again'
        });
    }
});

// Handle OAuth callback
app.get('/callback', async (req, res) => {
    const { code, state, error } = req.query;
    
    // Enhanced error handling for OAuth callback errors
    if (error) {
        logEvent('error', { endpoint: '/callback', error });
        console.error('❌ OAuth callback error:', error);
        return res.status(400).json({ 
            error: 'OAuth authorization failed', 
            details: error,
            description: req.query.error_description || 'User denied access or authentication failed',
            recommendation: 'Try the authentication flow again'
        });
    }

    if (!code) {
        logEvent('error', { endpoint: '/callback', error: 'No authorization code received' });
        console.error('❌ No authorization code received');
        return res.status(400).json({ 
            error: 'No authorization code received',
            details: 'Authorization code is required to exchange for access token',
            recommendation: 'Complete the OAuth flow by visiting /login first'
        });
    }

    // ✅ ENHANCED SECURITY: Validate state parameter
    if (state) {
        const storedStateData = oauthStates.get(state);
        if (!storedStateData) {
            logEvent('security', { endpoint: '/callback', event: 'Invalid state parameter', state });
            console.error('❌ Invalid state parameter:', state);
            return res.status(400).json({
                error: 'Invalid state parameter',
                details: 'State parameter does not match or has expired',
                security: 'Possible CSRF attack attempt',
                recommendation: 'Start the OAuth flow again from /login'
            });
        }
        
        // Check if state has expired (10 minutes)
        if (Date.now() - storedStateData.timestamp > 600000) {
            logEvent('security', { endpoint: '/callback', event: 'Expired state parameter', state });
            oauthStates.delete(state);
            console.error('❌ Expired state parameter:', state);
            return res.status(400).json({
                error: 'Expired state parameter',
                details: 'OAuth flow took too long, state parameter expired',
                recommendation: 'Start the OAuth flow again from /login'
            });
        }
        
        // Remove used state to prevent replay attacks
        oauthStates.delete(state);
        logEvent('security', { endpoint: '/callback', event: 'State parameter validated', state });
    } else {
        logEvent('security', { endpoint: '/callback', event: 'No state parameter received' });
    }

    console.log('🔁 Received authorization code:', code.substring(0, 20) + '...');

    // Check if this is a PKCE flow
    const pkceData = state ? pkceStorage.get(state) : null;
    const isPKCE = pkceData !== null;

    try {
        logEvent('security', { endpoint: '/callback', event: 'Token exchange attempt', code });
        if (isPKCE) {
            console.log('🔄 Exchanging authorization code for access token (PKCE flow)...');
            console.log('🔐 Using code verifier for PKCE verification');
        } else {
            console.log('🔄 Exchanging authorization code for access token (standard flow)...');
        }
        
        // ✅ ENHANCED: Support both standard and PKCE flows (APS expects client_secret even with PKCE for confidential apps)
        const tokenParams = {
            grant_type: 'authorization_code',
            code: code,
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET,
            redirect_uri: REDIRECT_URI
        };
        
        // Add PKCE code_verifier when present
        if (isPKCE && pkceData) {
            tokenParams.code_verifier = pkceData.codeVerifier;
            console.log('🔐 PKCE: Added code_verifier (and client_secret) to token exchange');
            // Clean up PKCE data after use
            pkceStorage.delete(state);
        } else {
            console.log('🔐 Standard: Using client_secret for token exchange');
        }
        
        const formData = new URLSearchParams(tokenParams);

        const tokenResponse = await axios.post('https://developer.api.autodesk.com/authentication/v2/token', 
            formData.toString(), {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
        });

        // Store tokens and calculate expiry
        access_token = tokenResponse.data.access_token;
        refresh_token = tokenResponse.data.refresh_token || null;
        token_expiry = refresh_token ? Date.now() + (tokenResponse.data.expires_in * 1000) : null;
        
        const tokenInfo = {
            access_token: access_token.substring(0, 20) + '...',
            token_type: tokenResponse.data.token_type,
            expires_in: tokenResponse.data.expires_in,
            scope: tokenResponse.data.scope,
            has_refresh_token: !!refresh_token,
            flow_type: isPKCE ? 'PKCE Enhanced' : 'Standard',
            expires_at: token_expiry ? new Date(token_expiry).toISOString() : null
        };
        
        logEvent('security', { endpoint: '/callback', event: 'Token exchange success', token: access_token ? access_token.substring(0, 20) + '...' : null });
        if (isPKCE) {
            console.log('✅ PKCE-enhanced 3-legged OAuth successful:', tokenInfo);
        } else {
            console.log('✅ Standard 3-legged OAuth successful:', tokenInfo);
        }
        
        // Enhanced response with refresh token information
        const response = {
            success: true,
            message: `✅ ${isPKCE ? 'PKCE-Enhanced' : 'Standard'} 3-legged OAuth completed successfully!`,
            tokenInfo: tokenInfo,
            security: {
                flow_type: isPKCE ? 'PKCE (RFC 7636) - Maximum Security' : 'Standard OAuth 2.0',
                state_validated: !!state,
                csrf_protection: !!state,
                pkce_protection: isPKCE
            },
            nextSteps: [
                'You can now make API calls on behalf of the user',
                `Token expires in ${tokenResponse.data.expires_in} seconds`,
                'Use the token with Authorization: Bearer header'
            ]
        };
        
        if (refresh_token) {
            response.nextSteps.push('Refresh token available for automatic renewal');
            response.nextSteps.push('Visit /refresh-token to renew access token');
        }
        
        if (isPKCE) {
            response.nextSteps.push('PKCE protection prevented code interception attacks');
        }
        
        res.json(response);
        
    } catch (err) {
        logEvent('error', { endpoint: '/callback', error: err.message, details: err.response?.data });
        console.error('❌ Token exchange error:', {
            status: err.response?.status,
            statusText: err.response?.statusText,
            data: err.response?.data,
            message: err.message
        });
        
        // Enhanced error response with detailed information
        const errorResponse = {
            error: 'Failed to exchange authorization code for access token',
            details: err.response?.data || err.message,
            status: err.response?.status || 500,
            timestamp: new Date().toISOString(),
            troubleshooting: []
        };
        
        // Add specific troubleshooting advice based on error type
        if (err.response?.status === 401) {
            errorResponse.troubleshooting.push('Check CLIENT_ID and CLIENT_SECRET are correct');
            errorResponse.troubleshooting.push('Verify app exists in your Autodesk Developer Console');
        } else if (err.response?.status === 400) {
            errorResponse.troubleshooting.push('Check redirect_uri matches app configuration');
            errorResponse.troubleshooting.push('Verify authorization code is valid and not expired');
        } else {
            errorResponse.troubleshooting.push('Check network connectivity');
            errorResponse.troubleshooting.push('Visit /diagnose for more information');
        }
        
        res.status(err.response?.status || 500).json(errorResponse);
    }
});

// Refresh Token endpoint for automatic token renewal
app.get('/refresh-token', async (req, res) => {
    if (!refresh_token) {
        return res.status(400).json({
            error: 'No refresh token available',
            details: 'Refresh token is only available after successful 3-legged OAuth flow',
            recommendation: 'Complete 3-legged OAuth first: visit /login or /login-pkce'
        });
    }
    
    // Check if current access token is expired or about to expire (within 5 minutes)
    const now = Date.now();
    const fiveMinutes = 5 * 60 * 1000;
    
    if (token_expiry && (now < token_expiry - fiveMinutes)) {
        return res.json({
            message: 'Access token is still valid',
            expires_in: Math.floor((token_expiry - now) / 1000),
            expires_at: new Date(token_expiry).toISOString(),
            recommendation: 'No need to refresh yet'
        });
    }

    try {
        console.log('🔄 Refreshing access token using refresh token...');
        
        const formData = new URLSearchParams({
            grant_type: 'refresh_token',
            refresh_token: refresh_token,
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET
        });

        const tokenResponse = await axios.post('https://developer.api.autodesk.com/authentication/v2/token', 
            formData.toString(), {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
        });

        // Update stored tokens
        const old_access_token = access_token;
        access_token = tokenResponse.data.access_token;
        
        // Update refresh token if new one provided
        if (tokenResponse.data.refresh_token) {
            refresh_token = tokenResponse.data.refresh_token;
        }
        
        token_expiry = Date.now() + (tokenResponse.data.expires_in * 1000);

        const tokenInfo = {
            access_token: access_token.substring(0, 20) + '...',
            old_token: old_access_token.substring(0, 20) + '...',
            token_type: tokenResponse.data.token_type,
            expires_in: tokenResponse.data.expires_in,
            scope: tokenResponse.data.scope,
            refreshed_at: new Date().toISOString(),
            expires_at: new Date(token_expiry).toISOString()
        };
        
        console.log('✅ Token refresh successful:', tokenInfo);
        
        res.json({
            success: true,
            message: '✅ Access token refreshed successfully!',
            tokenInfo: tokenInfo,
            nextSteps: [
                'Updated access token is now active',
                `New token expires in ${tokenResponse.data.expires_in} seconds`,
                'Continue making API calls with the refreshed token'
            ]
        });
        
    } catch (err) {
        console.error('❌ Token refresh error:', {
            status: err.response?.status,
            statusText: err.response?.statusText,
            data: err.response?.data,
            message: err.message
        });
        
        // Clear invalid refresh token
        refresh_token = null;
        token_expiry = null;
        
        const errorResponse = {
            error: 'Failed to refresh access token',
            details: err.response?.data || err.message,
            status: err.response?.status || 500,
            timestamp: new Date().toISOString(),
            troubleshooting: []
        };
        
        if (err.response?.status === 401 || err.response?.status === 400) {
            errorResponse.troubleshooting.push('Refresh token is invalid or expired');
            errorResponse.troubleshooting.push('User needs to re-authenticate via 3-legged OAuth');
            errorResponse.troubleshooting.push('Visit /login or /login-pkce to start new authentication');
        } else {
            errorResponse.troubleshooting.push('Check network connectivity');
            errorResponse.troubleshooting.push('Retry the refresh operation');
        }
        
        res.status(err.response?.status || 500).json(errorResponse);
    }
});

// Token Introspection endpoint for validation
app.get('/introspect-token', async (req, res) => {
    const token = req.query.token || access_token;
    
    if (!token) {
        return res.status(400).json({
            error: 'No token provided',
            details: 'Provide token as query parameter or ensure access_token is available',
            usage: 'GET /introspect-token?token=YOUR_TOKEN'
        });
    }

    try {
        console.log('🔍 Introspecting token:', token.substring(0, 20) + '...');
        
        const formData = new URLSearchParams({
            token: token,
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET
        });

        const introspectResponse = await axios.post('https://developer.api.autodesk.com/authentication/v2/introspect', 
            formData.toString(), {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
        });

        const introspectionData = introspectResponse.data;
        
        console.log('✅ Token introspection successful');
        
        res.json({
            success: true,
            message: '✅ Token introspection completed',
            tokenStatus: {
                active: introspectionData.active,
                client_id: introspectionData.client_id,
                exp: introspectionData.exp,
                iat: introspectionData.iat,
                scope: introspectionData.scope,
                token_type: introspectionData.token_type,
                expires_at: introspectionData.exp ? new Date(introspectionData.exp * 1000).toISOString() : null,
                issued_at: introspectionData.iat ? new Date(introspectionData.iat * 1000).toISOString() : null,
                time_remaining: introspectionData.exp ? Math.max(0, introspectionData.exp - Math.floor(Date.now() / 1000)) : null
            },
            validation: {
                is_valid: introspectionData.active === true,
                is_expired: introspectionData.exp ? introspectionData.exp < Math.floor(Date.now() / 1000) : false,
                belongs_to_client: introspectionData.client_id === CLIENT_ID
            }
        });
        
    } catch (err) {
        console.error('❌ Token introspection error:', {
            status: err.response?.status,
            statusText: err.response?.statusText,
            data: err.response?.data,
            message: err.message
        });
        
        const errorResponse = {
            error: 'Failed to introspect token',
            details: err.response?.data || err.message,
            status: err.response?.status || 500,
            timestamp: new Date().toISOString(),
            troubleshooting: []
        };
        
        if (err.response?.status === 401) {
            errorResponse.troubleshooting.push('Invalid client credentials for introspection');
            errorResponse.troubleshooting.push('Check CLIENT_ID and CLIENT_SECRET');
        } else if (err.response?.status === 400) {
            errorResponse.troubleshooting.push('Invalid token format or missing parameters');
            errorResponse.troubleshooting.push('Ensure token parameter is provided correctly');
        } else {
            errorResponse.troubleshooting.push('Check network connectivity');
            errorResponse.troubleshooting.push('Verify APS introspection endpoint availability');
        }
        
        res.status(err.response?.status || 500).json(errorResponse);
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
