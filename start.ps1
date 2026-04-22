$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"
$postgresRoot = Join-Path $projectRoot "postgres-runtime"
$postgresDataDir = Join-Path $postgresRoot "data"
$postgresLog = Join-Path $postgresRoot "postgres.log"
$postgresPasswordFile = Join-Path $postgresRoot "pgpass.txt"
$runtimeDir = Join-Path $projectRoot ".runtime"
$backendPidFile = Join-Path $runtimeDir "backend-shell.pid"
$frontendPidFile = Join-Path $runtimeDir "frontend-shell.pid"
$backendRequirementsHashFile = Join-Path $runtimeDir "backend.requirements.sha256"

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor DarkYellow
}

function Ensure-File([string]$Source, [string]$Target) {
    if (-not (Test-Path $Target)) {
        Copy-Item $Source $Target -Force
        Write-Step "Created $(Split-Path -Leaf $Target) from example."
    }
}

function Get-CommandPath([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Required command '$Name' is not installed or not on PATH."
    }

    return $command.Source
}

function Get-PostgresTool([string]$ToolName) {
    $postgresInstallRoot = "C:\Program Files\PostgreSQL"
    if (-not (Test-Path $postgresInstallRoot)) {
        throw "PostgreSQL was not found under '$postgresInstallRoot'. Install PostgreSQL first."
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
    $databaseUrlLine = Get-Content $EnvFile | Where-Object { $_ -match "^DATABASE_URL=" } | Select-Object -First 1
    if (-not $databaseUrlLine) {
        throw "DATABASE_URL is missing from '$EnvFile'."
    }

    $databaseUrl = $databaseUrlLine -replace "^DATABASE_URL=", ""
    $pattern = "^postgresql\+psycopg://(?<user>[^:]+):(?<password>[^@]+)@(?<host>[^:\/]+):(?<port>\d+)\/(?<database>.+)$"
    if ($databaseUrl -notmatch $pattern) {
        throw "DATABASE_URL format is not supported by start.ps1: '$databaseUrl'."
    }

    return @{
        User = $Matches.user
        Password = $Matches.password
        Host = $Matches.host
        Port = [int]$Matches.port
        Database = $Matches.database
    }
}

function Wait-ForListeningPort([int]$Port, [int]$TimeoutSeconds = 60) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1) {
            return $true
        }

        Start-Sleep -Seconds 1
    }

    return $false
}

function Start-WindowedProcess(
    [string]$Title,
    [string]$WorkingDirectory,
    [string]$CommandText,
    [string]$PidFile
) {
    $pwsh = Get-CommandPath "pwsh"
    $script = @"
Set-Location '$WorkingDirectory'
`$Host.UI.RawUI.WindowTitle = '$Title'
$CommandText
"@

    $process = Start-Process -FilePath $pwsh `
        -WorkingDirectory $WorkingDirectory `
        -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $script) `
        -PassThru

    $process.Id | Set-Content $PidFile
    return $process
}

function Ensure-BackendEnvironment() {
    $venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
    $alembicExecutable = Join-Path $backendDir ".venv\Scripts\alembic.exe"
    $requirementsPath = Join-Path $backendDir "requirements.txt"
    $requirementsHash = (Get-FileHash -Path $requirementsPath -Algorithm SHA256).Hash
    $needsInstall = $false

    if (-not (Test-Path $venvPython)) {
        $python = Get-CommandPath "python"
        Write-Step "Creating backend virtual environment."
        & $python -m venv (Join-Path $backendDir ".venv")
        $needsInstall = $true
    }

    if (-not (Test-Path $alembicExecutable)) {
        $needsInstall = $true
    }

    if ((Test-Path $backendRequirementsHashFile) -and -not $needsInstall) {
        $installedHash = (Get-Content $backendRequirementsHashFile -ErrorAction SilentlyContinue | Select-Object -First 1)
        if ($installedHash -ne $requirementsHash) {
            $needsInstall = $true
        }
    } elseif (-not $needsInstall) {
        $needsInstall = $true
    }

    if ($needsInstall) {
        Write-Step "Installing backend dependencies."
        & $venvPython -m pip install --disable-pip-version-check -r $requirementsPath | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "Backend dependency installation failed."
        }
        Set-Content -Path $backendRequirementsHashFile -Value $requirementsHash -NoNewline
    }

    return [string]$venvPython
}

function Ensure-FrontendEnvironment() {
    $nodeModulesDir = Join-Path $frontendDir "node_modules"
    if (-not (Test-Path $nodeModulesDir)) {
        $npm = Get-CommandPath "npm.cmd"
        Write-Step "Installing frontend dependencies."
        Push-Location $frontendDir
        try {
            & $npm install
        } finally {
            Pop-Location
        }
    }
}

