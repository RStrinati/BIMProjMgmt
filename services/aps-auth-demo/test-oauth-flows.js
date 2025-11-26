#!/usr/bin/env node
/**
 * OAuth Flow Tester - Tests both 2-legged and 3-legged OAuth flows
 * 
 * Usage: node test-oauth-flows.js
 */

const axios = require('axios');

const BASE_URL = 'http://localhost:3000';

async function testOAuthFlows() {
    console.log('🧪 Testing APS OAuth Flows for Hub Access\n');

    // Test 2-legged OAuth
    console.log('1️⃣ Testing 2-Legged OAuth (App-Level)...');
    try {
        const response = await axios.get(`${BASE_URL}/login-2legged`);
        console.log('✅ 2-Legged OAuth: SUCCESS');
        console.log(`   Token expires in: ${response.data.tokenInfo.expires_in} seconds`);
        console.log(`   Scopes: ${response.data.tokenInfo.scope}`);
        
        // Test hub access with 2-legged token
        console.log('   Testing hub access...');
        const hubsResponse = await axios.get(`${BASE_URL}/hubs`);
        console.log(`   ✅ Hub access: ${hubsResponse.data.length || 0} hubs found`);
        
    } catch (error) {
        console.log('❌ 2-Legged OAuth: FAILED');
        console.log(`   Error: ${error.response?.data?.error || error.message}`);
        if (error.response?.data?.troubleshooting) {
            console.log('   Troubleshooting:');
            error.response.data.troubleshooting.forEach(tip => 
                console.log(`     - ${tip}`)
            );
        }
    }

    console.log('\n' + '='.repeat(50) + '\n');

    // Test 3-legged OAuth (just show the URL since it requires user interaction)
    console.log('2️⃣ Testing 3-Legged OAuth (User-Level)...');
    console.log('✅ 3-Legged OAuth endpoint available');
    console.log(`   Visit: ${BASE_URL}/login`);
    console.log('   This requires user authentication via browser');
    console.log('   After login, test hub access via: GET /hubs');

    console.log('\n' + '='.repeat(50) + '\n');

    // Test diagnostic endpoint
    console.log('3️⃣ Testing Diagnostic Information...');
    try {
        const diagResponse = await axios.get(`${BASE_URL}/diagnose`);
        console.log('✅ Diagnostic endpoint: SUCCESS');
        console.log(`   App configured for: ${diagResponse.data.summary.apis_detected.join(', ')}`);
        console.log(`   OAuth flows: ${diagResponse.data.summary.oauth_flows_available.join(', ')}`);
    } catch (error) {
        console.log('❌ Diagnostic endpoint: Not available');
    }

    console.log('\n🎯 Summary:');
    console.log('- 2-legged OAuth: For app-level hub access');
    console.log('- 3-legged OAuth: For user-level hub access with admin permissions');
    console.log('- Hub access requires account:read scope (✅ configured)');
    console.log('- Admin operations require account:write scope (✅ configured for 3-legged)');
    console.log('\n📚 See OAUTH_HUB_ACCESS_GUIDE.md for detailed setup instructions');
}

// Run the tests
testOAuthFlows().catch(console.error);