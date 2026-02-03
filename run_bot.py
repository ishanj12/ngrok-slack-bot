#!/usr/bin/env python3
"""
ngrok Slack Bot - Documentation Assistant

This bot helps users find information in the ngrok documentation.
"""

import atexit
import os
import signal
import sys
from dotenv import load_dotenv

load_dotenv()


def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        "SLACK_BOT_TOKEN",
        "SLACK_APP_TOKEN",
        "SLACK_SIGNING_SECRET"
    ]
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        print("❌ Error: Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease add these to your .env file")
        return False
    
    return True


def cleanup():
    """Cleanup MCP connection on exit"""
    print("\n🧹 Cleaning up...")
    try:
        from src.mcp.ngrok_assistant import shutdown_background_loop
        shutdown_background_loop()
        print("✓ Background loop stopped")
    except Exception:
        pass
    print("👋 Goodbye!")


def main():
    """Main entry point for the bot"""
    print("=" * 60)
    print("🤖 ngrok Slack Bot - Documentation Assistant")
    print("=" * 60)
    
    if not check_environment():
        sys.exit(1)
    
    print("\n✓ Environment variables loaded")
    print("✓ Starting bot...\n")
    
    # Register cleanup handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    
    from src.bot.app import start
    
    try:
        start()
    except KeyboardInterrupt:
        print("\n\n⚡️ Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
