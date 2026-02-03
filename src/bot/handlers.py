import re

from src.mcp.ngrok_assistant import ask_ngrok


def _ask_and_respond(query: str, say, logger, thread_ts: str | None = None, searching_msg: str = "🔍 Searching ngrok documentation...") -> None:
    """Common helper for asking ngrok and responding in Slack."""
    say(text=searching_msg, thread_ts=thread_ts)
    
    answer = ask_ngrok(query)
    
    if answer and not answer.startswith("Error"):
        blocks = format_answer_for_slack(answer)
        say(text=answer[:200], blocks=blocks, thread_ts=thread_ts)
    else:
        logger.error(f"MCP error: {answer}")
        say(text=f"Sorry, I encountered an issue: {answer}", thread_ts=thread_ts)


def format_answer_for_slack(answer: str) -> list[dict]:
    """Format synthesized answer for Slack display"""
    
    # Remove language identifiers from code blocks (Slack doesn't support them)
    answer = re.sub(r'```(\w+)\n', '```\n', answer)
    
    blocks = []
    
    # Split answer into chunks if too long (Slack has 3000 char limit per block)
    max_len = 2900
    if len(answer) <= max_len:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": answer
            }
        })
    else:
        # Split by double newlines to preserve formatting
        parts = answer.split('\n\n')
        current_chunk = ""
        for part in parts:
            if len(current_chunk) + len(part) + 2 > max_len:
                if current_chunk:
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": current_chunk.strip()}
                    })
                current_chunk = part
            else:
                current_chunk += "\n\n" + part if current_chunk else part
        if current_chunk:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": current_chunk.strip()}
            })
    
    return blocks


def handle_mention(event, say, logger):
    """Handle when bot is mentioned"""
    try:
        user = event.get("user")
        text = event.get("text", "")
        
        query = text.split(">", 1)[-1].strip()
        
        if not query:
            say(
                text="Hi! Ask me anything about ngrok!",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Hi <@{user}>! 👋\n\nI'm your ngrok documentation assistant. Ask me anything about ngrok!\n\n*Examples:*\n• What is ngrok?\n• How do I create an HTTP tunnel?\n• Show me authentication examples\n• How do I configure Traffic Policy?"
                        }
                    }
                ]
            )
            return
        
        logger.info(f"Question: {query}")
        _ask_and_respond(query, say, logger, thread_ts=event.get("ts"))
    
    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        say(
            text=f"Sorry, I encountered an error: {str(e)}",
            thread_ts=event.get("ts")
        )


def handle_dm(event, say, logger):
    """Handle direct messages"""
    if event.get("channel_type") != "im":
        return
    
    if event.get("subtype") is not None:
        return
    
    try:
        text = event.get("text", "").strip()
        
        if not text:
            return
        
        logger.info(f"DM Question: {text}")
        _ask_and_respond(text, say, logger)
    
    except Exception as e:
        logger.error(f"Error handling DM: {e}")
        say(text=f"Sorry, I encountered an error: {str(e)}")


def handle_help(ack, command, say):
    """Handle /ngrok-help command"""
    ack()
    
    say(
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚀 ngrok Documentation Bot Help"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*How to use this bot:*\n\n1. *Mention the bot* - `@ngrok-bot your question`\n2. *Direct message* - Send a DM with your question\n3. *Use slash commands* - Try the commands below"
                }
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Available Commands:*\n\n• `/ngrok-ask <question>` - Ask a question about ngrok\n• `/ngrok-yaml <description>` - Get YAML configuration help\n• `/ngrok-ticket` - Create a support ticket\n• `/ngrok-help` - Show this help message"
                }
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Example Questions:*\n\n• What is ngrok?\n• How do I create an HTTP tunnel?\n• Show me authentication examples\n• How do I use Traffic Policy?\n• What are ngrok endpoints?"
                }
            }
        ]
    )


def handle_ask(ack, command, say, logger):
    """Handle /ngrok-ask command"""
    ack()
    
    question = command.get("text", "").strip()
    
    if not question:
        say(text="Please provide a question. Example: `/ngrok-ask What is ngrok?`")
        return
    
    try:
        _ask_and_respond(question, say, logger, searching_msg=f"🔍 Searching for: _{question}_")
    except Exception as e:
        say(text=f"Sorry, I encountered an error: {str(e)}")


