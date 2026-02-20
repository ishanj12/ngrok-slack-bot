import json
import os
import re

from src.mcp.ngrok_assistant import ask_ngrok, generate_ngrok_yaml

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def _ask_and_respond(query: str, say, logger, thread_ts: str | None = None, searching_msg: str = "🔍 Searching ngrok documentation...", channel: str | None = None, thread_context: str = "") -> None:
    """Common helper for asking ngrok and responding in Slack."""
    say(text=searching_msg, thread_ts=thread_ts)
    
    answer = ask_ngrok(query, thread_context=thread_context)
    
    if answer and not answer.startswith("Error"):
        blocks = format_answer_for_slack(answer)
        if not thread_context:
            blocks.append({"type": "divider"})
            button_data = {"channel": channel or "", "thread_ts": thread_ts or ""}
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🎫 Create Support Ticket"},
                        "style": "primary",
                        "action_id": "create_ticket_from_conversation",
                        "value": json.dumps(button_data)
                    }
                ]
            })
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


def handle_mention(event, say, client, logger):
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
        
        thread_context = ""
        thread_ts = event.get("thread_ts")
        if thread_ts and thread_ts != event.get("ts"):
            thread_context = fetch_thread_messages(client, event["channel"], thread_ts, logger)
        
        _ask_and_respond(query, say, logger, thread_ts=thread_ts or event.get("ts"), channel=event.get("channel"), thread_context=thread_context)
    
    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        say(
            text=f"Sorry, I encountered an error: {str(e)}",
            thread_ts=event.get("ts")
        )


def handle_dm(event, say, client, logger):
    """Handle direct messages and threaded replies to the bot"""
    logger.info(f"Message event received: channel_type={event.get('channel_type')}, thread_ts={event.get('thread_ts')}, ts={event.get('ts')}, subtype={event.get('subtype')}, text={event.get('text', '')[:50]}")
    
    if event.get("subtype") is not None:
        return
    
    text = event.get("text", "")
    if re.match(r'<@\w+>', text):
        return
    
    is_dm = event.get("channel_type") == "im"
    is_thread_reply = event.get("thread_ts") is not None and event.get("thread_ts") != event.get("ts")
    
    if not is_dm and not is_thread_reply:
        return
    
    # For thread replies in channels, only respond if the bot participated in the thread
    if is_thread_reply and not is_dm:
        try:
            result = client.conversations_replies(
                channel=event["channel"], ts=event["thread_ts"], limit=50
            )
            bot_info = client.auth_test()
            bot_user_id = bot_info["user_id"]
            bot_in_thread = any(
                msg.get("user") == bot_user_id or msg.get("bot_id")
                for msg in result.get("messages", [])
            )
            if not bot_in_thread:
                return
        except Exception as e:
            logger.error(f"Error checking thread participation: {e}")
            return
    
    try:
        text = event.get("text", "").strip()
        
        if not text:
            return
        
        logger.info(f"DM Question: {text}")
        
        thread_context = ""
        thread_ts = event.get("thread_ts")
        if thread_ts and thread_ts != event.get("ts"):
            thread_context = fetch_thread_messages(client, event["channel"], thread_ts, logger)
        
        _ask_and_respond(text, say, logger, thread_ts=thread_ts, channel=event.get("channel"), thread_context=thread_context)
    
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
    """Handle /ngrok-yaml command - generates custom YAML configurations"""
    ack()
    
    request = command.get("text", "").strip()
    
    if not request:
        say(text="Please describe what you need. Example: `/ngrok-yaml rate limit API to 100 requests per minute`")
        return
    
    try:
        say(text=f"⚙️ Generating YAML configuration for: _{request}_")
        
        result = generate_ngrok_yaml(request)
        
        if result and not result.startswith("Error"):
            blocks = format_answer_for_slack(result)
            say(text=result[:200], blocks=blocks)
        else:
            logger.error(f"YAML generation error: {result}")
            say(text=f"Sorry, I couldn't generate that configuration: {result}")
    except Exception as e:
        logger.error(f"Error in handle_yaml: {e}")
        say(text=f"Sorry, I encountered an error: {str(e)}")


def _get_user_email(client, user_id: str, logger) -> str:
    """Fetch a Slack user's email from their profile."""
    try:
        user_info = client.users_info(user=user_id)
        return user_info["user"].get("profile", {}).get("email", "")
    except Exception as e:
        logger.error(f"Error fetching user email: {e}")
        return ""


def handle_ticket_command(ack, command, client, logger):
    """Handle /ngrok-ticket command - opens a modal to create a support ticket"""
    ack()
    
    try:
        user_email = _get_user_email(client, command["user_id"], logger)
        client.views_open(
            trigger_id=command["trigger_id"],
            view=_build_ticket_modal(email=user_email)
        )
    except Exception as e:
        logger.error(f"Error opening ticket modal: {e}")


