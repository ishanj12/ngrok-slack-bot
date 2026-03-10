# ngrok Slack Bot - Documentation Assistant

A Slack bot that helps users find information in the ngrok documentation using the [ngrok-mcp](https://github.com/nijikokun/ngrok-mcp) server, and creates support tickets in Zendesk with automatic routing based on the customer's organization and plan.

## Features

- **Smart Search** — Searches ngrok documentation via MCP
- **AI-Powered Answers** — Synthesizes concise answers from docs using configurable LLM models (OpenAI, Anthropic, Gemini)
- **Multiple Interaction Methods**:
  - Mention the bot: `@ngrok-bot your question`
  - Direct message the bot
  - Slash commands: `/ngrok-ask`, `/ngrok-yaml`, `/ngrok-help`
- **Real-time Docs** — Uses ngrok's official documentation catalog
- **No Scraping Required** — MCP server handles doc fetching and caching
- **Zendesk Ticket Creation** — Create support tickets directly from Slack with automatic organization-based routing
- **Automatic Ticket Categorization** — Tickets are auto-assigned a priority and routed to the correct Zendesk support group based on the requester's organization plan

## Architecture
https://mermaid.live/edit#pako:eNqNV-tu2zYUfhVCRYEEkxM7tZ1GP4ZlSVEUy6VoMhRbUwi0RMmEKVIjqTRuGqAPsSfYo_VJdg4pyaKTFvWPgDyXj-fyHYq5jzKVsyiJCqE-ZUuqLbk-vZEEfqZZlJrWS3IlaLbyMvxVTFqu5Ieb6Dda12m7JewWFjfRx41hXoFNxYyhJfNqsnN6TvaJXWpGc6JZLda7gYsR1CzBa1-WWq1G1Kxi0q7XtBL9ZslE3Tsymd_IrZiXVOaCaQNY3XKvXgdneXm6SScU7Ow-Ze1y6tdgcyO_ff2PFFxYphMC6SlNFsqOaiglz3hNLcu7hJUU69aBl1JpBiUoG0E1gcpLyQSpTGleOhYKsTkXNlvBgSTVzNRK5mCGBimYdqI-yloZa4hhVGdLLks8rYtf6YqCzrWaLITKVuaH9aXGcGOptHCea0naS7brjNE4EzDt1zu7wIOSSaahQF6UYoddrDtmLTPyCQ6qoW9hqosyFUrVgPU7hAp-jczhCHDgqiUZ6hFFNzLlMl30drs_TCkTnLl8_ALDIN--_ksuMLbzk7cnTrqdmc9pqx2-wqDyizRXmembkC4aLvK0Vf3TMM3ZQItBf0e3emlaokHzOnuTAY-w042wUFRN5Qq1w3CY1NyFk_pVa70BLpjNlmSvykkNo2rILadkaW191-rZndU0s-Sv4_OzjhytZyNEmilpsXLJdDwefwy75XLN7B2e7jdQDO9xZ10AwBtWLQQjKCG_uEMCjEwgtYo1QnRrV5u18181C6YlsxD3PqE1x7_ldqeAH9ZVwC2Y4Z9hjKT5xLTDuKyZPH5DytqOpmpUcckDb4Bz5ASAnrI9WQPfHxIM8oNIKcK8apfkiulbnrFw6KusBg7oW6bB9JxLKyBlAhx05kzDqdgek-z763AvU9U-kmwfPJH5V45AjrmnKmvwRqPukrZKia17DfucOgZ0o0wQakMHBHRW5PWr69BZQe6Ug19bhOO3b9Aa-eORaq3u1k-OXffZGI1-3bqJvT6vhqq8amuJ34ehAoavQwxRnNHgXgxsWvDvqUH-WO8tBqLexKW6UfvMUdneVZ3hAMOJ_Ji3ibk1ir9Ay6HTGYXJwnbdRF8GhNi2boe7Ky-uW5B-qBFg0OVt082Mek2_dcpu4Lyu2_nwcZTaeHDZngufMouErAXDPhg83vPE23bD9BPmj8H9zLqrAg0fNXAL3F1YTxp78-fP4QtcqVv4RLvUTlmBFMtWF_AowrtWJM8mdEIPWGwsdJUlz6b0iBVFnCmhdPKsKIrvI7UPjwDrgE3oAKsopvSnsPw3aQCFQAOoopgv5oufgoJyBDhBSEWRZVshDVrfTW2cV7Efxb5aQ6twEuN-6OLNfMXDQRoUagjTD1PcDhI6xZ77sSdw3LM17rgZO77EPRM2lQsS6ScqHsxG7JnXlSiKo1LzPEqsblgMT1l4JOE2ukco_LxnjeZ2fQbvDpjTBEUWwgK6xQMLhqoP_vSNKA4EG5RensNQgKJYnyhZcPiko-JjC_xImZD7zvH47Ozy_avT9Pr49dXgaFTRHh93i2CHFMCXw0DEgx2rgi3-4xAIah3uTU1laBCern1KXVLD0I-vr98NcmpDH6SCEnhUFwNEFFluBetgAdgvHkL89M-LPy4u31-kb99dXl-eXJ65KhVUGEeRh7bE8E6omO9qzgoKLyYEfgBSQF5_K1V1vIC3ZbmMEgcQR02dw_vglFP46G9M4MvH9Ak8Qm2UTGcvHEaU3Ed3UTKZTfbm05ezo-l8PJ-Mx4cHcbSOktFsvDebHL6cjA9nR_PZfPbiIY4-u2PHe0ezw9nh4ezFfDIDv8nBw__uDpOW

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
# Required
NGROK_API_KEY=your-ngrok-api-key          # From dashboard.ngrok.com/api
OPENAI_API_KEY=your-openai-api-key        # For AI answers

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...

# Zendesk (required for ticket creation)
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=your-email@company.com
ZENDESK_API_TOKEN=your-zendesk-api-token
```

### 4. Run CLI Mode (No Slack Required)

```bash
python chat_cli.py
```

Example:
```
Connecting to ngrok-mcp server...
Connected! Available tools: search_ngrok_docs, get_doc, ...

Your question: How do I restrict IPs with Traffic Policy?
```

### 5. Run Slack Bot

```bash
python run_bot.py
```

## Slash Commands

| Command | Description |
|---------|-------------|
| `/ngrok-ask <question>` | Ask a question about ngrok |
| `/ngrok-yaml <description>` | Generate an ngrok YAML configuration |
| `/ngrokbot-model` | Select your preferred AI model |
| `/ngrok-ticket` | Create a support ticket |
| `/ngrok-help` | Show help and usage info |

## Ticket Creation

Users can create Zendesk support tickets in two ways:

### Via Slash Command

1. Type `/ngrok-ticket` in any channel
2. A modal opens with fields for **Subject**, **Description**, and **Email**
3. Submit the form

### Via Conversation Button

1. Ask the bot a question (mention or DM)
2. After the bot responds, click the **Create Support Ticket** button
3. The modal opens pre-filled with a synthesized summary of the conversation
4. Review, edit if needed, and submit

### How Tickets Are Scoped

When a ticket is submitted, the bot automatically:

1. **Looks up the requester** in Zendesk by the email provided
2. **Resolves their organization** and reads the `plans` field from the org's custom fields
3. **Assigns the ticket to a Zendesk group** based on the plan:

   | Plan | Zendesk Group |
   |------|---------------|
   | `v2_enterprise` | Enterprise Tier Support |
   | `v1_basic`, `v1_pro`, `v1_business`, `v2_pro`, `v3_paygo`, `v3_hobbyist` | Self-Service Tier Support |
   | No plan / unrecognized plan | Self-Service Tier Support (default) |

4. **Sets ticket priority** automatically based on the plan:

   | Plan | Priority |
   |------|----------|
   | `v2_enterprise`, `v2_pro`, `v1_pro`, `v2_legacy_pro` | High |
   | `v3_paygo`, `v2_paygo`, `v2_personal`, `v1_basic`, `v2_legacy_basic` | Normal |
   | No plan / unrecognized | Low |

5. **Tags the ticket** with `slack`, `ngrok-bot`, and plan/support-package identifiers (e.g. `plan_v2_pro`) so Zendesk triggers can act on them
6. **Associates the ticket** with the requester's Zendesk organization

## Project Structure

```
ngrok-slack-bot/
├── src/
│   ├── mcp/
│   │   ├── client.py             # MCP client (connects to ngrok-mcp)
│   │   └── ngrok_assistant.py    # Sync wrappers for Slack handlers
│   ├── bot/
│   │   ├── app.py                # Slack Bolt app & event routing
│   │   ├── handlers.py           # Message/command/ticket handlers
│   │   └── models.py             # Per-user AI model preferences
│   └── zendesk/
│       └── client.py             # Zendesk API client (tickets, org lookup, plan routing)
├── chat_cli.py                   # Interactive CLI
├── run_bot.py                    # Bot startup script
├── ngrok-mcp/                    # Clone of ngrok-mcp server (gitignored)
└── requirements.txt
```

## Slack App Setup

### 1. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. **Create New App** --> **From scratch**
3. Enable **Socket Mode**

### 2. Add Bot Scopes

Under **OAuth & Permissions**:
- `app_mentions:read`, `chat:write`, `im:history`, `im:read`, `im:write`, `commands`, `users:read`, `users:read.email`

### 3. Subscribe to Events

- `app_mention`, `message.im`

### 4. Create Slash Commands

- `/ngrok-ask` -- Ask a question about ngrok
- `/ngrok-yaml` -- Get YAML configuration help
- `/ngrokbot-model` -- Select AI model
- `/ngrok-ticket` -- Create a support ticket
- `/ngrok-help` -- Show help message

### 5. Enable Interactivity

Turn on **Interactivity & Shortcuts** (required for modals used by ticket creation and model selection).

### 6. Run

```bash
python run_bot.py
```

## Requirements

- Python 3.11+
- Node.js (for ngrok-mcp)
- ngrok API key
- At least one LLM API key (OpenAI, Anthropic, or Gemini)
- Zendesk API credentials (for ticket creation)

## License

MIT License
