param(
  [string]$Server = $env:DB_SERVER,
  [string]$Database = "ProjectManagement",
  [string]$User = $env:DB_USER,
  [string]$Password = $env:DB_PASSWORD,
  [string]$Driver = $env:DB_DRIVER,
  [string]$SqlFile = "warehouse/sql/run_full_load.sql"
)

if (-not $Server) { Write-Error "DB server not specified. Set DB_SERVER env var or pass -Server"; exit 1 }

# Resolve path
$repoRoot = Split-Path -Parent $PSCommandPath
$root = Resolve-Path "$repoRoot/.."
$fullSqlPath = Join-Path $root $SqlFile

if (-not (Test-Path $fullSqlPath)) { Write-Error "SQL file not found: $fullSqlPath"; exit 1 }

# Prefer sqlcmd if available
$sqlcmd = Get-Command sqlcmd -ErrorAction SilentlyContinue
if ($null -eq $sqlcmd) {
  Write-Error "sqlcmd not found. Install SQL Server Command Line Utilities or run the SQL manually in SSMS: $fullSqlPath"
  exit 1
}

$credArgs = @()
if ($User -and $Password) {
  $credArgs += @("-U", $User, "-P", $Password)
} else {
  $credArgs += @("-E") # Windows auth
}

Write-Host "Running warehouse load from $fullSqlPath against $Server/$Database"
& sqlcmd -S $Server -d $Database -b -i $fullSqlPath @credArgs
if ($LASTEXITCODE -ne 0) { Write-Error "Warehouse load failed."; exit $LASTEXITCODE }
Write-Host "Warehouse load completed successfully."