def handle_yaml(ack, command, say, logger):
    """Handle /ngrok-yaml command"""
    ack()
    
    request = command.get("text", "").strip()
    
    if not request:
        say(text="Please describe what you need. Example: `/ngrok-yaml basic authentication config`")
        return
    
    try:
        query = f"Show me a YAML configuration example for: {request}"
        _ask_and_respond(query, say, logger, searching_msg=f"🔍 Finding YAML configuration for: _{request}_")
    except Exception as e:
        say(text=f"Sorry, I encountered an error: {str(e)}")


def handle_ticket_command(ack, command, client, logger):
    """Handle /ngrok-ticket command - opens a modal to create a support ticket"""
    ack()
    
    try:
        client.views_open(
            trigger_id=command["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "ticket_submission",
                "title": {"type": "plain_text", "text": "Create Support Ticket"},
                "submit": {"type": "plain_text", "text": "Submit Ticket"},
                "close": {"type": "plain_text", "text": "Cancel"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "subject_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "subject",
                            "placeholder": {"type": "plain_text", "text": "Brief description of your issue"}
                        },
                        "label": {"type": "plain_text", "text": "Subject"}
                    },
                    {
                        "type": "input",
                        "block_id": "description_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "description",
                            "multiline": True,
                            "placeholder": {"type": "plain_text", "text": "Describe your issue in detail..."}
                        },
                        "label": {"type": "plain_text", "text": "Description"}
                    },
                    {
                        "type": "input",
                        "block_id": "email_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "email",
                            "placeholder": {"type": "plain_text", "text": "your.email@company.com"}
                        },
                        "label": {"type": "plain_text", "text": "Your Email"}
                    },
                    {
                        "type": "input",
                        "block_id": "priority_block",
                        "element": {
                            "type": "static_select",
                            "action_id": "priority",
                            "placeholder": {"type": "plain_text", "text": "Select priority"},
                            "options": [
                                {"text": {"type": "plain_text", "text": "Low"}, "value": "low"},
                                {"text": {"type": "plain_text", "text": "Normal"}, "value": "normal"},
                                {"text": {"type": "plain_text", "text": "High"}, "value": "high"},
                                {"text": {"type": "plain_text", "text": "Urgent"}, "value": "urgent"}
                            ],
                            "initial_option": {"text": {"type": "plain_text", "text": "Normal"}, "value": "normal"}
                        },
                        "label": {"type": "plain_text", "text": "Priority"}
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error opening ticket modal: {e}")


def handle_ticket_submission(ack, body, client, view, logger):
    """Handle ticket modal submission - creates a Zendesk ticket"""
    ack()
    
    try:
        # Extract form values
        values = view["state"]["values"]
        subject = values["subject_block"]["subject"]["value"]
        description = values["description_block"]["description"]["value"]
        email = values["email_block"]["email"]["value"]
        priority = values["priority_block"]["priority"]["selected_option"]["value"]
        
        # Get user info
        user_id = body["user"]["id"]
        user_info = client.users_info(user=user_id)
        user_name = user_info["user"]["real_name"] or user_info["user"]["name"]
        
        # Create Zendesk ticket
        from src.zendesk.client import create_support_ticket
        
        result = create_support_ticket(
            subject=subject,
            description=f"{description}\n\n---\nSubmitted via Slack by {user_name}",
            requester_name=user_name,
            requester_email=email,
            priority=priority,
            tags=["slack", "ngrok-bot"]
        )
        
        if result.success:
            client.chat_postMessage(
                channel=user_id,
                text=f"✅ *Ticket created successfully!*\n\n"
                     f"*Ticket ID:* #{result.ticket_id}\n"
                     f"*Subject:* {subject}\n"
                     f"*Priority:* {priority.capitalize()}\n\n"
                     f"Our support team will respond to your email ({email}) shortly."
            )
            logger.info(f"Created Zendesk ticket #{result.ticket_id} for {email}")
        else:
            client.chat_postMessage(
                channel=user_id,
                text=f"❌ *Failed to create ticket*\n\nError: {result.error}\n\n"
                     f"Please try again or contact support directly."
            )
            logger.error(f"Failed to create Zendesk ticket: {result.error}")
    
    except Exception as e:
        logger.error(f"Error handling ticket submission: {e}")
        user_id = body["user"]["id"]
        client.chat_postMessage(
            channel=user_id,
            text=f"❌ Sorry, there was an error creating your ticket: {str(e)}"
        )
