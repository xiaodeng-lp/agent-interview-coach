# Setup

## 1. Install Dependencies

```powershell
cd path\to\agent-interview-coach
powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
```

## 2. Configure Model API

Edit `app\.env`:

```text
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4.1-mini
MODEL_API_STYLE=chat
```

For OpenAI-compatible providers, change `OPENAI_BASE_URL` and `MODEL_NAME`.

## 3. Log In to WeChat

```powershell
wechat-clawbot-cc setup
```

Scan the QR code with WeChat.

## 4. Verify Connectivity

```powershell
python smoke_test.py --model
python smoke_test.py --wechat
```

## 5. Start

```powershell
powershell -ExecutionPolicy Bypass -File .\start_bot.ps1
```

If WeChat is not available yet, run the local CLI fallback:

```powershell
python cli_chat.py
```

Run full diagnostics from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\doctor.ps1
```

## 6. First WeChat Flow

```text
/资料入口
```

Then either send a `.docx/.pdf/.md/.txt` file directly in WeChat, or import a local folder:

```text
/导入资料 C:\path\to\resume_materials
/生成背景
开始电话面
```
