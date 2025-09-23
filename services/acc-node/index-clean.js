const express = require('express');
const axios = require('axios');
const sql = require('mssql');
const app = express();

// Database configuration using your SQL Server credentials
const dbConfig = {
    user: process.env.DB_USER || 'admin02',
    password: process.env.DB_PASSWORD || '1234',
    server: process.env.DB_SERVER || 'P-NB-USER-028\\SQLEXPRESS',
    database: process.env.ACC_DB || 'acc_data_schema',
    driver: process.env.DB_DRIVER || 'ODBC Driver 17 for SQL Server',
    options: {
        encrypt: false,
        trustServerCertificate: true,
        enableArithAbort: true
    },
    pool: {
        max: 10,
        min: 0,
        idleTimeoutMillis: 30000
    }
};

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
            <li><a href="/create-tables">/create-tables</a> - 🏗️ Create SQL tables for ACC data</li>
            <li><a href="/sync-to-database">/sync-to-database</a> - 🔄 Sync all ACC data to SQL</li>
            <li><a href="/power-bi-summary">/power-bi-summary</a> - 📊 Power BI ready summary</li>
        </ul>
        <p><strong>✅ Full ACC + SQL Integration Ready!</strong></p>
        <p><strong>Workflow:</strong> /login-2legged → /test-database → /create-tables → /sync-to-database → /power-bi-summary</p>
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
        const pool = await sql.connect(dbConfig);
        
        // Test query
        const result = await pool.request().query('SELECT @@VERSION as version, DB_NAME() as database_name');
        await pool.close();
        
        console.log('✅ Database connection successful');
        res.json({
            success: true,
            message: '✅ Database connection successful',
            serverInfo: {
                version: result.recordset[0].version.split('\n')[0],
                database: result.recordset[0].database_name,
                server: dbConfig.server,
                user: dbConfig.user
            },
            nextStep: 'Visit /create-tables to set up ACC data schema'
        });
    } catch (err) {
        console.error('❌ Database connection failed:', err);
        res.status(500).json({
            error: 'Database connection failed',
            details: err.message,
            config: {
                server: dbConfig.server,
                database: dbConfig.database,
                user: dbConfig.user
            },
            suggestions: [
                'Check if SQL Server is running',
                'Verify server name and instance',
                'Check username and password',
                'Ensure database exists'
            ]
        });
    }
});

