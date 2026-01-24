const express = require('express');
const axios = require('axios');
const DatabaseHelper = require('./database-helper');
const app = express();

// Initialize database helper
const db = new DatabaseHelper();

// Root route for instructions
app.get('/', (req, res) => {
    res.send(`
        <h2>APS OAuth Demo - BIM Project Management Integration</h2>
        <p>Welcome! Use the following endpoints:</p>
        <h3>🔑 Authentication</h3>
        <ul>
            <li><a href="/login-2legged">/login-2legged</a> - ✅ Get app token (2-legged OAuth)</li>
            <li><a href="/test-token">/test-token</a> - 🧪 Test if your token works</li>
            <li><a href="/login">/login</a> - Start user authentication (3-legged OAuth)</li>
            <li><a href="/diagnose">/diagnose</a> - 🚨 Diagnostic information</li>
        </ul>
        <h3>🏢 ACC Data Access</h3>
        <ul>
            <li><a href="/hubs">/hubs</a> - 🏢 Get your ACC hubs</li>
            <li>/projects/{hubId} - 📁 Get projects in a specific hub</li>
            <li>/project-details/{hubId}/{projectId} - 📊 Comprehensive project analysis</li>
            <li>/project-issues/{hubId}/{projectId} - 🐛 Project issues</li>
            <li>/project-files/{hubId}/{projectId} - 📄 Project files and models</li>
        </ul>
        <h3>🗄️ SQL Database Integration</h3>
        <ul>
            <li><a href="/test-database">/test-database</a> - 🔌 Test database connection</li>
            <li><a href="/create-views">/create-views</a> - 🏗️ Create simplified SQL views from ACC data</li>
            <li><a href="/test-views">/test-views</a> - 🧪 Test and preview simplified views</li>
            <li><a href="/sync-to-database">/sync-to-database</a> - 🔄 AUTOMATE: Fetch ACC data and update database</li>
            <li><a href="/power-bi-summary">/power-bi-summary</a> - 📊 Power BI ready summary</li>
        </ul>
        <p><strong>✅ ACC API Automation Ready!</strong></p>
        <p><strong>Purpose:</strong> Automate manual ACC data extraction → Update existing database schema</p>
        <p><strong>Workflow:</strong> /login-2legged → /test-database → /sync-to-database → /create-views → /power-bi-summary</p>
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

// Test database connection
app.get('/test-database', async (req, res) => {
    try {
        console.log('🔌 Testing database connection...');
        
        // Test connection using our database helper
        const connected = await db.testConnection();
        if (!connected) {
            throw new Error('Database connection test failed');
        }
        
        // Get additional info
        const projectCount = await db.getProjectCount();
        
        console.log('✅ Database connection successful');
        res.json({
            success: true,
            message: '✅ Database connection successful (via sqlcmd)',
            serverInfo: {
                server: process.env.DB_SERVER || 'localhost\\SQLEXPRESS',
                database: process.env.ACC_DB || 'acc_data_schema',
                user: process.env.DB_USER,
                method: 'sqlcmd (bypassing Node.js connection issues)'
            },
            dataInfo: {
                projectCount: projectCount,
                tablesAvailable: true
            },
            nextStep: 'Visit /sync-to-database for full ACC automation'
        });
    } catch (err) {
        console.error('❌ Database connection failed:', err);
        res.status(500).json({
            error: 'Database connection failed',
            details: err.message,
            method: 'sqlcmd approach',
            suggestions: [
                'Check if SQL Server is running',
                'Verify sqlcmd is available',
                'Check SQL Server authentication',
                'Ensure acc_data_schema database exists'
            ]
        });
    }
});

// Create database tables for ACC data - TEMPORARILY DISABLED (needs database helper integration)
app.get('/create-views-disabled', async (req, res) => {
    res.json({
        status: 'temporarily_disabled',
        message: 'This endpoint needs to be updated to use the database helper',
        workingEndpoints: ['/test-database', '/sync-to-database'],
        suggestion: 'Use /sync-to-database to populate data first'
    });
});

// Original create-views code (commented out)
/*
app.get('/create-views', async (req, res) => {
    try {
        console.log('🏗️ Creating simplified ACC data views...');
        const pool = await sql.connect(dbConfig);

        // Create simplified Hubs view (mapping from admin_accounts)
        await pool.request().query(`
            IF EXISTS (SELECT * FROM sys.views WHERE name='vw_Hubs')
                DROP VIEW vw_Hubs
        `);
        await pool.request().query(`
            CREATE VIEW vw_Hubs AS
            SELECT DISTINCT
                CAST(bim360_account_id AS VARCHAR(255)) as hubId,
                display_name as hubName,
                'US' as region,
                CAST(bim360_account_id AS VARCHAR(255)) as accountId,
                start_date as createdAt,
                end_date as lastSync
            FROM admin_accounts
            WHERE display_name IS NOT NULL
        `);

        // Create simplified Projects view (mapping from admin_projects)
        await pool.request().query(`
            IF EXISTS (SELECT * FROM sys.views WHERE name='vw_Projects')
                DROP VIEW vw_Projects
        `);
        await pool.request().query(`
            CREATE VIEW vw_Projects AS
            SELECT 
                CAST(id AS VARCHAR(255)) as projectId,
                CAST(bim360_account_id AS VARCHAR(255)) as hubId,
                name as projectName,
                status,
                type as projectType,
                created_at as createdAt,
                updated_at as updatedAt,
                updated_at as lastSync
            FROM admin_projects
            WHERE name IS NOT NULL
        `);

        // Create simplified Issues view (mapping from issues_issues)
        await pool.request().query(`
            IF EXISTS (SELECT * FROM sys.views WHERE name='vw_Issues')
                DROP VIEW vw_Issues
        `);
        await pool.request().query(`
            CREATE VIEW vw_Issues AS
            SELECT 
                CAST(issue_id AS VARCHAR(255)) as issueId,
                CAST(bim360_project_id AS VARCHAR(255)) as projectId,
                title,
                description,
                status,
                'Normal' as priority,
                CAST(type_id AS VARCHAR(100)) as issueType,
                assignee_id as assignedTo,
                created_by as createdBy,
                created_at as createdAt,
                updated_at as updatedAt,
                due_date as dueDate,
                updated_at as lastSync
            FROM issues_issues
            WHERE title IS NOT NULL
        `);

        // Create simplified Files view (mapping from multiple document tables)
        await pool.request().query(`
            IF EXISTS (SELECT * FROM sys.views WHERE name='vw_Files')
                DROP VIEW vw_Files
        `);
        await pool.request().query(`
            CREATE VIEW vw_Files AS
            SELECT 
                CAST(NEWID() AS VARCHAR(255)) as fileId,
                'N/A' as projectId,
                'Document' as fileName,
                'pdf' as fileExtension,
                0 as fileSize,
                'Root' as folderName,
                '/' as folderPath,
                1 as version,
                0 as isModel,
                GETDATE() as createdAt,
                GETDATE() as modifiedAt,
                GETDATE() as lastSync
            WHERE 1=0  -- Empty view for now, will be populated when document tables are analyzed
        `);

        await pool.close();
        console.log('✅ Database views created successfully');

        res.json({
            success: true,
            message: '✅ Simplified ACC database views created successfully',
            viewsCreated: ['vw_Hubs', 'vw_Projects', 'vw_Issues', 'vw_Files'],
            database: dbConfig.database,
            description: 'Views map complex ACC tables to simplified structure',
            nextStep: 'Visit /test-views to verify views work, then use endpoints normally'
        });

    } catch (err) {
        console.error('❌ View creation failed:', err);
        res.status(500).json({
            error: 'Failed to create views',
            details: err.message,
            suggestion: 'Check database permissions and connection. Views require existing ACC data.'
        });
    }
});
*/

// Test the simplified views
app.get('/test-views', async (req, res) => {
    try {
        console.log('🧪 Testing simplified ACC views...');
        const pool = await sql.connect(dbConfig);

        // Test each view
        const hubsResult = await pool.request().query('SELECT COUNT(*) as count FROM vw_Hubs');
        const projectsResult = await pool.request().query('SELECT COUNT(*) as count FROM vw_Projects');
        const issuesResult = await pool.request().query('SELECT COUNT(*) as count FROM vw_Issues');
        const filesResult = await pool.request().query('SELECT COUNT(*) as count FROM vw_Files');

        // Get sample data
        const sampleHubs = await pool.request().query('SELECT TOP 3 * FROM vw_Hubs');
        const sampleProjects = await pool.request().query('SELECT TOP 3 * FROM vw_Projects');
        const sampleIssues = await pool.request().query('SELECT TOP 3 * FROM vw_Issues');

        await pool.close();
        console.log('✅ Views tested successfully');

        res.json({
            success: true,
            message: '✅ All simplified views are working',
            counts: {
                hubs: hubsResult.recordset[0].count,
                projects: projectsResult.recordset[0].count,
                issues: issuesResult.recordset[0].count,
                files: filesResult.recordset[0].count
            },
            samples: {
                hubs: sampleHubs.recordset,
                projects: sampleProjects.recordset,
                issues: sampleIssues.recordset
            },
            database: dbConfig.database,
            nextStep: 'Views are ready! Use /hubs, /projects, etc. endpoints normally'
        });

    } catch (err) {
        console.error('❌ View testing failed:', err);
        res.status(500).json({
            error: 'Failed to test views',
            details: err.message,
            suggestion: 'Make sure views are created first with /create-views'
        });
    }
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

// Test token with hubs API
app.get('/test-token', async (req, res) => {
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    try {
        console.log('🧪 Testing token with hubs API...');
        const response = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
        });

        console.log('✅ Token test successful');
        res.json({
            success: true,
            message: '✅ Token works! You can access Autodesk APIs',
            hubsFound: response.data.data.length,
            tokenValid: true
        });
    } catch (err) {
        console.error('❌ Token test failed:', err.response?.data?.developerMessage || err.message);
        res.status(500).json({
            error: 'Token test failed',
            details: err.response?.data?.developerMessage || err.message,
            suggestion: 'Check token validity or API permissions'
        });
    }
});

// Get ACC hubs
app.get('/hubs', async (req, res) => {
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    try {
        console.log('🏢 Fetching ACC hubs...');
        const response = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
        });

        const hubs = response.data.data.map(hub => ({
            id: hub.id,
            name: hub.attributes.name,
            region: hub.attributes.region,
            projectsLink: `http://localhost:3000/projects/${hub.id}`,
            accountId: hub.relationships?.account?.data?.id
        }));

        console.log(`✅ Found ${hubs.length} hubs`);
        res.json({
            success: true,
            hubsCount: hubs.length,
            hubs: hubs,
            nextStep: 'Click projectsLink to see projects in each hub'
        });
    } catch (err) {
        console.error('❌ Failed to fetch hubs:', err.response?.data || err.message);
        res.status(500).json({
            error: 'Failed to fetch hubs',
            details: err.response?.data || err.message
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

    const { hubId } = req.params;

    try {
        console.log(`📁 Fetching projects for hub: ${hubId}`);
        const response = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hubId}/projects`, {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
        });

        const projects = response.data.data.map(project => ({
            id: project.id,
            name: project.attributes.name,
            status: project.attributes.status,
            created: project.attributes.createdAt,
            updated: project.attributes.updatedAt,
            detailsLink: `http://localhost:3000/project-details/${hubId}/${project.id}`,
            issuesLink: `http://localhost:3000/project-issues/${hubId}/${project.id}`,
            filesLink: `http://localhost:3000/project-files/${hubId}/${project.id}`
        }));

        console.log(`✅ Found ${projects.length} projects in hub ${hubId}`);
        res.json({
            success: true,
            hubId: hubId,
            projectsCount: projects.length,
            projects: projects
        });
    } catch (err) {
        console.error(`❌ Failed to fetch projects for hub ${hubId}:`, err.response?.data || err.message);
        res.status(500).json({
            error: 'Failed to fetch projects',
            hubId: hubId,
            details: err.response?.data || err.message
        });
    }
});

