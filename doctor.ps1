$ErrorActionPreference = "Continue"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$app = Join-Path $root "app"
$envFile = Join-Path $app ".env"

function Section($name) {
    Write-Host "`n== $name =="
}

Section "Paths"
Write-Host "Root: $root"
Write-Host "App:  $app"
Write-Host ".env: $envFile"

Section "Python"
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    Write-Host "python: $($python.Source)"
    python --version
} else {
    Write-Host "python not found"
}

Section "Dependencies"
if ($python) {
@'
import importlib.util
mods = ["wechat_clawbot", "openai", "dotenv", "docx", "pypdf"]
for m in mods:
    print(f"{m}: {'ok' if importlib.util.find_spec(m) else 'missing'}")
'@ | python -
}

Section "Environment"
if (Test-Path $envFile) {
    $envText = Get-Content $envFile -Raw
    if ($envText -match "OPENAI_API_KEY=\s*$" -or $envText -notmatch "OPENAI_API_KEY=") {
        Write-Host "OPENAI_API_KEY: missing or empty"
    } else {
        Write-Host "OPENAI_API_KEY: present (hidden)"
    }
    ($envText -split "`n") |
        Where-Object { $_ -match "^(OPENAI_BASE_URL|MODEL_NAME|MODEL_API_STYLE|RESUME_SOURCE_DIR|MAX_CONTEXT_CHARS)=" } |
        ForEach-Object { Write-Host $_ }
} else {
    Write-Host ".env missing. Run install_windows.ps1 first."
}

Section "WeChat Credentials"
@'
try:
    from wechat_clawbot.claude_channel.credentials import load_credentials, credentials_file_path
    acc = load_credentials()
    print(f"credentials_path: {credentials_file_path()}")
    print(f"has_credentials: {bool(acc)}")
    if acc:
        print(f"account_id: {acc.account_id}")
except Exception as e:
    print(f"credential check failed: {e}")
'@ | python -

Section "Model Smoke Test"
if (Test-Path $envFile) {
    Push-Location $app
    $env:PYTHONIOENCODING = "utf-8"
    python smoke_test.py --model
    Pop-Location
} else {
    Write-Host "Skipped: .env missing"
}

Section "WeChat Smoke Test"
Push-Location $app
$env:PYTHONIOENCODING = "utf-8"
python smoke_test.py --wechat
Pop-Location
