# Slack App Setup Guide

This guide walks you through setting up a Slack app for the ngrok Documentation Bot.

## Step 1: Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Select **"From scratch"**
4. Enter app name: `ngrok Bot` (or your preferred name)
5. Select your workspace
6. Click **"Create App"**

## Step 2: Configure OAuth & Permissions

1. In the left sidebar, click **OAuth & Permissions**
2. Scroll down to **Bot Token Scopes**
3. Click **Add an OAuth Scope** and add these scopes:

   ```
   app_mentions:read    - View messages that mention the bot
   chat:write           - Send messages as the bot
   channels:history     - View messages in public channels
   im:history           - View messages in direct messages
   im:read              - View basic info about DMs
   im:write             - Start DMs with users
   commands             - Add slash commands
   ```

4. Scroll to the top and click **Install to Workspace**
5. Click **Allow**
6. **Copy the Bot User OAuth Token** (starts with `xoxb-`)
   - Save this as `SLACK_BOT_TOKEN` in your `.env` file

## Step 3: Enable Socket Mode

1. In the left sidebar, click **Socket Mode**
2. Toggle **Enable Socket Mode** to ON
3. Enter a token name (e.g., `ngrok-bot-socket`)
4. Add the `connections:write` scope
5. Click **Generate**
6. **Copy the App-Level Token** (starts with `xapp-`)
   - Save this as `SLACK_APP_TOKEN` in your `.env` file

## Step 4: Subscribe to Events

1. In the left sidebar, click **Event Subscriptions**
2. Toggle **Enable Events** to ON
3. Under **Subscribe to bot events**, click **Add Bot User Event**
4. Add these events:
   ```
   app_mention      - When someone mentions the bot
   message.im       - When someone sends a DM to the bot
   ```
5. Click **Save Changes**

## Step 5: Add Slash Commands

1. In the left sidebar, click **Slash Commands**
2. Click **Create New Command**

### Command 1: /ngrok-ask

```
Command: /ngrok-ask
Request URL: (leave empty for Socket Mode)
Short Description: Ask a question about ngrok
Usage Hint: What is ngrok?
```

### Command 2: /ngrok-yaml

```
Command: /ngrok-yaml
Request URL: (leave empty for Socket Mode)
Short Description: Get YAML configuration help
Usage Hint: authentication config
```

### Command 3: /ngrok-help

```
Command: /ngrok-help
Request URL: (leave empty for Socket Mode)
Short Description: Show help message
Usage Hint:
```

3. Click **Save** for each command

## Step 6: Get Signing Secret

1. In the left sidebar, click **Basic Information**
2. Scroll down to **App Credentials**
3. **Copy the Signing Secret**
   - Save this as `SLACK_SIGNING_SECRET` in your `.env` file

## Step 7: Customize App (Optional)

1. In the left sidebar, click **Basic Information**
2. Under **Display Information**, you can:
   - Upload an app icon
   - Add a description
   - Set background color

## Step 8: Update .env File

Your `.env` file should now have all three values:

```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
```

## Step 9: Invite Bot to Channels

1. Open Slack
2. Go to any channel where you want to use the bot
3. Type `/invite @ngrok Bot` (or your app name)
4. The bot will join the channel

## Step 10: Test the Bot

Run the bot:
```bash
python run_bot.py
```

In Slack, try:
```
@ngrok Bot What is ngrok?
```

Or send a DM:
```
How do I create an HTTP tunnel?
```

Or use a slash command:
```
/ngrok-ask What are Traffic Policy actions?
```

## Troubleshooting

### Bot doesn't respond to mentions
- Make sure the bot is invited to the channel (`/invite @ngrok Bot`)
- Check that `app_mentions:read` scope is added
- Verify `app_mention` event is subscribed

### Bot doesn't respond to DMs
- Check that `im:history` and `im:read` scopes are added
- Verify `message.im` event is subscribed
- Try reinstalling the app after adding scopes

### Slash commands don't work
- Make sure Socket Mode is enabled
- Verify the commands are created in Slack App settings
- Check that the bot is running

### Invalid token errors
- Double-check your `.env` file has the correct tokens
- Make sure there are no extra spaces in the token values
- Verify you copied the full token (they're quite long)

## Next Steps

Once your bot is working:
1. Test different types of questions
2. Try the slash commands
3. Experiment with YAML configuration queries
4. Share the bot with your team!
