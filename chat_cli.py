#!/usr/bin/env python3
"""
Command-line interface for the ngrok Documentation Bot
Uses MCP client to connect to ngrok-mcp server
"""

import sys
import asyncio

from dotenv import load_dotenv
load_dotenv()

from src.mcp.client import NgrokMCPClient


class NgrokChatCLI:
    def __init__(self):
        self.client: NgrokMCPClient | None = None
    
    async def initialize(self):
        """Initialize the MCP client connection."""
        print("🤖 Connecting to ngrok-mcp server...")
        self.client = await NgrokMCPClient.connect()
        
        tools = await self.client.list_tools()
        print(f"✅ Connected! Available tools: {', '.join(tools)}\n")
    
    async def shutdown(self):
        """Shutdown the MCP client connection."""
        await NgrokMCPClient.disconnect()
    
    async def ask(self, question: str):
        """Ask a question and get a synthesized answer"""
        if not question.strip():
            return
        
        if self.client is None:
            print("❌ Not connected to MCP server")
            return
        
        print(f"\n🔍 Searching ngrok docs...")
        
        try:
            answer = await self.client.ask(question)
            print("\n" + "=" * 80)
            print(answer)
            print("=" * 80)
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    async def run(self):
        """Run the interactive CLI"""
        await self.initialize()
        
        print("=" * 80)
        print("🚀 ngrok Documentation Bot - CLI Mode (MCP)")
        print("=" * 80)
        print("\nAsk me anything about ngrok! Type 'exit' or 'quit' to stop.\n")
        print("💡 Example questions:")
        print("   • What is ngrok?")
        print("   • How do I create an HTTP tunnel?")
        print("   • What are Traffic Policy actions?")
        print("   • How do I configure authentication?")
        print("   • Show me YAML configuration examples")
        print("\n💡 Special commands:")
        print("   • list    - List available documentation")
        print("   • cache   - Show cache status")
        print("   • tools   - List available MCP tools")
        print("\n" + "=" * 80)
        
        while True:
            try:
                question = input("\n❓ Your question: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['exit', 'quit', 'q', 'bye']:
                    print("\n👋 Thanks for using ngrok Documentation Bot!")
                    break
                
                if question.lower() in ['help', '?']:
                    print("\n📖 Commands:")
                    print("   • Ask any question about ngrok")
                    print("   • 'list' - List available docs")
                    print("   • 'cache' - Show cache status")
                    print("   • 'tools' - List MCP tools")
                    print("   • 'exit' or 'quit' to stop")
                    continue
                
                if question.lower() == 'list':
                    result = await self.client.list_docs()
                    print(f"\n📚 Available documentation:\n{result}")
                    continue
                
                if question.lower() == 'cache':
                    result = await self.client.docs_cache_status()
                    print(f"\n💾 Cache status:\n{result}")
                    continue
                
                if question.lower() == 'tools':
                    tools = await self.client.list_tools()
                    print(f"\n🛠️ Available tools: {', '.join(tools)}")
                    continue
                
                await self.ask(question)
            
            except KeyboardInterrupt:
                print("\n\n👋 Thanks for using ngrok Documentation Bot!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


async def async_main():
    bot = NgrokChatCLI()
    try:
        await bot.run()
    finally:
        await bot.shutdown()


def main():
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"\n❌ Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
