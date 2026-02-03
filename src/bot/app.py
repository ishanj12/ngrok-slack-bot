import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)


@app.event("app_mention")
def handle_app_mention(event, say, logger):
    """Handle when the bot is mentioned in a channel"""
    from src.bot.handlers import handle_mention
    handle_mention(event, say, logger)


@app.event("message")
def handle_message_events(event, say, logger):
    """Handle direct messages to the bot"""
    from src.bot.handlers import handle_dm
    handle_dm(event, say, logger)


@app.command("/ngrok-help")
def handle_help_command(ack, command, say):
    """Handle /ngrok-help slash command"""
    from src.bot.handlers import handle_help
    handle_help(ack, command, say)


@app.command("/ngrok-ask")
def handle_ask_command(ack, command, say, logger):
    """Handle /ngrok-ask slash command"""
    from src.bot.handlers import handle_ask
    handle_ask(ack, command, say, logger)


@app.command("/ngrok-yaml")
def handle_yaml_command(ack, command, say, logger):
    """Handle /ngrok-yaml slash command"""
    from src.bot.handlers import handle_yaml
    handle_yaml(ack, command, say, logger)


@app.command("/ngrok-ticket")
def handle_ticket_command(ack, command, client, logger):
    """Handle /ngrok-ticket slash command - opens ticket creation modal"""
    from src.bot.handlers import handle_ticket_command
    handle_ticket_command(ack, command, client, logger)


@app.view("ticket_submission")
def handle_ticket_submission(ack, body, client, view, logger):
    """Handle ticket modal submission"""
    from src.bot.handlers import handle_ticket_submission
    handle_ticket_submission(ack, body, client, view, logger)


def start():
    """Start the Slack bot"""
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    print("⚡️ ngrok Slack Bot is running!")
    handler.start()


if __name__ == "__main__":
    start()
