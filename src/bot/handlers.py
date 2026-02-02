import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.mcp.ngrok_assistant import ask_ngrok


def format_answer_for_slack(answer: str):
    """Format synthesized answer for Slack display"""
    import re
    
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
        
        say(text="🔍 Searching ngrok documentation...", thread_ts=event.get("ts"))
        
        answer = ask_ngrok(query)
        
        if answer and not answer.startswith("Error"):
            blocks = format_answer_for_slack(answer)
            say(
                text=answer[:200],
                blocks=blocks,
                thread_ts=event.get("ts")
            )
        else:
            logger.error(f"MCP error: {answer}")
            say(
                text=f"Sorry, I encountered an issue: {answer}",
                thread_ts=event.get("ts")
            )
    
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
        
        say(text="🔍 Searching ngrok documentation...")
        
        answer = ask_ngrok(text)
        
        if answer and not answer.startswith("Error"):
            blocks = format_answer_for_slack(answer)
            say(text=answer[:200], blocks=blocks)
        else:
            logger.error(f"MCP error: {answer}")
            say(text=f"Sorry, I encountered an issue: {answer}")
    
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
                    "text": "*Available Commands:*\n\n• `/ngrok-ask <question>` - Ask a question about ngrok\n• `/ngrok-yaml <description>` - Get YAML configuration help\n• `/ngrok-help` - Show this help message"
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


def handle_ask(ack, command, say):
    """Handle /ngrok-ask command"""
    ack()
    
    question = command.get("text", "").strip()
    
    if not question:
        say(text="Please provide a question. Example: `/ngrok-ask What is ngrok?`")
        return
    
    try:
        say(text=f"🔍 Searching for: _{question}_")
        
        answer = ask_ngrok(question)
        
        if answer and not answer.startswith("Error"):
            blocks = format_answer_for_slack(answer)
            say(text=answer[:200], blocks=blocks)
        else:
            say(text=f"Sorry, I encountered an issue: {answer}")
    
    except Exception as e:
        say(text=f"Sorry, I encountered an error: {str(e)}")


def handle_yaml(ack, command, say):
    """Handle /ngrok-yaml command"""
    ack()
    
    request = command.get("text", "").strip()
    
    if not request:
        say(text="Please describe what you need. Example: `/ngrok-yaml basic authentication config`")
        return
    
    try:
        say(text=f"🔍 Finding YAML configuration for: _{request}_")
        
        answer = ask_ngrok(f"Show me a YAML configuration example for: {request}")
        
        if answer and not answer.startswith("Error"):
            blocks = format_answer_for_slack(answer)
            say(text=answer[:200], blocks=blocks)
        else:
            say(text=f"Sorry, I encountered an issue: {answer}")
    
    except Exception as e:
        say(text=f"Sorry, I encountered an error: {str(e)}")
