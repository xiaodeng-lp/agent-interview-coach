$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root "coach_bot.pid"
$outLogFile = Join-Path $root "coach_bot.out.log"
$errLogFile = Join-Path $root "coach_bot.err.log"

if (Test-Path $pidFile) {
    $pidValue = (Get-Content $pidFile -Raw).Trim()
    $process = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "coach_bot running, pid=$pidValue"
    } else {
        Write-Host "coach_bot pid file exists, but process is not running"
    }
} else {
    Write-Host "coach_bot not running"
}

if (Test-Path $outLogFile) {
    Write-Host "`nlast stdout logs:"
    Get-Content $outLogFile -Tail 20
}

if (Test-Path $errLogFile) {
    Write-Host "`nlast stderr logs:"
    Get-Content $errLogFile -Tail 20
}
