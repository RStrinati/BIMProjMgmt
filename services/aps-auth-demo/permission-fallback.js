// Alternative authentication approach for restricted environments
// Add this endpoint to handle user-based authentication for additional permissions

app.get('/login-3legged', (req, res) => {
    // 3-legged OAuth provides user-level permissions which may bypass some integration restrictions
    const authUrl = `https://developer.api.autodesk.com/authentication/v2/authorize?` +
        `response_type=code&` +
        `client_id=${CLIENT_ID}&` +
        `redirect_uri=${encodeURIComponent(REDIRECT_URI)}&` +
        `scope=${encodeURIComponent('data:read account:read viewables:read')}`;
    
    res.json({
        message: 'Use this for user-based authentication if 2-legged fails',
        authUrl: authUrl,
        instructions: [
            'Click the authUrl to authenticate as a user',
            'User permissions may provide access to restricted APIs',
            'Useful when app-level integration permissions are denied'
        ]
    });
});

app.get('/callback', async (req, res) => {
    const { code } = req.query;
    if (!code) {
        return res.status(400).json({ error: 'No authorization code received' });
    }

    try {
        // Exchange code for user token
        const response = await axios.post('https://developer.api.autodesk.com/authentication/v2/token', {
            grant_type: 'authorization_code',
            code: code,
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET,
            redirect_uri: REDIRECT_URI
        });

        access_token = response.data.access_token;
        
        res.json({
            success: true,
            message: 'User authentication successful',
            token_type: '3-legged (user-based)',
            note: 'This may provide access to APIs restricted for app-only authentication'
        });
    } catch (err) {
        res.status(500).json({
            error: 'Failed to exchange authorization code',
            details: err.response?.data || err.message
        });
    }
});