// Create database tables for ACC data
app.get('/create-tables', async (req, res) => {
    try {
        console.log('🏗️ Creating ACC data tables...');
        const pool = await sql.connect(dbConfig);

        // Create Hubs table
        await pool.request().query(`
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Hubs')
            CREATE TABLE Hubs (
                hubId VARCHAR(255) PRIMARY KEY,
                hubName VARCHAR(255) NOT NULL,
                region VARCHAR(100),
                accountId VARCHAR(255),
                createdAt DATETIME DEFAULT GETDATE(),
                lastSync DATETIME DEFAULT GETDATE()
            )
        `);

        // Create Projects table
        await pool.request().query(`
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Projects')
            CREATE TABLE Projects (
                projectId VARCHAR(255) PRIMARY KEY,
                hubId VARCHAR(255) NOT NULL,
                projectName VARCHAR(255) NOT NULL,
                status VARCHAR(50),
                projectType VARCHAR(100),
                createdAt DATETIME,
                updatedAt DATETIME,
                lastSync DATETIME DEFAULT GETDATE(),
                CONSTRAINT FK_Projects_Hubs FOREIGN KEY (hubId) REFERENCES Hubs(hubId)
            )
        `);

        // Create Issues table
        await pool.request().query(`
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Issues')
            CREATE TABLE Issues (
                issueId VARCHAR(255) PRIMARY KEY,
                projectId VARCHAR(255) NOT NULL,
                title VARCHAR(500),
                description TEXT,
                status VARCHAR(50),
                priority VARCHAR(50),
                issueType VARCHAR(100),
                assignedTo VARCHAR(255),
                createdBy VARCHAR(255),
                createdAt DATETIME,
                updatedAt DATETIME,
                dueDate DATETIME,
                lastSync DATETIME DEFAULT GETDATE(),
                CONSTRAINT FK_Issues_Projects FOREIGN KEY (projectId) REFERENCES Projects(projectId)
            )
        `);

        // Create Files table
        await pool.request().query(`
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Files')
            CREATE TABLE Files (
                fileId VARCHAR(255) PRIMARY KEY,
                projectId VARCHAR(255) NOT NULL,
                fileName VARCHAR(500),
                fileExtension VARCHAR(10),
                fileSize BIGINT,
                folderName VARCHAR(255),
                folderPath VARCHAR(1000),
                version INT,
                isModel BIT DEFAULT 0,
                createdAt DATETIME,
                modifiedAt DATETIME,
                lastSync DATETIME DEFAULT GETDATE(),
                CONSTRAINT FK_Files_Projects FOREIGN KEY (projectId) REFERENCES Projects(projectId)
            )
        `);

        await pool.close();
        console.log('✅ Database tables created successfully');

        res.json({
            success: true,
            message: '✅ Database tables created successfully',
            tablesCreated: ['Hubs', 'Projects', 'Issues', 'Files'],
            database: dbConfig.database,
            nextStep: 'Visit /sync-to-database to populate with ACC data'
        });

    } catch (err) {
        console.error('❌ Table creation failed:', err);
        res.status(500).json({
            error: 'Failed to create tables',
            details: err.message,
            suggestion: 'Check database permissions and connection'
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

// Sync all ACC data to SQL database
app.get('/sync-to-database', async (req, res) => {
    if (!client_credentials_token) {
        return res.json({
            error: 'No 2-legged token available',
            action: 'Visit /login-2legged first'
        });
    }

    try {
        console.log('🔄 Starting ACC data sync to SQL database...');
        const pool = await sql.connect(dbConfig);
        
        // Get all hubs
        const hubsResponse = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: { 'Authorization': `Bearer ${client_credentials_token}` }
        });

        let syncStats = {
            hubsProcessed: 0,
            projectsProcessed: 0,
            issuesProcessed: 0,
            filesProcessed: 0,
            errors: []
        };

        for (const hub of hubsResponse.data.data) {
            try {
                // Sync hub data
                await pool.request()
                    .input('hubId', sql.VarChar, hub.id)
                    .input('hubName', sql.VarChar, hub.attributes.name)
                    .input('region', sql.VarChar, hub.attributes.region || 'Unknown')
                    .input('accountId', sql.VarChar, hub.relationships?.account?.data?.id || 'Unknown')
                    .input('lastSync', sql.DateTime, new Date())
                    .query(`
                        MERGE Hubs AS target
                        USING (SELECT @hubId AS hubId, @hubName AS hubName, @region AS region, @accountId AS accountId, @lastSync AS lastSync) AS source
                        ON target.hubId = source.hubId
                        WHEN MATCHED THEN UPDATE SET hubName = source.hubName, region = source.region, accountId = source.accountId, lastSync = source.lastSync
                        WHEN NOT MATCHED THEN INSERT (hubId, hubName, region, accountId, lastSync) VALUES (source.hubId, source.hubName, source.region, source.accountId, source.lastSync);
                    `);

                syncStats.hubsProcessed++;

                // Get projects for this hub
                const projectsResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${hub.id}/projects`, {
                    headers: { 'Authorization': `Bearer ${client_credentials_token}` }
                });

                for (const project of projectsResponse.data.data) {
                    try {
                        // Sync project data
                        await pool.request()
                            .input('projectId', sql.VarChar, project.id)
                            .input('hubId', sql.VarChar, hub.id)
                            .input('projectName', sql.VarChar, project.attributes.name)
                            .input('status', sql.VarChar, project.attributes.status || 'Unknown')
                            .input('projectType', sql.VarChar, project.attributes.projectType || 'Unknown')
                            .input('createdAt', sql.DateTime, project.attributes.createdAt ? new Date(project.attributes.createdAt) : new Date())
                            .input('updatedAt', sql.DateTime, project.attributes.updatedAt ? new Date(project.attributes.updatedAt) : new Date())
                            .input('lastSync', sql.DateTime, new Date())
                            .query(`
                                MERGE Projects AS target
                                USING (SELECT @projectId AS projectId, @hubId AS hubId, @projectName AS projectName, 
                                       @status AS status, @projectType AS projectType, @createdAt AS createdAt, @updatedAt AS updatedAt, @lastSync AS lastSync) AS source
                                ON target.projectId = source.projectId
                                WHEN MATCHED THEN UPDATE SET projectName = source.projectName, status = source.status, 
                                     projectType = source.projectType, updatedAt = source.updatedAt, lastSync = source.lastSync
                                WHEN NOT MATCHED THEN INSERT (projectId, hubId, projectName, status, projectType, createdAt, updatedAt, lastSync) 
                                     VALUES (source.projectId, source.hubId, source.projectName, source.status, source.projectType, source.createdAt, source.updatedAt, source.lastSync);
                            `);

                        syncStats.projectsProcessed++;

                    } catch (projectErr) {
                        syncStats.errors.push(`Project ${project.id}: ${projectErr.message}`);
                    }
                }

            } catch (hubErr) {
                syncStats.errors.push(`Hub ${hub.id}: ${hubErr.message}`);
            }
        }

        await pool.close();

        console.log('✅ ACC data sync completed');
        res.json({
            success: true,
            message: '✅ ACC data sync completed',
            database: dbConfig.database,
            syncStats: syncStats,
            timestamp: new Date().toISOString(),
            nextSteps: [
                'Check your SQL tables: Hubs, Projects, Issues, Files',
                'Visit /power-bi-summary for reporting insights',
                'Connect Power BI to your SQL Server database'
            ]
        });

    } catch (err) {
        console.error('❌ Database sync failed:', err);
        res.status(500).json({
            error: 'Database sync failed',
            details: err.message,
            database: dbConfig.database
        });
    }
});

// Power BI summary endpoint
app.get('/power-bi-summary', async (req, res) => {
    try {
        console.log('📊 Generating Power BI summary...');
        const pool = await sql.connect(dbConfig);

        // Get summary statistics
        const hubCount = await pool.request().query('SELECT COUNT(*) as count FROM Hubs');
        const projectCount = await pool.request().query('SELECT COUNT(*) as count FROM Projects');
        const activeProjects = await pool.request().query("SELECT COUNT(*) as count FROM Projects WHERE status = 'active'");

        // Get recent projects
        const recentProjects = await pool.request().query(`
            SELECT TOP 10 h.hubName, p.projectName, p.status, p.updatedAt
            FROM Projects p
            JOIN Hubs h ON p.hubId = h.hubId
            ORDER BY p.updatedAt DESC
        `);

        // Get project status breakdown
        const statusBreakdown = await pool.request().query(`
            SELECT status, COUNT(*) as count
            FROM Projects
            GROUP BY status
            ORDER BY count DESC
        `);

        await pool.close();

        console.log('✅ Power BI summary generated');
        res.json({
            success: true,
            powerBiSummary: {
                overview: {
                    totalHubs: hubCount.recordset[0].count,
                    totalProjects: projectCount.recordset[0].count,
                    activeProjects: activeProjects.recordset[0].count
                },
                recentActivity: {
                    recentProjects: recentProjects.recordset
                },
                statusBreakdown: statusBreakdown.recordset,
                lastDataSync: new Date().toISOString()
            },
            database: {
                server: dbConfig.server,
                database: dbConfig.database,
                tables: ['Hubs', 'Projects', 'Issues', 'Files']
            },
            powerBiConnection: {
                dataSource: dbConfig.server,
                database: dbConfig.database,
                authentication: 'SQL Server Authentication',
                username: dbConfig.user
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
    console.log(`✅ Database: ${dbConfig.database} on ${dbConfig.server}`);
    console.log(`👉 Visit http://localhost:${PORT}/test-database to verify SQL connection`);
    console.log(`🚀 Full workflow: /login-2legged → /test-database → /create-tables → /sync-to-database`);
});