#Requires -Version 5.1
<#
.SYNOPSIS
    Installs the RevitSync pyRevit extension on this machine.
.DESCRIPTION
    1. Locates (or creates) the pyRevit extensions directory.
    2. Copies the RevitSync.extension folder into it (proper pyRevit layout).
    3. Writes per-user environment variables for WS_URL and SESSION_ID.
    4. Reminds the user to reload pyRevit.

.NOTES
    Plugin runs under pyRevit's IronPython 3 engine (the default). No pip
    dependencies -- WebSocket support comes from .NET's built-in
    System.Net.WebSockets.ClientWebSocket.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# -- helpers ------------------------------------------------------------------

function Write-Step { param([string]$msg) Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Write-OK   { param([string]$msg) Write-Host "   OK   $msg" -ForegroundColor Green }
function Write-Warn { param([string]$msg) Write-Host "   WARN $msg" -ForegroundColor Yellow }
function Abort      { param([string]$msg) Write-Host "`nERROR: $msg" -ForegroundColor Red; exit 1 }

# -- locate pyRevit extensions dir --------------------------------------------

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

# -- copy the extension -------------------------------------------------------

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

# -- per-user config ----------------------------------------------------------

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

# -- done ---------------------------------------------------------------------

Write-Host @"

----------------------------------------------------------------
  RevitSync installed.

  Extension : $dstExt
  WS URL    : $wsUrl
  Session   : $sessionId

  Next steps:
    1. Open Revit (or fully close and reopen if it was open -- env vars
       are read at process startup).
    2. In the pyRevit ribbon: click Reload.
    3. New "RevitSync" tab should appear with Status + Test Toast buttons.
    4. Click "Test Toast" to verify the notification UI.

  Engine note:
    Plugin runs under IronPython 3 (the default Active Engine). No need
    to switch engines or pip-install anything.
----------------------------------------------------------------
"@ -ForegroundColor Green
