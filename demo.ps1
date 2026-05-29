#Requires -Version 5.1
<#
.SYNOPSIS
    RivalSense — one-command launcher (React + FastAPI).

.DESCRIPTION
    1.  Kills processes on ports 8000 (FastAPI) and 5173 (Vite).
    2.  Loads .env.
    3.  Finds Python virtualenv.
    4.  Installs Python requirements if needed.
    5.  Installs npm dependencies if needed.
    6.  Opens FastAPI backend window (port 8000).
    7.  Opens Vite dev server window (port 5173).
    8.  Waits for both, then opens browser.

.PARAMETER Demo
    Set DEMO_MODE=true (fixture data, no API keys required).

.EXAMPLE
    .\demo.ps1           # live data
    .\demo.ps1 -Demo     # demo data (no API keys needed)
#>

param(
    [switch]$Demo = $true
)

# ── Bootstrap ─────────────────────────────────────────────────────────────────

$RepoRoot = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
Set-Location $RepoRoot

# ── Color helpers ─────────────────────────────────────────────────────────────

function Write-Step { param([string]$Msg)
    Write-Host ""
    Write-Host "  >> $Msg" -ForegroundColor Cyan
}
function Write-Ok   { param([string]$Msg) Write-Host "  OK  $Msg" -ForegroundColor Green  }
function Write-Warn { param([string]$Msg) Write-Host "  !!  $Msg" -ForegroundColor Yellow }
function Write-Fail { param([string]$Msg) Write-Host "  XX  $Msg" -ForegroundColor Red    }

function Exit-Script {
    param([string]$Reason)
    Write-Fail $Reason
    Read-Host "`n  Press Enter to exit"
    exit 1
}

function Kill-Port {
    param([int]$Port)
    $lines = netstat -ano 2>$null | Where-Object { $_ -match ":$Port\s" }
    foreach ($line in $lines) {
        $parts  = ($line.Trim()) -split '\s+'
        $pidStr = $parts[-1]
        if ($pidStr -match '^\d+$') {
            $pidInt = [int]$pidStr
            if ($pidInt -le 4) { continue }
            try { Stop-Process -Id $pidInt -Force -ErrorAction SilentlyContinue; Write-Warn "Killed PID $pidInt (was on :$Port)" } catch { }
        }
    }
}

