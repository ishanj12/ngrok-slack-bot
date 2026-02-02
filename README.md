# ngrok Slack Bot - Documentation Assistant

A Slack bot that helps users find information in the ngrok documentation using the [ngrok-mcp](https://github.com/nijikokun/ngrok-mcp) server.

## Features

- 🔍 **Smart Search** - Searches ngrok documentation via MCP
- 💬 **Multiple Interaction Methods**:
  - Mention the bot: `@ngrok-bot your question`
  - Direct message the bot
  - Slash commands: `/ngrok-ask`, `/ngrok-yaml`, `/ngrok-help`
- ⚡ **Real-time Docs** - Uses ngrok's official documentation catalog
- 🔄 **No Scraping Required** - MCP server handles doc fetching and caching

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Add your ngrok API key (get one at [dashboard.ngrok.com](https://dashboard.ngrok.com/api)):

```
NGROK_API_KEY=your-ngrok-api-key
```

### 3. Run CLI Mode (No Slack Required)

```bash
python chat_cli.py
```

Example session:
```
🤖 Connecting to ngrok-mcp server...
✅ Connected! Available tools: search_ngrok_docs, get_doc, index_docs, ...

❓ Your question: What is ngrok?
❓ Your question: How do I create an HTTP tunnel?
❓ Your question: list    # Lists available documentation
❓ Your question: tools   # Shows available MCP tools
```

## Architecture

This bot uses the [ngrok-mcp](https://github.com/nijikokun/ngrok-mcp) server which provides:

- **search_ngrok_docs** - Search ngrok documentation
- **get_doc** - Fetch a specific doc (cached)
- **index_docs** - List available docs from the catalog
- **warm_docs** - Pre-fetch docs for a workflow
- **docs_cache_status** - Show cache state

Plus ngrok account management tools (endpoints, domains, tunnels, etc.)

## Project Structure

```
slack-chatbot/
├── src/
│   ├── mcp/
│   │   ├── client.py           # MCP client (connects to ngrok-mcp)
│   │   └── ngrok_assistant.py  # High-level wrapper + sync helpers
│   ├── bot/
│   │   ├── app.py              # Slack Bolt app
│   │   └── handlers.py         # Message/command handlers
│   └── rag/                    # (Legacy) Local RAG system
├── chat_cli.py                 # Interactive CLI
├── run_bot.py                  # Bot startup script
└── requirements.txt
```

## Slack Bot Setup (Optional)

### 1. Create Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. Name it (e.g., "ngrok Bot") and select your workspace

### 2. Configure Permissions

Add these OAuth scopes under **OAuth & Permissions**:
- `app_mentions:read`
- `chat:write`
- `channels:history`
- `im:history`
- `im:read`
- `im:write`
- `commands`

### 3. Enable Events

Enable **Event Subscriptions** and subscribe to:
- `app_mention`
- `message.im`

### 4. Create Slash Commands

Under **Slash Commands**:
- `/ngrok-ask` - Ask a question about ngrok
- `/ngrok-yaml` - Get YAML configuration help
- `/ngrok-help` - Show help message

### 5. Enable Socket Mode

Enable **Socket Mode** in settings.

### 6. Add Credentials to .env

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret
```

### 7. Run the Bot

```bash
python run_bot.py
```

## Legacy RAG System

The original RAG system (scraper + indexer + retriever) is still available in `src/rag/` and `src/scraper/` for fallback or offline use:

```bash
# Scrape docs
python src/scraper/ngrok_scraper.py

# Index for vector search
python src/rag/indexer.py
```

## Requirements

- Python 3.11+
- Node.js (for npx to run ngrok-mcp)
- ngrok API key

## License

MIT License
