const sql = require('mssql');

// Database configuration - using named pipes
const dbConfig = {
    user: 'admin02',
    password: '1234',
    server: 'np:\\\\.\\pipe\\MSSQL$SQLEXPRESS\\sql\\query',
    database: 'acc_data_schema',
    options: {
        encrypt: false,
        trustServerCertificate: true,
        enableArithAbort: true,
        useUTC: false,
        connectTimeout: 30000,
        requestTimeout: 30000
    },
    pool: {
        max: 10,
        min: 0,
        idleTimeoutMillis: 30000
    }
};

async function testDatabaseConnection() {
    try {
        console.log('🔌 Testing Node.js database connection...');
        console.log('Configuration:', {
            server: dbConfig.server,
            database: dbConfig.database,
            user: dbConfig.user,
            instanceName: dbConfig.options.instanceName
        });
        
        console.log('📡 Connecting to SQL Server...');
        const pool = await sql.connect(dbConfig);
        
        console.log('✅ Connected successfully!');
        
        console.log('🧪 Running test query...');
        const result = await pool.request().query('SELECT GETDATE() as CurrentTime, @@SERVERNAME as ServerName, DB_NAME() as DatabaseName');
        
        console.log('✅ Test query results:');
        console.log(result.recordset[0]);
        
        console.log('📊 Testing project count...');
        const projectCount = await pool.request().query('SELECT COUNT(*) as count FROM admin_projects');
        console.log(`✅ Found ${projectCount.recordset[0].count} projects in database`);
        
        await pool.close();
        console.log('✅ Database connection test SUCCESSFUL!');
        
    } catch (error) {
        console.error('❌ Database connection failed:');
        console.error('Error details:', error.message);
        console.error('Error code:', error.code);
        
        if (error.code === 'ETIMEOUT') {
            console.log('💡 Suggestions for timeout issues:');
            console.log('   1. Check if SQL Server Browser service is running');
            console.log('   2. Verify SQL Server is configured to accept TCP/IP connections');
            console.log('   3. Check Windows Firewall settings');
            console.log('   4. Try using port 1433 explicitly');
        }
    }
}

// Run the test
testDatabaseConnection();