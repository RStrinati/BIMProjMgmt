$token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIzMjgzODRhYTg1M2E2YTJjYWNmMTQzZGRjNmY4MTkyZSIsImp0aSI6IjNjYjg4MjE4NjgxZjhjMDE3ZDNhNzliZThjYjBjNzQ4MThhNDU0ZmFmYjg1ZjFjNzA4NDFmOGJiYThhNjMxMmY1ZTVjMTU2YTkzYjQ4NmRhIiwiaWF0IjoxNzU4NjgyNjI2LjY4NTA1MSwiaXNzIjoie1wiaG9zdFwiOlwiYXBpLnN5ZG5leS5yZXZpenRvLmNvbVwiLFwicG9ydFwiOjQ0MyxcInByb3RvY29sXCI6XCJodHRwc1wiLFwidGltZXpvbmVfbmFtZVwiOlwiQUNTVFwiLFwidGltZXpvbmVfc2hpZnRcIjpcIkF1c3RyYWxpYVxcL0RhcndpblwifSIsIm5iZiI6MTc1ODY4MjYyNi42ODUwNTcsImV4cCI6MTc1ODY4NjIyNi42MzY4MSwic3ViIjoicmljby5zdHJpbmF0aUBpaW1iZS5pbyIsInNjb3BlcyI6WyJvcGVuQXBpIl19"
$payload = $token.Split('.')[1]
$paddedPayload = $payload
while ($paddedPayload.Length % 4 -ne 0) {
    $paddedPayload += "="
}
$decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($paddedPayload))
$json = $decoded | ConvertFrom-Json

Write-Host "Token Payload:"
Write-Host $decoded
Write-Host ""
Write-Host "Expiration timestamp:" $json.exp
$expDate = [System.DateTimeOffset]::FromUnixTimeSeconds($json.exp).DateTime
Write-Host "Expiration date (UTC):" $expDate
Write-Host "Current date (UTC):" (Get-Date).ToUniversalTime()
$isExpired = (Get-Date).ToUniversalTime() -gt $expDate
Write-Host "Token is expired:" $isExpired