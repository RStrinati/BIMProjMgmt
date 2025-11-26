$accessToken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIzMjgzODRhYTg1M2E2YTJjYWNmMTQzZGRjNmY4MTkyZSIsImp0aSI6ImQzMzQ3MzVhNzAzNzUzZWRiMTAyNjc1OWQyOWZkMDZkOTZiMDdjYzhmZTdiZDM2MzQ0MzFlNGY1OWY4Yzc0ZmMwMmQxMjZkOGNiODUxODRiIiwiaWF0IjoxNzU5MTA5NDUyLjk1MTkxLCJpc3MiOiJ7XCJob3N0XCI6XCJhcGkuc3lkbmV5LnJldml6dG8uY29tXCIsXCJwb3J0XCI6NDQzLFwicHJvdG9jb2xcIjpcImh0dHBzXCIsXCJ0aW1lem9uZV9uYW1lXCI6XCJBQ1NUXCIsXCJ0aW1lem9uZV9zaGlmdFwiOlwiQXVzdHJhbGlhXFwvRGFyd2luXCJ9IiwibmJmIjoxNzU5MTA5NDUyLjk1MTkxNCwiZXhwIjoxNzU5MTEzMDUyLjg5OTI2Miwic3ViIjoicmljby5zdHJpbmF0aUBpaW1iZS5pbyIsInNjb3BlcyI6WyJvcGVuQXBpIl19"

$payload = $accessToken.Split('.')[1]
$paddingLength = (4 - $payload.Length % 4) % 4
$paddedPayload = $payload + ("=" * $paddingLength)

try {
    $decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($paddedPayload))
    $json = $decoded | ConvertFrom-Json
    
    Write-Host "=== Current Access Token Info ===" -ForegroundColor Green
    Write-Host "Issued at (iat):" $json.iat
    Write-Host "Expires at (exp):" $json.exp
    
    # Convert timestamps to readable dates
    $iatDate = [System.DateTimeOffset]::FromUnixTimeSeconds($json.iat).DateTime
    $expDate = [System.DateTimeOffset]::FromUnixTimeSeconds([double]$json.exp).DateTime
    
    Write-Host "Issued date:" $iatDate.ToString("yyyy-MM-dd HH:mm:ss") "UTC" -ForegroundColor Yellow
    Write-Host "Expiry date:" $expDate.ToString("yyyy-MM-dd HH:mm:ss") "UTC" -ForegroundColor Yellow
    Write-Host "Current time:" (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss") "UTC" -ForegroundColor Yellow
    
    $isExpired = (Get-Date).ToUniversalTime() -gt $expDate
    if ($isExpired) {
        Write-Host "❌ Token is EXPIRED" -ForegroundColor Red
        $hoursExpired = ((Get-Date).ToUniversalTime() - $expDate).TotalHours
        Write-Host "Token expired $([math]::Round($hoursExpired, 2)) hours ago" -ForegroundColor Red
    } else {
        Write-Host "✅ Token is VALID" -ForegroundColor Green
        $hoursLeft = ($expDate - (Get-Date).ToUniversalTime()).TotalHours
        Write-Host "Token expires in $([math]::Round($hoursLeft, 2)) hours" -ForegroundColor Green
    }
    
    Write-Host "User:" $json.sub -ForegroundColor Cyan
    Write-Host "Scopes:" ($json.scopes -join ", ") -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Failed to decode token: $_" -ForegroundColor Red
}