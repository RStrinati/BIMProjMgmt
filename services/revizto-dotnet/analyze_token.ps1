# JWT Token Analysis Script
# Analyzes the current access token to determine expiration status

param(
    [string]$TokenFromConfig = ""
)

function Decode-JWT {
    param([string]$Token)
    
    if ([string]::IsNullOrEmpty($Token)) {
        Write-Host "No token provided" -ForegroundColor Red
        return $null
    }
    
    $parts = $Token.Split('.')
    if ($parts.Length -ne 3) {
        Write-Host "Invalid JWT format - should have 3 parts separated by dots" -ForegroundColor Red
        return $null
    }
    
    # Decode the payload (second part)
    $payload = $parts[1]
    
    # Add padding if needed for base64 decoding
    while ($payload.Length % 4 -ne 0) {
        $payload += "="
    }
    
    try {
        $payloadBytes = [Convert]::FromBase64String($payload)
        $payloadJson = [System.Text.Encoding]::UTF8.GetString($payloadBytes)
        $payloadObj = $payloadJson | ConvertFrom-Json
        
        return $payloadObj
    } catch {
        Write-Host "Failed to decode JWT payload: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Analyze-Token {
    param($TokenPayload)
    
    if ($null -eq $TokenPayload) {
        return
    }
    
    Write-Host "`n=== JWT Token Analysis ===" -ForegroundColor Green
    Write-Host "Subject (user): $($TokenPayload.sub)" -ForegroundColor Cyan
    Write-Host "Issued at (iat): $($TokenPayload.iat)" -ForegroundColor Cyan
    Write-Host "Expires (exp): $($TokenPayload.exp)" -ForegroundColor Cyan
    Write-Host "Audience: $($TokenPayload.aud)" -ForegroundColor Cyan
    Write-Host "Scopes: $($TokenPayload.scopes -join ', ')" -ForegroundColor Cyan
    
    if ($TokenPayload.exp) {
        $expDouble = [double]$TokenPayload.exp
        $expirationTime = [DateTimeOffset]::FromUnixTimeSeconds([long]$expDouble).DateTime
        $currentTime = [DateTime]::UtcNow
        $timeUntilExpiry = $expirationTime - $currentTime
        
        Write-Host "`n=== Expiration Analysis ===" -ForegroundColor Yellow
        Write-Host "Token expires at: $($expirationTime.ToString('yyyy-MM-dd HH:mm:ss')) UTC" -ForegroundColor White
        Write-Host "Current time: $($currentTime.ToString('yyyy-MM-dd HH:mm:ss')) UTC" -ForegroundColor White
        
        if ($timeUntilExpiry.TotalMinutes -lt 0) {
            Write-Host "❌ TOKEN IS EXPIRED (expired $([Math]::Abs($timeUntilExpiry.TotalMinutes).ToString('F1')) minutes ago)" -ForegroundColor Red
            return $false
        } elseif ($timeUntilExpiry.TotalMinutes -lt 5) {
            Write-Host "⚠️  TOKEN EXPIRES SOON (in $($timeUntilExpiry.TotalMinutes.ToString('F1')) minutes)" -ForegroundColor Yellow
            return $false
        } else {
            Write-Host "✅ TOKEN IS VALID (expires in $($timeUntilExpiry.TotalMinutes.ToString('F1')) minutes)" -ForegroundColor Green
            return $true
        }
    } else {
        Write-Host "❌ No expiration claim found in token" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "JWT Token Analysis Tool" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green

# Get token from config if not provided
if ([string]::IsNullOrEmpty($TokenFromConfig)) {
    $configPath = "appsettings.json"
    if (Test-Path $configPath) {
        try {
            $config = Get-Content $configPath -Raw | ConvertFrom-Json
            $TokenFromConfig = $config.ReviztoAPI.AccessToken
            Write-Host "✅ Loaded token from appsettings.json" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to read token from appsettings.json: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ appsettings.json not found" -ForegroundColor Red
        exit 1
    }
}

$payload = Decode-JWT -Token $TokenFromConfig
$isValid = Analyze-Token -TokenPayload $payload

if ($isValid) {
    Write-Host "`n✅ Token refresh should NOT be needed" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n❌ Token refresh IS needed" -ForegroundColor Red
    exit 1
}