def _build_email_block(email: str = "") -> dict:
    """Build the email input block, pre-filled if email is available."""
    element = {
        "type": "plain_text_input",
        "action_id": "email",
        "placeholder": {"type": "plain_text", "text": "your.email@company.com"}
    }
    if email:
        element["initial_value"] = email
    return {
        "type": "input",
        "block_id": "email_block",
        "element": element,
        "label": {"type": "plain_text", "text": "Your Email"}
    }


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


def fetch_thread_messages(client, channel: str, thread_ts: str, logger) -> str:
    """Fetch all messages in a Slack thread and return as formatted context."""
    try:
        result = client.conversations_replies(channel=channel, ts=thread_ts, limit=50)
        messages = result.get("messages", [])
        
        thread_text = []
        for msg in messages:
            user = msg.get("user", "unknown")
            text = msg.get("text", "")
            if msg.get("bot_id"):
                thread_text.append(f"Bot: {text}")
            else:
                thread_text.append(f"User ({user}): {text}")
        
        return "\n\n".join(thread_text)
    except Exception as e:
        logger.error(f"Error fetching thread messages: {e}")
        return ""


def synthesize_ticket_content(thread_context: str) -> dict:
    """Use OpenAI to synthesize a ticket subject and description from thread messages."""
    if not HAS_OPENAI or not os.environ.get("OPENAI_API_KEY"):
        return {
            "subject": thread_context[:100],
            "description": thread_context[:3000]
        }
    
    client = OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You synthesize support ticket content from a Slack thread conversation between a user and an ngrok documentation bot.

Given the full thread, create:
1. A concise ticket subject (max 100 chars) that captures the user's core issue
2. A clear description that explains what the user needs help with

Respond in JSON format:
{"subject": "...", "description": "..."}

The description should:
- Summarize what the user was trying to accomplish
- Reference key details from the conversation
- Note what information the bot provided
- Indicate why additional support may be needed"""
            },
            {
                "role": "user",
                "content": f"Slack thread conversation:\n\n{thread_context}"
            }
        ],
        temperature=0.3,
        max_tokens=500
    )
    
    try:
        content = response.choices[0].message.content
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(content)
    except (json.JSONDecodeError, IndexError):
        return {
            "subject": thread_context[:100],
            "description": thread_context[:3000]
        }


def _build_ticket_modal(subject: str = "", description: str = "", email: str = "", loading: bool = False) -> dict:
    """Build the ticket submission modal view."""
    blocks = []
    if loading:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "⏳ *Loading conversation context...*"}]
        })
    elif subject or description:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "📝 *Pre-filled from your conversation.* Feel free to edit."}]
        })

    blocks.extend([
        {
            "type": "input",
            "block_id": "subject_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "subject",
                **({"initial_value": subject[:150]} if subject else {}),
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
                **({"initial_value": description[:3000]} if description else {}),
                "placeholder": {"type": "plain_text", "text": "Describe your issue in detail..."}
            },
            "label": {"type": "plain_text", "text": "Description"}
        },
        _build_email_block(email),
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
    ])

    return {
        "type": "modal",
        "callback_id": "ticket_submission",
        "title": {"type": "plain_text", "text": "Create Support Ticket"},
        "submit": {"type": "plain_text", "text": "Submit Ticket"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": blocks
    }


def handle_create_ticket_button(ack, body, client, logger):
    """Handle the 'Create Support Ticket' button click from conversation."""
    ack()
    
    user_id = body["user"]["id"]
    
    try:
        user_email = _get_user_email(client, user_id, logger)

        result = client.views_open(
            trigger_id=body["trigger_id"],
            view=_build_ticket_modal(email=user_email, loading=True)
        )
        view_id = result["view"]["id"]

        action = body["actions"][0]
        button_data = json.loads(action["value"])
        channel = button_data.get("channel", "")
        thread_ts = button_data.get("thread_ts", "")
        
        thread_context = ""
        if channel and thread_ts:
            thread_context = fetch_thread_messages(client, channel, thread_ts, logger)
        
        ticket_content = synthesize_ticket_content(thread_context) if thread_context else {}

        client.views_update(
            view_id=view_id,
            view=_build_ticket_modal(
                subject=ticket_content.get("subject", ""),
                description=ticket_content.get("description", ""),
                email=user_email,
            )
        )
    except Exception as e:
        logger.error(f"Error opening ticket modal from button: {e}")
        client.chat_postMessage(
            channel=user_id,
            text=f"❌ Sorry, there was an error opening the ticket form: {str(e)}"
        )
