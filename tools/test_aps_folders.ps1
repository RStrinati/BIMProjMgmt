# Test script to call APS service and see detailed folder data
$hubId = "b.e7f595c4-2827-4b95-a74e-ecb215fa9ea6"
$projectId = "b.d2de86cc-1018-409b-ae1b-8d62cbb13ccb"
$url = "http://localhost:3000/my-project-files/$hubId/$projectId"

Write-Host "Testing APS Folders API..." -ForegroundColor Cyan
Write-Host "URL: $url" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $url -Method Get
    
    Write-Host "Success - Response received!" -ForegroundColor Green
    Write-Host "Total Files: $($response.totalFiles)" -ForegroundColor Yellow
    Write-Host "Model Files: $($response.modelFiles.Count)" -ForegroundColor Yellow
    Write-Host "Folders: $($response.folders.Count)" -ForegroundColor Yellow
    Write-Host ""
    
    if ($response.folders.Count -gt 0) {
        Write-Host "Folder Details:" -ForegroundColor Cyan
        foreach ($folder in $response.folders) {
            Write-Host "  - $($folder.name): $($folder.counts.files) files, $($folder.counts.models) models" -ForegroundColor White
        }
    }
    
    if ($response.allFiles.Count -gt 0) {
        Write-Host ""
        Write-Host "Sample Files:" -ForegroundColor Cyan
        $response.allFiles | Select-Object -First 10 | ForEach-Object {
            Write-Host "  - $($_.name) ($($_.extension)) in $($_.folder)" -ForegroundColor White
        }
    } else {
        Write-Host ""
        Write-Host "WARNING - No files found!" -ForegroundColor Red
        Write-Host "This might mean:" -ForegroundColor Yellow
        Write-Host "  1. The recursive function encountered errors" -ForegroundColor Yellow
        Write-Host "  2. Permission issues accessing subfolders" -ForegroundColor Yellow
        Write-Host "  3. Token needs refresh" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "ERROR:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
