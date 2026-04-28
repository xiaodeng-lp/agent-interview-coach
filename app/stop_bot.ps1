$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root "coach_bot.pid"

if (!(Test-Path $pidFile)) {
    Write-Host "coach_bot is not running: no pid file"
    exit 0
}

$pidValue = (Get-Content $pidFile -Raw).Trim()
if ($pidValue) {
    Stop-Process -Id ([int]$pidValue) -Force
    Write-Host "stopped coach_bot, pid=$pidValue"
}
Remove-Item $pidFile -Force
