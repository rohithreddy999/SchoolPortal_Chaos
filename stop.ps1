$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$postgresDataDir = Join-Path $projectRoot "postgres-runtime\data"
$runtimeDir = Join-Path $projectRoot ".runtime"
$backendPidFile = Join-Path $runtimeDir "backend-shell.pid"
$frontendPidFile = Join-Path $runtimeDir "frontend-shell.pid"

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor DarkYellow
}

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

function Stop-TrackedShell([string]$PidFile, [string]$Label) {
    if (-not (Test-Path $PidFile)) {
        return $false
    }

    $pidValue = Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    if (-not $pidValue) {
        return $false
    }

    $process = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
    if ($process) {
        Write-Step "Stopping $Label shell window (PID $pidValue)."
        Stop-Process -Id ([int]$pidValue) -Force
        return $true
    }

    return $false
}

function Stop-ListenerIfMatch([int]$Port, [string]$Label, [string]$MatchText) {
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $connection) {
        return $false
    }

    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($connection.OwningProcess)"
    if ($process -and $process.CommandLine -and $process.CommandLine -like "*$MatchText*") {
        Write-Step "Stopping $Label listener on port $Port (PID $($connection.OwningProcess))."
        Stop-Process -Id $connection.OwningProcess -Force
        return $true
    }

    return $false
}

$null = Stop-TrackedShell -PidFile $backendPidFile -Label "backend"
$null = Stop-ListenerIfMatch -Port 8000 -Label "backend" -MatchText "School Fee Portal\backend"

$null = Stop-TrackedShell -PidFile $frontendPidFile -Label "frontend"
$null = Stop-ListenerIfMatch -Port 5173 -Label "frontend" -MatchText "School Fee Portal\frontend"

if (Test-Path (Join-Path $postgresDataDir "PG_VERSION")) {
    $pgCtl = Get-PostgresTool "pg_ctl"
    & $pgCtl -D $postgresDataDir status *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Step "Stopping the project PostgreSQL cluster."
        & $pgCtl -D $postgresDataDir stop -m fast
        if ($LASTEXITCODE -ne 0) {
            throw "Could not stop the project PostgreSQL cluster."
        }
    }
}

Write-Host ""
Write-Host "School Fee Portal services stopped." -ForegroundColor Green
