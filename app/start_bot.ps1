$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root "coach_bot.pid"
$outLogFile = Join-Path $root "coach_bot.out.log"
$errLogFile = Join-Path $root "coach_bot.err.log"
$botScript = Join-Path $root "coach_bot.py"

function Get-CoachBotProcess {
    $escapedBotScript = [Regex]::Escape($botScript)
    Get-CimInstance Win32_Process |
        Where-Object { $_.CommandLine -match $escapedBotScript } |
        ForEach-Object { Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
}

function Get-ProcessFromPidFile {
    if (!(Test-Path $pidFile)) {
        return $null
    }
    $rawPid = (Get-Content $pidFile -Raw).Trim()
    if (!($rawPid -match '^\d+$')) {
        Write-Host "removing invalid pid file: $rawPid"
        Remove-Item $pidFile -Force
        return $null
    }
    return Get-Process -Id ([int]$rawPid) -ErrorAction SilentlyContinue
}

if (Test-Path $pidFile) {
    $oldPid = (Get-Content $pidFile -Raw).Trim()
    $oldProcess = Get-ProcessFromPidFile
    $knownBotPids = @(Get-CoachBotProcess | ForEach-Object { $_.Id })
    if ($oldProcess -and ($knownBotPids -contains $oldProcess.Id)) {
        Write-Host "coach_bot is already running, pid=$($oldProcess.Id)"
        exit 0
    }
    if ($oldProcess) {
        Write-Host "pid file points to a non-coach process, leaving it alone: pid=$oldPid"
    } else {
        Write-Host "removing stale pid file: pid=$oldPid"
    }
    Remove-Item $pidFile -Force
}

$runningBots = @(Get-CoachBotProcess)
if ($runningBots.Count -gt 0) {
    $pidToUse = $runningBots[0].Id
    Set-Content -Path $pidFile -Value $pidToUse -Encoding ASCII
    Write-Host "coach_bot is already running, pid=$pidToUse"
    if ($runningBots.Count -gt 1) {
        Write-Host "warning: multiple coach_bot processes found: $($runningBots.Id -join ', ')"
    }
    exit 0
}

$python = (Get-Command python).Source
$args = @($botScript)
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
