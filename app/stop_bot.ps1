$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root "coach_bot.pid"
$botScript = Join-Path $root "coach_bot.py"

function Get-CoachBotProcess {
    $escapedBotScript = [Regex]::Escape($botScript)
    Get-CimInstance Win32_Process |
        Where-Object { $_.CommandLine -match $escapedBotScript } |
        ForEach-Object { Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
}

$stopped = @()

if (Test-Path $pidFile) {
    $pidValue = (Get-Content $pidFile -Raw).Trim()
    if ($pidValue -match '^\d+$') {
        $pidProcess = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
        $knownBotPids = @(Get-CoachBotProcess | ForEach-Object { $_.Id })
        if ($pidProcess -and ($knownBotPids -contains $pidProcess.Id)) {
            Stop-Process -Id $pidProcess.Id -Force
            Wait-Process -Id $pidProcess.Id -Timeout 5
            $stopped += $pidProcess.Id
        } elseif ($pidProcess) {
            Write-Host "pid file points to a non-coach process, not stopping it: pid=$pidValue"
        } else {
            Write-Host "removing stale pid file: pid=$pidValue"
        }
    } else {
        Write-Host "removing invalid pid file: $pidValue"
    }
    Remove-Item $pidFile -Force
}

$orphanBots = @(Get-CoachBotProcess | Where-Object { $stopped -notcontains $_.Id })
foreach ($bot in $orphanBots) {
    Stop-Process -Id $bot.Id -Force
    Wait-Process -Id $bot.Id -Timeout 5
    $stopped += $bot.Id
}

if ($stopped.Count -gt 0) {
    Write-Host "stopped coach_bot pid(s): $($stopped -join ', ')"
} else {
    Write-Host "coach_bot is not running"
}
