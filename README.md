# Claude Usage Widget

A sleek, always-on-top desktop widget that displays your **Claude.ai** usage limits and prepaid credits in real time.

![Dark glassmorphism UI with neon yellow arc gauges](https://img.shields.io/badge/style-dark%20neon-black?style=flat-square)

## Features

- **Session usage** — current 5-hour rate limit with countdown
- **Weekly limits** — all models + Sonnet-specific usage
- **Prepaid credits** — remaining balance in EUR/USD
- **Extra usage** — monthly spending if enabled
- **Auto-refresh** every 5 minutes + manual refresh
- **Always-on-top** borderless window, draggable
- **Dark glassmorphism** UI with neon yellow arc gauges

## Screenshot

```
 🧠 CLAUDE               LIVE ●  — ✕
 ┌─────────────────────────────────┐
 │   ◠ 2%    ◠ 27%    ◠ 24%      │
 │  Session  All models  Sonnet   │
 ├─────────────────────────────────┤
 │  PREPAID CREDITS               │
 │  176.77 €                      │
 ├─────────────────────────────────┤
 │  EXTRA USAGE                   │
 │  Disabled                      │
 └─────────────────────────────────┘
          By GF — 2026 Claude Widget
```

## Requirements

- Python 3.9+
- Windows 10/11

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/claude-usage-widget.git
cd claude-usage-widget
pip install -r requirements.txt
```

## Setup

1. Copy the example config:
   ```bash
   cp config.example.json config.json
   ```

2. Get your `sessionKey` from Claude.ai:
   - Go to [claude.ai](https://claude.ai)
   - Open DevTools (F12) → **Application** → **Cookies** → `claude.ai`
   - Copy the value of `sessionKey`

3. Get your `org_id`:
   - In DevTools → **Application** → **Cookies** → copy the value of `lastActiveOrg`

4. Paste both values in `config.json`:
   ```json
   {
     "session_key": "sk-ant-sid02-...",
     "org_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
   }
   ```

## Usage

```bash
python claude_widget.py
```

### Launch at Windows startup

Copy `launch_widget.vbs` to your Startup folder:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
```
Edit the path inside `launch_widget.vbs` if your install folder is different.

## How it works

The widget uses `curl_cffi` (which impersonates Chrome's TLS fingerprint) to bypass Cloudflare and fetch data from two Claude.ai internal API endpoints:
- `/api/organizations/{org_id}/usage` — rate limits
- `/api/organizations/{org_id}/prepaid/credits` — balance

Your `sessionKey` never leaves your machine — it is only used for direct HTTPS requests to claude.ai.

## Security

- `config.json` is in `.gitignore` — your session key is never committed
- No data is sent anywhere except claude.ai
- No telemetry, no analytics, no tracking

## License

MIT

---

**By GF — 2026 Claude Widget**