function Start-EncodedWindow {
    param([string]$Title, [string]$Command, [string]$WorkDir = $RepoRoot)
    $fullCmd = '$Host.UI.RawUI.WindowTitle = ''' + $Title + '''; ' + $Command
    $bytes   = [System.Text.Encoding]::Unicode.GetBytes($fullCmd)
    $encoded = [Convert]::ToBase64String($bytes)
    Start-Process powershell.exe -ArgumentList "-NoExit", "-EncodedCommand", $encoded -WorkingDirectory $WorkDir
}

function Wait-Http {
    param([string]$Url, [int]$MaxAttempts = 30)
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $r = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            if ($r.StatusCode -eq 200) { return $true }
        } catch { }
        Write-Host "    Not yet up -- ${i}/${MaxAttempts} ..." -ForegroundColor DarkGray
        Start-Sleep 2
    }
    return $false
}

# ── Banner ────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ======================================================" -ForegroundColor DarkCyan
Write-Host "     RivalSense  --  React + FastAPI                    " -ForegroundColor Cyan
Write-Host "  ======================================================" -ForegroundColor DarkCyan
Write-Host ""
if ($Demo) {
    Write-Host "  Running in DEMO MODE -- fixture data, no API keys needed." -ForegroundColor Yellow
    Write-Host ""
}

# ── Load .env ─────────────────────────────────────────────────────────────────

Write-Step "Loading environment variables"

$EnvFile = Join-Path $RepoRoot '.env'
if (-not (Test-Path $EnvFile)) {
    $ExampleFile = Join-Path $RepoRoot '.env.example'
    if (Test-Path $ExampleFile) {
        Copy-Item $ExampleFile $EnvFile
        Write-Warn ".env not found -- copied from .env.example"
    } else {
        Exit-Script ".env and .env.example are both missing"
    }
}

$envVarsLoaded = 0
Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line -match '^\s*#') { return }
    if ($line -match '^([^=]+)=(.*)$') {
        $key   = $matches[1].Trim()
        $value = $matches[2].Trim() -replace '\s+#.*$', '' -replace '^[''"]|[''"]$', ''
        [System.Environment]::SetEnvironmentVariable($key, $value, 'Process')
        $envVarsLoaded++
    }
}
if ($Demo) { [System.Environment]::SetEnvironmentVariable('DEMO_MODE', 'true', 'Process'); Write-Warn "DEMO_MODE overridden to true" }
Write-Ok "$envVarsLoaded variables loaded from .env"

# ── Find Python ───────────────────────────────────────────────────────────────

Write-Step "Locating Python"
$pythonExe = $null
foreach ($candidate in @((Join-Path $RepoRoot '.venv\Scripts\python.exe'), (Join-Path $RepoRoot 'venv\Scripts\python.exe'))) {
    if (Test-Path $candidate) { $pythonExe = $candidate; break }
}
if (-not $pythonExe) {
    $sys = Get-Command python -ErrorAction SilentlyContinue
    if ($sys) { $pythonExe = $sys.Source; Write-Warn "No venv found -- using system Python" }
}
if (-not $pythonExe) { Exit-Script "Python not found. Create a venv: python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt" }
$pyVersion = & $pythonExe --version 2>&1
Write-Ok "$pyVersion  ->  $pythonExe"

Write-Step "Checking Python packages"
$stCheck = & $pythonExe -c "import fastapi" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Dependencies missing -- running: pip install -r requirements.txt"
    & $pythonExe -m pip install -r (Join-Path $RepoRoot 'requirements.txt') --quiet
    if ($LASTEXITCODE -ne 0) { Exit-Script "pip install failed" }
    Write-Ok "Dependencies installed"
} else {
    Write-Ok "Python packages available"
}

# ── Ports ─────────────────────────────────────────────────────────────────────

$ApiPort      = 8000
$FrontendPort = 5173
$FrontendDir  = Join-Path $RepoRoot 'frontend'

Write-Step "Clearing ports $ApiPort and $FrontendPort"
Kill-Port $ApiPort
Kill-Port $FrontendPort
Write-Ok "Ports cleared"

# ── npm install if needed ─────────────────────────────────────────────────────

Write-Step "Checking npm dependencies"
$nodeModules = Join-Path $FrontendDir 'node_modules'
if (-not (Test-Path $nodeModules)) {
    Write-Warn "node_modules missing -- running npm install in frontend/"
    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmCmd) { Exit-Script "Node.js / npm not found. Install Node.js 20+ and retry." }
    $origDir = (Get-Location).Path
    Set-Location $FrontendDir
    npm install
    if ($LASTEXITCODE -ne 0) { Exit-Script "npm install failed" }
    Set-Location $origDir
    Write-Ok "npm dependencies installed"
} else {
    Write-Ok "node_modules found"
}

# ── FastAPI backend ───────────────────────────────────────────────────────────

Write-Step "Opening FastAPI backend window  (port $ApiPort)"
$demoLine   = if ($Demo) { '$env:DEMO_MODE = ''true''; ' } else { '' }
$apiCommand = $demoLine +
              '$env:PYTHONPATH = ''' + $RepoRoot + '''; ' +
              'Set-Location ''' + $RepoRoot + '''; ' +
              '& ''' + $pythonExe + ''' -m uvicorn backend.main:app --reload --host 0.0.0.0 --port ' + $ApiPort
Start-EncodedWindow -Title "RivalSense API :$ApiPort" -Command $apiCommand
Write-Ok "FastAPI window opened  ->  http://localhost:$ApiPort"

# ── Vite dev server ───────────────────────────────────────────────────────────

Write-Step "Opening Vite dev server window  (port $FrontendPort)"
$feCommand = 'Set-Location ''' + $FrontendDir + '''; npm run dev'
Start-EncodedWindow -Title "RivalSense UI :$FrontendPort" -Command $feCommand -WorkDir $FrontendDir
Write-Ok "Vite window opened  ->  http://localhost:$FrontendPort"

# ── Wait for API then open browser ───────────────────────────────────────────

Write-Step "Waiting for FastAPI ..."
$apiReady = Wait-Http "http://localhost:$ApiPort/api/meta/competitors"
if ($apiReady) { Write-Ok "API is responding" } else { Write-Warn "API not yet up -- opening browser anyway" }

$appUrl = "http://localhost:$FrontendPort"
Start-Process $appUrl
Write-Ok "Browser opened at $appUrl"

$div = "  " + ("-" * 56)
Write-Host ""
Write-Host $div                                                             -ForegroundColor DarkGray
Write-Host "  Service               URL"                                    -ForegroundColor White
Write-Host $div                                                             -ForegroundColor DarkGray
Write-Host "  React UI              http://localhost:$FrontendPort"         -ForegroundColor Green
Write-Host "  FastAPI backend       http://localhost:$ApiPort"              -ForegroundColor Green
Write-Host "  API docs (Swagger)    http://localhost:$ApiPort/docs"         -ForegroundColor Cyan
Write-Host $div                                                             -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Demo mode:  .\demo.ps1 -Demo" -ForegroundColor Gray
Write-Host "  Live mode:  .\demo.ps1 -Demo:`$false" -ForegroundColor Gray
Write-Host ""
