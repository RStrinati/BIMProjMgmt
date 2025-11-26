# Token Refresh Workflow Diagnostic Script
# This script monitors and analyzes the token refresh process

param(
    [string]$ConfigPath = "appsettings.json",
    [switch]$Monitor,
    [switch]$TestExpiredScenario
)

function Write-ColorOutput($Text, $Color = "White") {
    Write-Host $Text -ForegroundColor $Color
}

function Get-TokenInfo($Token) {
    if ([string]::IsNullOrEmpty($Token)) {
        return $null
    }
    
    try {
        $parts = $Token.Split('.')
        if ($parts.Length -ne 3) {
            return @{ Error = "Invalid JWT format" }
        }
        
        # Decode payload
        $payload = $parts[1]
        
        # Add padding if necessary
        $padding = 4 - ($payload.Length % 4)
        if ($padding -ne 4) {
            $payload += "=" * $padding
        }
        
        $decodedBytes = [System.Convert]::FromBase64String($payload)
        $payloadJson = [System.Text.Encoding]::UTF8.GetString($decodedBytes)
        $payloadObj = $payloadJson | ConvertFrom-Json
        
        $exp = $null
        if ($payloadObj.exp) {
            if ($payloadObj.exp -is [decimal] -or $payloadObj.exp -is [double]) {
                $exp = [DateTimeOffset]::FromUnixTimeSeconds([long]$payloadObj.exp)
            } else {
                $exp = [DateTimeOffset]::FromUnixTimeSeconds([long]$payloadObj.exp)
            }
        }
        
        return @{
            Subject = $payloadObj.sub
            Expiry = $exp
            IssuedAt = if ($payloadObj.iat) { [DateTimeOffset]::FromUnixTimeSeconds($payloadObj.iat) } else { $null }
            Audience = $payloadObj.aud
            Scopes = $payloadObj.scope
            TimeToExpiry = if ($exp) { $exp - [DateTimeOffset]::UtcNow } else { $null }
            IsExpired = if ($exp) { [DateTimeOffset]::UtcNow -gt $exp } else { $true }
            NeedsRefresh = if ($exp) { ([DateTimeOffset]::UtcNow.AddMinutes(5)) -gt $exp } else { $true }
        }
    }
    catch {
        return @{ Error = $_.Exception.Message }
    }
}

function Analyze-CurrentConfig {
    Write-ColorOutput "`n=== CONFIGURATION ANALYSIS ===" "Cyan"
    
    if (-not (Test-Path $ConfigPath)) {
        Write-ColorOutput "ERROR: Configuration file not found: $ConfigPath" "Red"
        return
    }
    
    try {
        $config = Get-Content $ConfigPath | ConvertFrom-Json
        $apiConfig = $config.ReviztoAPI
        
        if (-not $apiConfig) {
            Write-ColorOutput "ERROR: ReviztoAPI section not found in configuration" "Red"
            return
        }
        
        Write-ColorOutput "Configuration File: $ConfigPath" "White"
        Write-ColorOutput "Base URL: $($apiConfig.BaseUrl)" "White"
        Write-ColorOutput "Has Access Token: $(-not [string]::IsNullOrEmpty($apiConfig.AccessToken))" "White"
        Write-ColorOutput "Has Refresh Token: $(-not [string]::IsNullOrEmpty($apiConfig.RefreshToken))" "White"
        
        if ($apiConfig.AccessToken) {
            Write-ColorOutput "`n--- ACCESS TOKEN ANALYSIS ---" "Yellow"
            $tokenInfo = Get-TokenInfo $apiConfig.AccessToken
            
            if ($tokenInfo.Error) {
                Write-ColorOutput "ERROR: $($tokenInfo.Error)" "Red"
            } else {
                Write-ColorOutput "Subject: $($tokenInfo.Subject)" "White"
                Write-ColorOutput "Expires: $($tokenInfo.Expiry.ToString('yyyy-MM-dd HH:mm:ss UTC'))" "White"
                
                if ($tokenInfo.TimeToExpiry) {
                    $timeStr = "{0:d\:hh\:mm\:ss}" -f $tokenInfo.TimeToExpiry
                    $color = if ($tokenInfo.IsExpired) { "Red" } elseif ($tokenInfo.NeedsRefresh) { "Yellow" } else { "Green" }
                    Write-ColorOutput "Time to Expiry: $timeStr" $color
                }
                
                Write-ColorOutput "Status: $(if ($tokenInfo.IsExpired) { 'EXPIRED' } elseif ($tokenInfo.NeedsRefresh) { 'NEEDS REFRESH' } else { 'VALID' })" $(if ($tokenInfo.IsExpired) { "Red" } elseif ($tokenInfo.NeedsRefresh) { "Yellow" } else { "Green" })
                
                if ($tokenInfo.Scopes) {
                    Write-ColorOutput "Scopes: $($tokenInfo.Scopes)" "White"
                }
            }
        }
        
        return $apiConfig
    }
    catch {
        Write-ColorOutput "ERROR: Failed to parse configuration: $($_.Exception.Message)" "Red"
        return $null
    }
}

