$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root "coach_bot.pid"
$outLogFile = Join-Path $root "coach_bot.out.log"
$errLogFile = Join-Path $root "coach_bot.err.log"
$botScript = Join-Path $root "coach_bot.py"

function Get-CoachBotProcess {
    $escapedBotScript = [Regex]::Escape($botScript)
    Get-CimInstance Win32_Process |
        Where-Object { $_.CommandLine -match $escapedBotScript }
}

if (Test-Path $pidFile) {
    $pidValue = (Get-Content $pidFile -Raw).Trim()
    if (!($pidValue -match '^\d+$')) {
        Write-Host "coach_bot pid file is invalid: $pidValue"
    } else {
        $process = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
        $knownBotPids = @(Get-CoachBotProcess | ForEach-Object { $_.ProcessId })
        if ($process -and ($knownBotPids -contains $process.Id)) {
            Write-Host "coach_bot running, pid=$pidValue"
        } elseif ($process) {
            Write-Host "coach_bot pid file points to a non-coach process, pid=$pidValue"
        } else {
            Write-Host "coach_bot pid file is stale, process is not running, pid=$pidValue"
        }
    }
} else {
    $runningBots = @(Get-CoachBotProcess)
    if ($runningBots.Count -gt 0) {
        Write-Host "coach_bot running without pid file, pid(s): $($runningBots.ProcessId -join ', ')"
    } else {
        Write-Host "coach_bot not running"
    }
}

if (Test-Path $outLogFile) {
    Write-Host "`nlast stdout logs:"
    Get-Content $outLogFile -Tail 20
}

if (Test-Path $errLogFile) {
    Write-Host "`nlast stderr logs:"
    Get-Content $errLogFile -Tail 20
}
