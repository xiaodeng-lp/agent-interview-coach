$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root "coach_bot.pid"
$outLogFile = Join-Path $root "coach_bot.out.log"
$errLogFile = Join-Path $root "coach_bot.err.log"

if (Test-Path $pidFile) {
    $oldPid = (Get-Content $pidFile -Raw).Trim()
    if ($oldPid -and (Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue)) {
        Write-Host "coach_bot is already running, pid=$oldPid"
        exit 0
    }
}

$python = (Get-Command python).Source
$args = @("coach_bot.py")
$process = Start-Process `
    -FilePath $python `
    -ArgumentList $args `
    -WorkingDirectory $root `
    -RedirectStandardOutput $outLogFile `
    -RedirectStandardError $errLogFile `
    -WindowStyle Hidden `
    -PassThru

Set-Content -Path $pidFile -Value $process.Id -Encoding ASCII
Write-Host "started coach_bot, pid=$($process.Id)"
Write-Host "stdout log: $outLogFile"
Write-Host "stderr log: $errLogFile"
