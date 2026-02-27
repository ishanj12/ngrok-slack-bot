# ngrok Slack Bot - Documentation Assistant

A Slack bot that helps users find information in the ngrok documentation using the [ngrok-mcp](https://github.com/nijikokun/ngrok-mcp) server.

## Features

- 🔍 **Smart Search** - Searches ngrok documentation via MCP
- 🤖 **AI-Powered Answers** - Synthesizes concise answers from docs using OpenAI
- 💬 **Multiple Interaction Methods**:
  - Mention the bot: `@ngrok-bot your question`
  - Direct message the bot
  - Slash commands: `/ngrok-ask`, `/ngrok-yaml`, `/ngrok-help`
- ⚡ **Real-time Docs** - Uses ngrok's official documentation catalog
- 🔄 **No Scraping Required** - MCP server handles doc fetching and caching

## Architecture
https://mermaid.live/edit#pako:eNqNV-tu2zYUfhVCRYEEkxM7tZ1GP4ZlSVEUy6VoMhRbUwi0RMmEKVIjqTRuGqAPsSfYo_VJdg4pyaKTFvWPgDyXj-fyHYq5jzKVsyiJCqE-ZUuqLbk-vZEEfqZZlJrWS3IlaLbyMvxVTFqu5Ieb6Dda12m7JewWFjfRx41hXoFNxYyhJfNqsnN6TvaJXWpGc6JZLda7gYsR1CzBa1-WWq1G1Kxi0q7XtBL9ZslE3Tsymd_IrZiXVOaCaQNY3XKvXgdneXm6SScU7Ow-Ze1y6tdgcyO_ff2PFFxYphMC6SlNFsqOaiglz3hNLcu7hJUU69aBl1JpBiUoG0E1gcpLyQSpTGmeOhYKsTkXNlvBgSTVzNRK5mCGBimYdqI-yloZa4hhVGdLLks8rYtf6YqCzrWaLITKVuaH9aXGcGOptHCea0naS7brjNE4EzDt1zu7wIOSSaahQF6UYoddrDtmLTPyCQ6qoW9hqosyFUrVgPU7hAp-jczhCHDgqiUZ6hFFNzLlMl30drs_TCkTnLl8_ALSIN--_ksuMLbzk7cnTrqdmc9pqx2-wqDyizRXmembkC4aLvK0Vf3TMM3ZQItBf0e3emlaokHzOnuTAY-w042wUFRN5Qq1w3CY1NyFk_pVa70BLpjNlmSvykkNo2rILadkaW191-rZndU0s-Sv4_OzjhytZyNEmilpsXLJdDwefwy75XLN7B2e7jdQDO9xZ10AwBtWLQQjKCG_uEMCjEwgtYo1QnRrV5u18181C6YlsxD3PqE1x7_ldqeAH9ZVwC2Y4Z9hjKT5xLTDuKyZPH5DytqOpmpUcckDb4Bz5ASAnrI9WQPfHxIM8oNIKcK8apfkiulbnrFw6KusBg7oW6bB9JxLKyBlAhx05kzDqdgek-z763AvU9U-kmwfPJH5V45AjrmnKmvwRqPukrZKia17DfucOgZ0o0wQakMHBHRW5PWr69BZQe6Ug19bhOO3b9Aa-eORaq3u1k-OXffZGI1-3bqJvT6vhqq8amuJ34ehAoavQwxRnNHgXgxsWvDvqUH-WO8tBqLexKW6UfvMUdneVZ3hAMOJ_Ji3ibk1ir9Ay6HTGYXJwnbdRF8GhNi2boe7Ky-uW5B-qBFg0OVt082Mek2_dcpu4Lyu2_nwcZTaeHDZngufMouErAXDPhg83vPE23bD9BPmj8H9zLqrAg0fNXAL3F1YTxp78-fP4QtcqVv4RLvUTlmBFMtWF_AowrtWJM8mdEIPWGwsdJUlz6b0iBVFnCmhdPKsKIrvI7UPjwDrgE3oAKsopvSnsPw3aQCFQAOoopgv5oufgoJyBDhBSEWRZVshDVrfTW2cV7Efxb5aQ6twEuN-6OLNfMXDQRoUagjTD1PcDhI6xZ77sSdw3LM17rgZO77EPRM2lQsS6ScqHsxG7JnXlSiKo1LzPEqsblgMT1l4JOE2ukco_LxnjeZ2fQbvDpjTBEUWwgK6xQMLhqoP_vSNKA4EG5RensNQgKJYnyhZcPiko-JjC_xImZD7zvH47Ozy_avT9Pr49dXgaFTRHh93i2CHFMCXw0DEgx2rgi3-4xAIah3uTU1laBCern1KXVLD0I-vr98NcmpDH6SCEnhUFwNEFFluBetgAdgvHkL89M-LPy4u31-kb99dXl-eXJ65KhVUGEeRh7bE8E6omO9qzgoKLyYEfgBSQF5_K1V1vIC3ZbmMEgcQR02dw_vglFP46G9M4MvH9Ak8Qm2UTGcvHEaU3Ed3UTKZTfbm05ezo-l8PJ-Mx4cHcbSOktFsvDebHL6cjA9nR_PZfPbiIY4-u2PHe0ezw9nh4ezFfDIDv8nBw__uDpOW

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/ishanj12/ngrok-slack-bot.git
cd ngrok-slack-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup ngrok-mcp

```bash
git clone https://github.com/nijikokun/ngrok-mcp.git
cd ngrok-mcp && npm install && npm run build && cd ..
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Add your keys to `.env`:
```
NGROK_API_KEY=your-ngrok-api-key      # Required - get from dashboard.ngrok.com/api
OPENAI_API_KEY=your-openai-api-key    # Required for AI answers
```

### 4. Run CLI Mode (No Slack Required)

```bash
python chat_cli.py
```

Example:
```
🤖 Connecting to ngrok-mcp server...
✅ Connected! Available tools: search_ngrok_docs, get_doc, ...

❓ Your question: How do I restrict IPs with Traffic Policy?
```

## Project Structure

```
ngrok-slack-bot/
├── src/
│   ├── mcp/
│   │   ├── client.py           # MCP client (connects to ngrok-mcp)
│   │   └── ngrok_assistant.py  # Sync wrappers for Slack handlers
│   └── bot/
│       ├── app.py              # Slack Bolt app
│       └── handlers.py         # Message/command handlers
├── chat_cli.py                 # Interactive CLI
├── run_bot.py                  # Bot startup script
├── ngrok-mcp/                  # Clone of ngrok-mcp server (gitignored)
└── requirements.txt
```

## Slack Bot Setup (Optional)

### 1. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. **Create New App** → **From scratch**
3. Enable **Socket Mode**

### 2. Add Bot Scopes

Under **OAuth & Permissions**:
- `app_mentions:read`, `chat:write`, `im:history`, `im:read`, `im:write`, `commands`

### 3. Subscribe to Events

- `app_mention`, `message.im`

### 4. Create Slash Commands

- `/ngrok-ask` - Ask a question about ngrok
- `/ngrok-yaml` - Get YAML configuration help
- `/ngrok-help` - Show help message

### 5. Add Slack Credentials to .env

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...
```

### 6. Run

```bash
python run_bot.py
```

## Requirements

- Python 3.11+
- Node.js (for ngrok-mcp)
- ngrok API key
- OpenAI API key

## License

MIT License
