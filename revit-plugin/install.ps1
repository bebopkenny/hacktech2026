#Requires -Version 5.1
<#
.SYNOPSIS
    Installs the RevitSync pyRevit extension on this machine.
.DESCRIPTION
    1. Locates (or creates) the pyRevit extensions directory.
    2. Copies the RevitSync.extension folder into it (proper pyRevit layout).
    3. Installs websocket-client into pyRevit's CPython 3 environment.
    4. Writes per-user environment variables for WS_URL and SESSION_ID.
    5. Reminds the user to reload pyRevit and ensure CPython3 is the active engine.

.NOTES
    Requires pyRevit to be installed and configured to use the CPython3 engine.
    Switch engines from the pyRevit ribbon: pyRevit -> Settings -> Engines.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── helpers ──────────────────────────────────────────────────────────────────

function Write-Step { param([string]$msg) Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Write-OK   { param([string]$msg) Write-Host "   OK   $msg" -ForegroundColor Green }
function Write-Warn { param([string]$msg) Write-Host "   WARN $msg" -ForegroundColor Yellow }
function Abort      { param([string]$msg) Write-Host "`nERROR: $msg" -ForegroundColor Red; exit 1 }

# ── locate pyRevit extensions dir ────────────────────────────────────────────

Write-Step "Locating pyRevit extensions directory"

$defaultExtDir = Join-Path $env:APPDATA "pyRevit\Extensions"
$pyrevitIni    = Join-Path $env:APPDATA "pyRevit\pyRevit_config.ini"
$extDir        = $defaultExtDir

if (Test-Path $pyrevitIni) {
    $match = Select-String -Path $pyrevitIni -Pattern "^\s*extensions_dirs\s*=" | Select-Object -First 1
    if ($match) {
        $custom = ($match.Line -split "=", 2)[1].Trim().Trim('"').Split(";")[0].Trim()
        if ($custom -and (Test-Path $custom)) {
            $extDir = $custom
            Write-OK "Custom extensions dir from pyRevit config: $extDir"
        }
    }
}

if (-not (Test-Path $extDir)) {
    New-Item -ItemType Directory -Path $extDir -Force | Out-Null
    Write-OK "Created $extDir"
} else {
    Write-OK "Found $extDir"
}

# ── copy the extension ───────────────────────────────────────────────────────

Write-Step "Copying RevitSync.extension"

$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$srcExt      = Join-Path $scriptDir "RevitSync.extension"
$dstExt      = Join-Path $extDir   "RevitSync.extension"

if (-not (Test-Path $srcExt)) {
    Abort "Source extension folder not found: $srcExt"
}

if (Test-Path $dstExt) {
    Remove-Item -Recurse -Force $dstExt
    Write-OK "Removed existing $dstExt"
}

Copy-Item -Recurse -Path $srcExt -Destination $dstExt -Force
Write-OK "Installed to $dstExt"

# ── locate pyRevit CPython 3 ─────────────────────────────────────────────────

Write-Step "Locating pyRevit's CPython 3 interpreter"

$candidates = @(
    "$env:APPDATA\pyRevit-Master\bin\engines\CPY*\python.exe",
    "$env:APPDATA\pyRevit\bin\engines\CPY*\python.exe",
    "C:\ProgramData\pyRevit\bin\engines\CPY*\python.exe",
    "C:\Program Files\pyRevit-Master\bin\engines\CPY*\python.exe",
    "C:\Program Files\pyRevit\bin\engines\CPY*\python.exe"
)

$pyRevitPython = $null
foreach ($pattern in $candidates) {
    $hit = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) { $pyRevitPython = $hit.FullName; break }
}

# Fall back to the pyrevit CLI for the python path
if (-not $pyRevitPython) {
    $pyrevitCLI = Get-Command "pyrevit" -ErrorAction SilentlyContinue
    if ($pyrevitCLI) {
        try {
            $envInfo = & pyrevit env 2>&1 | Out-String
            $match = [regex]::Match($envInfo, 'python(?:\.exe)?\s*[:=]\s*(.+\.exe)')
            if ($match.Success) { $pyRevitPython = $match.Groups[1].Value.Trim() }
        } catch {
            Write-Warn "pyrevit CLI present but could not read env: $($_.Exception.Message)"
        }
    }
}

if (-not $pyRevitPython) {
    Write-Warn "Could not auto-detect pyRevit's CPython 3."
    Write-Warn "Install websocket-client manually into pyRevit's CPython 3:"
    Write-Warn "    <pyrevit-cpython3>\python.exe -m pip install websocket-client"
} else {
    Write-OK "Found: $pyRevitPython"

    Write-Step "Installing websocket-client into pyRevit's CPython 3"
    & $pyRevitPython -m pip install --quiet --upgrade websocket-client
    if ($LASTEXITCODE -eq 0) {
        Write-OK "websocket-client installed"
    } else {
        Write-Warn "pip install returned exit code $LASTEXITCODE — check output above"
    }
}

# ── per-user config ──────────────────────────────────────────────────────────

Write-Step "Configuring per-machine settings"

$currentWS  = [System.Environment]::GetEnvironmentVariable("REVITSYNC_WS_URL",    "User")
$currentSID = [System.Environment]::GetEnvironmentVariable("REVITSYNC_SESSION_ID", "User")

$defaultWS = if ($currentWS) { $currentWS } else { "ws://107.191.50.160:8000/ws" }
$wsInput   = Read-Host "  Coordination service WebSocket URL [$defaultWS]"
$wsUrl     = if ($wsInput.Trim()) { $wsInput.Trim() } else { $defaultWS }
[System.Environment]::SetEnvironmentVariable("REVITSYNC_WS_URL", $wsUrl, "User")
Write-OK "REVITSYNC_WS_URL = $wsUrl"

$defaultSID = if ($currentSID) { $currentSID } else { ($env:USERNAME.ToLower() -replace '\s','-') }
$sidInput   = Read-Host "  Your session ID (unique per person) [$defaultSID]"
$sessionId  = if ($sidInput.Trim()) { $sidInput.Trim() } else { $defaultSID }
[System.Environment]::SetEnvironmentVariable("REVITSYNC_SESSION_ID", $sessionId, "User")
Write-OK "REVITSYNC_SESSION_ID = $sessionId"

# ── done ─────────────────────────────────────────────────────────────────────

Write-Host @"

----------------------------------------------------------------
  RevitSync installed.

  Extension : $dstExt
  WS URL    : $wsUrl
  Session   : $sessionId

  Next steps:
    1. Open Revit (or restart it if it was open).
    2. In the pyRevit ribbon: pyRevit -> Settings -> Engines -> select CPython3.
    3. pyRevit -> Reload (or restart Revit).
    4. New "RevitSync" tab should appear with Status + Test Toast buttons.
    5. Click "Test Toast" to verify the notification UI.
----------------------------------------------------------------
"@ -ForegroundColor Green
