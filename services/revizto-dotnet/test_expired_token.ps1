# Test Expired Token Scenario
Write-Host "=== TESTING EXPIRED TOKEN SCENARIO ===" -ForegroundColor Cyan

# Backup current config
Write-Host "Backing up current configuration..." -ForegroundColor Yellow
Copy-Item appsettings.json appsettings.json.backup

try {
    # Load current config
    $config = Get-Content appsettings.json | ConvertFrom-Json
    
    # Create an expired token (expired 1 hour ago)
    $expiredTime = [DateTimeOffset]::UtcNow.AddHours(-1).ToUnixTimeSeconds()
    
    # Create JWT components
    $header = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"typ":"JWT","alg":"RS256"}')) -replace '=',''
    $payload = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("{`"sub`":`"test@example.com`",`"exp`":$expiredTime}")) -replace '=',''
    $signature = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('dummy-signature')) -replace '=',''
    $expiredToken = "$header.$payload.$signature"
    
    Write-Host "Created expired token (expired 1 hour ago)" -ForegroundColor Yellow
    
    # Update config with expired token
    $config.ReviztoAPI.AccessToken = $expiredToken
    $config | ConvertTo-Json -Depth 10 | Set-Content appsettings.json
    
    Write-Host "Updated configuration with expired token" -ForegroundColor Yellow
    
    # Verify the expired token
    Write-Host "`nAnalyzing expired token..." -ForegroundColor White
    & .\analyze_token.ps1
    
    Write-Host "`nTesting application with expired token..." -ForegroundColor White
    $output = & .\bin\Release\net9.0-windows\win-x64\ReviztoDataExporter.exe list-projects 2>&1
    $exitCode = $LASTEXITCODE
    
    Write-Host "Exit Code: $exitCode" -ForegroundColor $(if ($exitCode -eq 0) { "Green" } else { "Red" })
    Write-Host "Output:" -ForegroundColor White
    Write-Host $output -ForegroundColor Gray
    
    # Check for specific indicators
    if ($output -match "401" -or $output -match "Unauthorized") {
        Write-Host "⚠️ 401 Unauthorized detected - expired token correctly identified" -ForegroundColor Yellow
    }
    
    if ($output -match "refresh" -or $output -match "Refresh") {
        Write-Host "✅ Token refresh activity detected" -ForegroundColor Green
    }
    
    if ($output -match "success.*true") {
        Write-Host "✅ API call succeeded - token may have been refreshed automatically" -ForegroundColor Green
    }
    
    Write-Host "`nChecking if token was updated in configuration..." -ForegroundColor White
    $updatedConfig = Get-Content appsettings.json | ConvertFrom-Json
    if ($updatedConfig.ReviztoAPI.AccessToken -ne $expiredToken) {
        Write-Host "✅ Token was updated in configuration - automatic refresh worked!" -ForegroundColor Green
        Write-Host "Analyzing new token..." -ForegroundColor White
        & .\analyze_token.ps1
    } else {
        Write-Host "⚠️ Token was not updated - manual refresh may be needed" -ForegroundColor Yellow
    }
    
}
finally {
    # Always restore original config
    Write-Host "`nRestoring original configuration..." -ForegroundColor Yellow
    Copy-Item appsettings.json.backup appsettings.json
    Remove-Item appsettings.json.backup
    Write-Host "✅ Configuration restored" -ForegroundColor Green
}

Write-Host "`n=== TEST COMPLETE ===" -ForegroundColor Cyan