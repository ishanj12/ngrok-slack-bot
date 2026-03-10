# ngrok Slack Bot — Documentation Assistant

A Slack bot that answers ngrok questions by searching the official documentation via [MCP](https://ngrok.com/docs/mcp), then synthesizing answers with YAML examples using an LLM. Supports OpenAI, Anthropic, and Gemini. Includes Zendesk ticket creation from conversations with automatic organization-based routing.

## How to Use It

### In Slack

| Method | Example |
|---|---|
| **Mention** | `@ngrok-bot how do I rate limit my endpoint?` |
| **Direct message** | Just DM the bot with your question |
| **Thread replies** | Reply in any thread where the bot has responded — it keeps context |
| **`/ngrok-ask`** | `/ngrok-ask what is Traffic Policy?` |
| **`/ngrok-yaml`** | `/ngrok-yaml rate limit API to 100 req/min` — generates YAML config |
| **`/ngrokbot-model`** | Opens a dropdown to pick your LLM (GPT-4o, Claude, Gemini, etc.) |
| **`/ngrok-ticket`** | Opens a modal to create a Zendesk support ticket |
| **`/ngrok-help`** | Shows available commands and example questions |

Every bot response includes a **🎫 Create Support Ticket** button that pre-fills a Zendesk ticket from the conversation context.

### CLI Mode (no Slack required)

```bash
python chat_cli.py
```

## Features

- 🔍 **Smart Search** — Multi-query search via ngrok's MCP server + direct doc page fetching for traffic policy actions and Kubernetes topics
- 🤖 **Multi-Provider LLM** — Choose between OpenAI (GPT-4o-mini, GPT-4o, o3-mini), Anthropic (Claude Sonnet 4, Claude 3.5 Haiku), or Google (Gemini 2.5 Flash/Pro) per user
- 🔄 **Auto-Fallback** — If your selected model's provider fails, the bot silently retries with another provider
- 📝 **YAML Examples** — Includes verbatim YAML from the docs when relevant
- 🧵 **Thread Context** — Understands follow-up questions in threads
- 🎫 **Zendesk Integration** — Create support tickets pre-filled from conversation context, with automatic organization-based routing and priority assignment
- 🎯 **Fuzzy Matching** — Handles typos in action names (e.g., "ratelimting" → rate-limit)
- 🏷️ **Query Classification** — Detects whether you're asking about the agent/CLI, Kubernetes, or the API, and tailors the response accordingly

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/ishanj12/ngrok-slack-bot.git
cd ngrok-slack-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Add your keys to `.env`:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | At least one LLM key | OpenAI API key |
| `ANTHROPIC_API_KEY` | Optional | Anthropic API key for Claude models |
| `GEMINI_API_KEY` | Optional | Google API key for Gemini models |
| `NGROK_API_KEY` | Optional | Routes OpenAI calls through the ngrok AI Gateway |
| `SLACK_BOT_TOKEN` | For Slack bot | `xoxb-...` |
| `SLACK_APP_TOKEN` | For Slack bot | `xapp-...` |
| `SLACK_SIGNING_SECRET` | For Slack bot | Signing secret from Slack app settings |
| `ZENDESK_SUBDOMAIN` | For tickets | Your Zendesk subdomain |
| `ZENDESK_EMAIL` | For tickets | Zendesk admin email |
| `ZENDESK_API_TOKEN` | For tickets | Zendesk API token |

### 3. Run

**CLI mode** (no Slack credentials needed):
```bash
python chat_cli.py
```

**Slack bot**:
```bash
python run_bot.py
```

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
│   │   ├── client.py           # MCP client — search pipeline, LLM dispatch, doc fetching
│   │   └── ngrok_assistant.py  # Async-to-sync bridge for Slack handlers
│   ├── bot/
│   │   ├── app.py              # Slack Bolt app (Socket Mode)
│   │   ├── handlers.py         # Mention/DM/slash command handlers, ticket modals
│   │   └── models.py           # Per-user model preferences (persisted to disk)
│   └── zendesk/
│       └── client.py           # Zendesk API client (tickets, org lookup, plan routing)
├── data/                       # Runtime data (model prefs, gitignored)
├── chat_cli.py                 # Interactive CLI for testing
├── run_bot.py                  # Bot startup with env checks and cleanup
├── Procfile                    # Railway deployment (worker: python run_bot.py)
└── requirements.txt
```

## Slack App Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Enable **Socket Mode**
3. Under **OAuth & Permissions**, add scopes: `app_mentions:read`, `chat:write`, `im:history`, `im:read`, `im:write`, `commands`, `users:read`, `users:read.email`
4. Under **Event Subscriptions**, subscribe to: `app_mention`, `message.im`
5. Create slash commands: `/ngrok-ask`, `/ngrok-yaml`, `/ngrok-help`, `/ngrokbot-model`, `/ngrok-ticket`
6. Enable **Interactivity & Shortcuts** (required for modals used by ticket creation and model selection)
7. Install the app to your workspace and add the tokens to `.env`

## Requirements

- Python 3.11+
- At least one LLM API key (OpenAI, Anthropic, or Gemini)
- Zendesk API credentials (for ticket creation)

## License

MIT License
