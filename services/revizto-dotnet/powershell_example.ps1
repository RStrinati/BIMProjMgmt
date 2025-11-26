# PowerShell example for calling Revizto Data Exporter

# Example 1: Get status
function Get-ReviztoStatus {
    $result = & ".\publish\ReviztoDataExporter.exe" "status" | ConvertFrom-Json
    return $result
}

# Example 2: List all projects
function Get-ReviztoProjects {
    $result = & ".\publish\ReviztoDataExporter.exe" "list-projects" | ConvertFrom-Json
    return $result.projects
}

# Example 3: Export a specific project
function Export-ReviztoProject {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ProjectId,
        [string]$OutputPath = ""
    )
    
    if ($OutputPath) {
        $result = & ".\publish\ReviztoDataExporter.exe" "export" $ProjectId $OutputPath | ConvertFrom-Json
    } else {
        $result = & ".\publish\ReviztoDataExporter.exe" "export" $ProjectId | ConvertFrom-Json
    }
    return $result
}

# Example 4: Refresh projects from API
function Update-ReviztoProjects {
    $result = & ".\publish\ReviztoDataExporter.exe" "refresh" | ConvertFrom-Json
    return $result
}

# Example usage:
Write-Host "Revizto PowerShell Integration Examples"
Write-Host "======================================"

# Get status
Write-Host "`nGetting status..."
$status = Get-ReviztoStatus
Write-Host "Project Count: $($status.status.projectCount)"

# List projects
Write-Host "`nListing projects..."
$projects = Get-ReviztoProjects
foreach ($project in $projects) {
    Write-Host "- $($project.name) [$($project.id)]"
}

# Export example (uncomment to use)
# Write-Host "`nExporting first project..."
# if ($projects.Count -gt 0) {
#     $exportResult = Export-ReviztoProject -ProjectId $projects[0].id
#     if ($exportResult.success) {
#         Write-Host "Export successful: $($exportResult.exportedFile)"
#     } else {
#         Write-Host "Export failed: $($exportResult.message)"
#     }
# }

Write-Host "`nDone!"