function Test-TokenRefreshWorkflow {
    Write-ColorOutput "`n=== TOKEN REFRESH WORKFLOW TEST ===" "Cyan"
    
    # Check if the executable exists
    $exePath = "ReviztoDataExporter.exe"
    if (-not (Test-Path $exePath)) {
        $exePath = "bin\Release\net9.0-windows\win-x64\ReviztoDataExporter.exe"
        if (-not (Test-Path $exePath)) {
            $exePath = "bin\Debug\net9.0-windows\win-x64\ReviztoDataExporter.exe"
            if (-not (Test-Path $exePath)) {
                Write-ColorOutput "ERROR: ReviztoDataExporter.exe not found in expected locations" "Red"
                Write-ColorOutput "Searched: .\ReviztoDataExporter.exe, .\bin\Release\net9.0-windows\win-x64\ReviztoDataExporter.exe, .\bin\Debug\net9.0-windows\win-x64\ReviztoDataExporter.exe" "Gray"
                return
            }
        }
    }
    
    Write-ColorOutput "Found executable: $exePath" "White"
    
    # Test with a simple command that should trigger token validation
    Write-ColorOutput "Testing token validation by attempting to list projects..." "White"
    
    try {
        $result = & $exePath list-projects 2>&1
        $exitCode = $LASTEXITCODE
        
        Write-ColorOutput "Exit Code: $exitCode" $(if ($exitCode -eq 0) { "Green" } else { "Red" })
        Write-ColorOutput "Output:" "White"
        Write-ColorOutput $result "Gray"
        
        if ($result -match "401" -or $result -match "Unauthorized") {
            Write-ColorOutput "WARNING: 401 Unauthorized detected - token may be invalid" "Yellow"
        }
        
        if ($result -match "Token refreshed" -or $result -match "refresh") {
            Write-ColorOutput "INFO: Token refresh activity detected" "Green"
        }
    }
    catch {
        Write-ColorOutput "ERROR: Failed to execute test: $($_.Exception.Message)" "Red"
    }
}

function Monitor-TokenStatus {
    Write-ColorOutput "`n=== MONITORING TOKEN STATUS ===" "Cyan"
    Write-ColorOutput "Press Ctrl+C to stop monitoring..." "Gray"
    
    $lastStatus = ""
    
    while ($true) {
        Clear-Host
        Write-ColorOutput "=== TOKEN MONITOR === $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Cyan"
        
        $config = Analyze-CurrentConfig
        
        if ($config -and $config.AccessToken) {
            $tokenInfo = Get-TokenInfo $config.AccessToken
            
            if (-not $tokenInfo.Error) {
                $currentStatus = if ($tokenInfo.IsExpired) { "EXPIRED" } elseif ($tokenInfo.NeedsRefresh) { "NEEDS_REFRESH" } else { "VALID" }
                
                if ($currentStatus -ne $lastStatus) {
                    Write-ColorOutput "`nSTATUS CHANGE: $lastStatus -> $currentStatus" "Magenta"
                    $lastStatus = $currentStatus
                    
                    if ($currentStatus -eq "NEEDS_REFRESH") {
                        Write-ColorOutput "Token is approaching expiry - should refresh soon!" "Yellow"
                    } elseif ($currentStatus -eq "EXPIRED") {
                        Write-ColorOutput "Token has expired - refresh required!" "Red"
                    }
                }
            }
        }
        
        Start-Sleep -Seconds 30
    }
}

function Create-ExpiredTokenScenario {
    Write-ColorOutput "`n=== CREATING EXPIRED TOKEN SCENARIO ===" "Cyan"
    
    # Backup current config
    $backupPath = "$ConfigPath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item $ConfigPath $backupPath
    Write-ColorOutput "Created backup: $backupPath" "Green"
    
    try {
        $config = Get-Content $ConfigPath | ConvertFrom-Json
        
        # Create an expired token (expired 1 hour ago)
        $expiredTime = [DateTimeOffset]::UtcNow.AddHours(-1).ToUnixTimeSeconds()
        
        # Simple expired JWT for testing
        $header = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes('{"typ":"JWT","alg":"RS256"}')) -replace '=',''
        $payload = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("{`"sub`":`"test@example.com`",`"exp`":$expiredTime}")) -replace '=',''
        $signature = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes('dummy-signature')) -replace '=',''
        $expiredToken = "$header.$payload.$signature"
        
        $config.ReviztoAPI.AccessToken = $expiredToken
        
        $config | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath
        
        Write-ColorOutput "Created expired token scenario. Current config:" "Yellow"
        Analyze-CurrentConfig
        
        Write-ColorOutput "`nNow testing workflow with expired token..." "White"
        Test-TokenRefreshWorkflow
        
        # Restore backup
        Write-ColorOutput "`nRestoring original configuration..." "Yellow"
        Copy-Item $backupPath $ConfigPath
        Remove-Item $backupPath
        Write-ColorOutput "Configuration restored." "Green"
    }
    catch {
        Write-ColorOutput "ERROR: $($_.Exception.Message)" "Red"
        # Restore backup on error
        if (Test-Path $backupPath) {
            Copy-Item $backupPath $ConfigPath
            Remove-Item $backupPath
            Write-ColorOutput "Configuration restored due to error." "Yellow"
        }
    }
}

# Main execution
Write-ColorOutput "=== REVIZTO TOKEN REFRESH DIAGNOSTIC ===" "Cyan"
Write-ColorOutput "Configuration: $ConfigPath" "White"

if ($TestExpiredScenario) {
    Create-ExpiredTokenScenario
} elseif ($Monitor) {
    Monitor-TokenStatus
} else {
    Analyze-CurrentConfig
    Test-TokenRefreshWorkflow
    
    Write-ColorOutput "`n=== DIAGNOSTIC COMPLETE ===" "Cyan"
    Write-ColorOutput "Available options:" "White"
    Write-ColorOutput "  -Monitor           : Continuously monitor token status" "Gray"
    Write-ColorOutput "  -TestExpiredScenario : Test workflow with expired token" "Gray"
}