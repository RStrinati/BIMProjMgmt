const DatabaseHelper = require('./database-helper');

async function testDatabaseHelper() {
    console.log('🚀 Testing Database Helper with sqlcmd approach...');
    
    const db = new DatabaseHelper();
    
    // Test connection
    const connected = await db.testConnection();
    if (!connected) {
        console.error('❌ Database connection failed');
        return;
    }
    
    // Test project count
    console.log('📊 Getting project count...');
    const projectCount = await db.getProjectCount();
    console.log(`✅ Found ${projectCount} projects in database`);
    
    console.log('🎉 Database Helper test completed successfully!');
}

testDatabaseHelper().catch(console.error);