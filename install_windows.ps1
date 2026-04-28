$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$app = Join-Path $root "app"
$envExample = Join-Path $root ".env.example"
$envFile = Join-Path $app ".env"
$requirements = Join-Path $root "requirements.txt"

Write-Host "Agent Interview Coach - Windows installer"
Write-Host "Project root: $root"

$python = (Get-Command python -ErrorAction Stop).Source
Write-Host "Python: $python"
python --version

Write-Host "`nInstalling Python dependencies..."
python -m pip install -r $requirements

if (!(Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Host "`nCreated app\.env from .env.example"
    Write-Host "Edit this file and fill OPENAI_API_KEY before running the bot:"
    Write-Host $envFile
} else {
    Write-Host "`napp\.env already exists, keeping it."
}

New-Item -ItemType Directory -Force -Path (Join-Path $app "resume_materials") | Out-Null

Write-Host "`nNext steps:"
Write-Host "1. Edit app\.env and fill OPENAI_API_KEY"
Write-Host "2. Run: cd app"
Write-Host "3. Run: python smoke_test.py --model"
Write-Host "4. Optional WeChat login: wechat-clawbot-cc setup"
Write-Host "5. Run: python cli_chat.py"
Write-Host "6. Or start WeChat bot: powershell -ExecutionPolicy Bypass -File .\start_bot.ps1"