// Test ACC API data fetching (without database)
app.get('/test-acc-api', async (req, res) => {
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first to get authentication'
        });
    }

    try {
        console.log('🧪 Testing ACC API data fetching...');
        
        // Step 1: Get ACC Hubs
        console.log('📡 Fetching hubs from ACC API...');
        const hubsResponse = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
        });

        let testResults = {
            hubs: [],
            projects: [],
            hubCount: hubsResponse.data.data.length
        };

        // Process first hub for testing
        if (hubsResponse.data.data.length > 0) {
            const firstHub = hubsResponse.data.data[0];
            testResults.hubs.push({
                id: firstHub.id,
                name: firstHub.attributes.name,
                region: firstHub.attributes.region
            });

            // Get projects for first hub
            console.log(`📡 Fetching projects for hub: ${firstHub.attributes.name}`);
            const projectsResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${firstHub.id}/projects`, {
                headers: { 'Authorization': `Bearer ${client_credentials_token}` }
            });

            testResults.projects = projectsResponse.data.data.map(project => ({
                id: project.id,
                name: project.attributes.name,
                status: project.attributes.status,
                created: project.attributes.createdAt,
                updated: project.attributes.updatedAt
            }));
        }

        console.log('✅ ACC API test completed successfully');
        res.json({
            success: true,
            message: '✅ ACC API data fetching works perfectly!',
            accApiStatus: 'Connected and working',
            testResults: testResults,
            nextStep: 'Fix database connection and run /sync-to-database for full automation'
        });

    } catch (err) {
        console.error('❌ ACC API test failed:', err);
        res.status(500).json({
            error: 'Failed to test ACC API',
            details: err.response?.data || err.message,
            suggestion: 'Check ACC API credentials and network connection'
        });
    }
});

// Sync ACC data from APIs to existing database schema
app.get('/sync-to-database', async (req, res) => {
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first to get authentication'
        });
    }

    try {
        console.log('🔄 Starting ACC data sync from APIs to database...');
        
        // Test database connection first
        const connected = await db.testConnection();
        if (!connected) {
            throw new Error('Database connection failed');
        }
        
        let syncStats = {
            accountsProcessed: 0,
            projectsProcessed: 0,
            issuesProcessed: 0,
            errors: []
        };

        // Step 1: Get ACC Hubs (which map to accounts)
        console.log('📡 Fetching hubs from ACC API...');
        const hubsResponse = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
        });

        for (const hub of hubsResponse.data.data) {
            try {
                // Insert/Update account using database helper
                const accountData = {
                    id: hub.id,
                    name: hub.attributes.name,
                    status: 'active',
                    created_at: new Date(),
                    updated_at: new Date()
                };

                // Use upsert logic via sqlcmd
                await db.executeNonQuery(`
                    IF EXISTS (SELECT 1 FROM admin_accounts WHERE bim360_account_id = '${hub.id}')
                        UPDATE admin_accounts 
                        SET display_name = '${hub.attributes.name.replace(/'/g, "''")}', end_date = NULL
                        WHERE bim360_account_id = '${hub.id}'
                    ELSE
                        INSERT INTO admin_accounts (bim360_account_id, display_name, start_date, end_date)
                        VALUES ('${hub.id}', '${hub.attributes.name.replace(/'/g, "''")}', GETDATE(), NULL)
                `);

                syncStats.accountsProcessed++;
                console.log(`✅ Synced account: ${hub.attributes.name}`);

                // Step 2: Get Projects for each Hub
                console.log(`📡 Fetching projects for hub: ${hub.attributes.name}`);
                const projectsResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hub.id}/projects`, {
                    headers: { 'Authorization': `Bearer ${client_credentials_token}` }
                });

                for (const project of projectsResponse.data.data) {
                    try {
                        // Insert/Update project using database helper
                        await db.executeNonQuery(`
                            IF EXISTS (SELECT 1 FROM admin_projects WHERE id = '${project.id}')
                                UPDATE admin_projects 
                                SET name = '${project.attributes.name.replace(/'/g, "''")}', 
                                    status = '${project.attributes.status || 'active'}', 
                                    updated_at = GETDATE()
                                WHERE id = '${project.id}'
                            ELSE
                                INSERT INTO admin_projects (id, bim360_account_id, name, status, type, created_at, updated_at)
                                VALUES ('${project.id}', '${hub.id}', '${project.attributes.name.replace(/'/g, "''")}', 
                                       '${project.attributes.status || 'active'}', '${project.attributes.projectType || 'Unknown'}', 
                                       GETDATE(), GETDATE())
                        `);

                        syncStats.projectsProcessed++;
                        console.log(`✅ Synced project: ${project.attributes.name}`);

                    } catch (projectErr) {
                        syncStats.errors.push(`Project ${project.id}: ${projectErr.message}`);
                        console.error(`❌ Failed to sync project: ${projectErr.message}`);
                    }
                }

            } catch (hubErr) {
                syncStats.errors.push(`Hub ${hub.id}: ${hubErr.message}`);
                console.error(`❌ Failed to sync hub: ${hubErr.message}`);
            }
        }

        console.log('✅ ACC data sync completed from APIs to database');
        res.json({
            success: true,
            message: '✅ ACC data sync completed - Database updated with latest API data',
            database: 'acc_data_schema',
            method: 'sqlcmd via DatabaseHelper',
            syncStats: syncStats,
            totalProcessed: {
                accounts: syncStats.accountsProcessed,
                projects: syncStats.projectsProcessed,
                errors: syncStats.errors.length
            },
            nextSteps: [
                'Visit /test-views to see updated data',
                'Use /power-bi-summary for reporting',
                'Check database directly via SQL Management Studio'
            ]
        });

    } catch (err) {
        console.error('❌ Sync failed:', err);
        res.status(500).json({
            error: 'ACC data sync failed',
            details: err.message,
            suggestion: 'Check database connection and ACC API credentials'
        });
    }
});