function Ensure-ProjectDatabase([hashtable]$DbSettings) {
    $pgCtl = Get-PostgresTool "pg_ctl"
    $initdb = Get-PostgresTool "initdb"
    $psql = Get-PostgresTool "psql"

    if (-not (Test-Path (Join-Path $postgresDataDir "PG_VERSION"))) {
        Write-Step "Initializing the project PostgreSQL cluster."
        New-Item -ItemType Directory -Force $postgresRoot | Out-Null
        Set-Content -Path $postgresPasswordFile -Value $DbSettings.Password -NoNewline
        & $initdb -D $postgresDataDir -U $DbSettings.User -A password "--pwfile=$postgresPasswordFile"
        if ($LASTEXITCODE -ne 0) {
            throw "initdb failed. Check PostgreSQL installation."
        }
    }

    & $pgCtl -D $postgresDataDir status *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Step "Starting the project PostgreSQL cluster on port $($DbSettings.Port)."
        & $pgCtl -D $postgresDataDir -l $postgresLog -o " -p $($DbSettings.Port) " start
        if ($LASTEXITCODE -ne 0) {
            throw "Could not start PostgreSQL. Inspect '$postgresLog'."
        }
    } else {
        Write-Step "Project PostgreSQL is already running."
    }

    $env:PGPASSWORD = $DbSettings.Password
    try {
        $dbExists = & $psql -U $DbSettings.User -h $DbSettings.Host -p $DbSettings.Port -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$($DbSettings.Database)';"
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to connect to PostgreSQL on $($DbSettings.Host):$($DbSettings.Port)."
        }

        if ($dbExists.Trim() -ne "1") {
            Write-Step "Creating database '$($DbSettings.Database)'."
            & $psql -U $DbSettings.User -h $DbSettings.Host -p $DbSettings.Port -d postgres -c "CREATE DATABASE $($DbSettings.Database);"
            if ($LASTEXITCODE -ne 0) {
                throw "Could not create database '$($DbSettings.Database)'."
            }
        }
    } finally {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
}

function Run-DatabaseMigrations([string]$PythonExecutable) {
    Write-Step "Applying database migrations."
    Push-Location $backendDir
    try {
        & $PythonExecutable -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) {
            throw "Database migrations failed."
        }
    } finally {
        Pop-Location
    }
}

function Get-ListeningProcess([int]$Port) {
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $connection) {
        return $null
    }

    return Get-CimInstance Win32_Process -Filter "ProcessId = $($connection.OwningProcess)"
}

New-Item -ItemType Directory -Force $runtimeDir | Out-Null
Ensure-File (Join-Path $backendDir ".env.example") (Join-Path $backendDir ".env")
Ensure-File (Join-Path $frontendDir ".env.example") (Join-Path $frontendDir ".env")

$venvPython = Ensure-BackendEnvironment
Ensure-FrontendEnvironment
$npm = Get-CommandPath "npm.cmd"
$dbSettings = Get-DatabaseSettings (Join-Path $backendDir ".env")
Ensure-ProjectDatabase $dbSettings
Run-DatabaseMigrations $venvPython

$backendProcess = Get-ListeningProcess 8000
if ($backendProcess) {
    Write-Step "Backend already running on port 8000 (PID $($backendProcess.ProcessId))."
} else {
    Write-Step "Starting backend in a new PowerShell window."
    $backendCommand = "& '$venvPython' -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    Start-WindowedProcess -Title "School Fee Portal Backend" -WorkingDirectory $backendDir -CommandText $backendCommand -PidFile $backendPidFile | Out-Null
}

$frontendProcess = Get-ListeningProcess 5173
if ($frontendProcess) {
    Write-Step "Frontend already running on port 5173 (PID $($frontendProcess.ProcessId))."
} else {
    Write-Step "Starting frontend in a new PowerShell window."
    $frontendCommand = "& '$npm' run dev -- --host 0.0.0.0 --port 5173"
    Start-WindowedProcess -Title "School Fee Portal Frontend" -WorkingDirectory $frontendDir -CommandText $frontendCommand -PidFile $frontendPidFile | Out-Null
}

if (-not (Wait-ForListeningPort -Port 8000 -TimeoutSeconds 60)) {
    throw "Backend did not start listening on port 8000."
}

if (-not (Wait-ForListeningPort -Port 5173 -TimeoutSeconds 60)) {
    throw "Frontend did not start listening on port 5173."
}

Write-Host ""
Write-Host "School Fee Portal is running." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend:  http://localhost:8000"
Write-Host "Docs:     http://localhost:8000/docs"
Write-Host "Login:    admin / admin123"
