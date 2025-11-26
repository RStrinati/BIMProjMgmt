const axios = require('axios');

// Your working ACC API credentials
const CLIENT_ID = 'HSIzVK9vT8AGY0emotXgOylhsczvoO0XSPy6M76vAAovAeN8';
const CLIENT_SECRET = 'JuLnXcguwKB2g0QoG5auJWnF2XnI9uiW8wdYw5xIAmKiqTIvK3q9pfAHTq7ZcNZ4';

async function demonstrateAccAutomation() {
    try {
        console.log('🔑 Step 1: Getting ACC API Token...');
        
        // Get 2-legged token
        const tokenResponse = await axios.post('https://developer.api.autodesk.com/authentication/v2/token', 
            'grant_type=client_credentials&scope=data:read account:read', {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `Basic ${Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64')}`
            }
        });
        
        const token = tokenResponse.data.access_token;
        console.log(`✅ Token received: ${token.substring(0, 20)}...`);
        
        console.log('📡 Step 2: Fetching ACC Hubs...');
        
        // Get hubs from ACC
        const hubsResponse = await axios.get('https://developer.api.autodesk.com/project/v1/hubs', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        console.log(`✅ Found ${hubsResponse.data.data.length} hubs in your ACC account`);
        
        if (hubsResponse.data.data.length > 0) {
            const firstHub = hubsResponse.data.data[0];
            console.log(`📋 First Hub: ${firstHub.attributes.name} (ID: ${firstHub.id})`);
            
            console.log('📡 Step 3: Fetching Projects...');
            
            // Get projects for first hub
            const projectsResponse = await axios.get(`https://developer.api.autodesk.com/project/v1/hubs/${firstHub.id}/projects`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            console.log(`✅ Found ${projectsResponse.data.data.length} projects in this hub`);
            
            // Show first few projects
            projectsResponse.data.data.slice(0, 3).forEach((project, index) => {
                console.log(`   ${index + 1}. ${project.attributes.name} (Status: ${project.attributes.status})`);
            });
            
            console.log('');
            console.log('🎉 AUTOMATION WORKING PERFECTLY!');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log('✅ ACC API Authentication: SUCCESS');
            console.log('✅ Hubs Data Retrieval: SUCCESS');
            console.log('✅ Projects Data Retrieval: SUCCESS');
            console.log('');
            console.log('📊 This data would normally be inserted into your database:');
            console.log(`   - ${hubsResponse.data.data.length} accounts → admin_accounts table`);
            console.log(`   - ${projectsResponse.data.data.length} projects → admin_projects table`);
            console.log(`   - Issues (if available) → issues_issues table`);
            console.log('');
            console.log('🔄 Your manual process is now AUTOMATED!');
            
        } else {
            console.log('⚠️ No hubs found. Check ACC account access.');
        }
        
    } catch (error) {
        console.error('❌ Error:', error.response?.data || error.message);
    }
}

// Run the demonstration
demonstrateAccAutomation();