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
