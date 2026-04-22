[CmdletBinding()]
param(
    [int]$RetentionDays = 14
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendEnvFile = Join-Path $projectRoot "backend\.env"
$backupRoot = Join-Path $projectRoot "backups"

function Get-PostgresTool([string]$ToolName) {
    $postgresInstallRoot = "C:\Program Files\PostgreSQL"
    if (-not (Test-Path $postgresInstallRoot)) {
        throw "PostgreSQL was not found under '$postgresInstallRoot'."
    }

    $tool = Get-ChildItem $postgresInstallRoot -Directory |
        Sort-Object Name -Descending |
        ForEach-Object { Join-Path $_.FullName "bin\$ToolName.exe" } |
        Where-Object { Test-Path $_ } |
        Select-Object -First 1

    if (-not $tool) {
        throw "Could not find '$ToolName.exe' under '$postgresInstallRoot'."
    }

    return $tool
}

function Get-DatabaseSettings([string]$EnvFile) {
    if (-not (Test-Path $EnvFile)) {
        throw "Missing backend environment file at '$EnvFile'."
    }

    $databaseUrlLine = Get-Content $EnvFile | Where-Object { $_ -match "^DATABASE_URL=" } | Select-Object -First 1
    if (-not $databaseUrlLine) {
        throw "DATABASE_URL is missing from '$EnvFile'."
    }

    $databaseUrl = $databaseUrlLine -replace "^DATABASE_URL=", ""
    $pattern = "^postgresql\+psycopg://(?<user>[^:]+):(?<password>[^@]+)@(?<host>[^:\/]+):(?<port>\d+)\/(?<database>.+)$"
    if ($databaseUrl -notmatch $pattern) {
        throw "DATABASE_URL format is not supported by backup.ps1: '$databaseUrl'."
    }

    return @{
        User = $Matches.user
        Password = $Matches.password
        Host = $Matches.host
        Port = [int]$Matches.port
        Database = $Matches.database
    }
}

$dbSettings = Get-DatabaseSettings $backendEnvFile
$pgDump = Get-PostgresTool "pg_dump"
New-Item -ItemType Directory -Force $backupRoot | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$fileName = "$($dbSettings.Database)_$timestamp.dump"
$outputPath = Join-Path $backupRoot $fileName

Write-Host "Creating backup: $outputPath" -ForegroundColor DarkYellow
$env:PGPASSWORD = $dbSettings.Password
try {
    & $pgDump `
        -U $dbSettings.User `
        -h $dbSettings.Host `
        -p $dbSettings.Port `
        -d $dbSettings.Database `
        -F c `
        -f $outputPath

    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump failed."
    }
} finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}

Get-ChildItem $backupRoot -Filter "*.dump" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) } |
    Remove-Item -Force

Write-Host "Backup completed." -ForegroundColor Green