// Power BI summary endpoint
app.get('/power-bi-summary', async (req, res) => {
    try {
        console.log('📊 Generating Power BI summary...');
        const pool = await sql.connect(dbConfig);

        // Get summary statistics
        const hubCount = await pool.request().query('SELECT COUNT(*) as count FROM vw_Hubs');
        const projectCount = await pool.request().query('SELECT COUNT(*) as count FROM vw_Projects');
        const issueCount = await pool.request().query('SELECT COUNT(*) as count FROM vw_Issues');
        const activeProjects = await pool.request().query("SELECT COUNT(*) as count FROM vw_Projects WHERE status = 'active'");

        // Get recent projects
        const recentProjects = await pool.request().query(`
            SELECT TOP 10 h.hubName, p.projectName, p.status, p.updatedAt
            FROM vw_Projects p
            LEFT JOIN vw_Hubs h ON p.hubId = h.hubId
            ORDER BY p.updatedAt DESC
        `);

        // Get project status breakdown
        const statusBreakdown = await pool.request().query(`
            SELECT status, COUNT(*) as count
            FROM vw_Projects
            WHERE status IS NOT NULL
            GROUP BY status
            ORDER BY count DESC
        `);

        // Get issues summary
        const issueStatusBreakdown = await pool.request().query(`
            SELECT status, COUNT(*) as count
            FROM vw_Issues
            WHERE status IS NOT NULL
            GROUP BY status
            ORDER BY count DESC
        `);

        await pool.close();

        console.log('✅ Power BI summary generated from simplified views');
        res.json({
            success: true,
            powerBiSummary: {
                overview: {
                    totalHubs: hubCount.recordset[0].count,
                    totalProjects: projectCount.recordset[0].count,
                    totalIssues: issueCount.recordset[0].count,
                    activeProjects: activeProjects.recordset[0].count
                },
                recentActivity: {
                    recentProjects: recentProjects.recordset
                },
                projectStatusBreakdown: statusBreakdown.recordset,
                issueStatusBreakdown: issueStatusBreakdown.recordset,
                lastDataSync: new Date().toISOString()
            },
            database: {
                server: dbConfig.server,
                database: dbConfig.database,
                views: ['vw_Hubs', 'vw_Projects', 'vw_Issues', 'vw_Files'],
                description: 'Using simplified views over complex ACC database tables'
            },
            powerBiConnection: {
                dataSource: dbConfig.server,
                database: dbConfig.database,
                authentication: 'SQL Server Authentication',
                username: dbConfig.user,
                recommendedTables: ['vw_Hubs', 'vw_Projects', 'vw_Issues', 'vw_Files']
            }
        });

    } catch (err) {
        console.error('❌ Power BI summary failed:', err);
        res.status(500).json({
            error: 'Failed to generate Power BI summary',
            details: err.message,
            database: dbConfig.database
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
    console.log(`✅ Database: acc_data_schema on P-NB-USER-028\\SQLEXPRESS (via sqlcmd)`);
    console.log(`👉 Visit http://localhost:${PORT}/test-database to verify SQL connection`);
    console.log(`🚀 Full workflow: /login-2legged → /test-database → /sync-to-database → /create-views`);
    console.log(`🤖 AUTOMATION: Replaces manual ACC data extraction with API automation`);
});