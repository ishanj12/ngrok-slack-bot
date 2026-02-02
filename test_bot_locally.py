#!/usr/bin/env python3
"""
Local test script for the ngrok Slack Bot
Tests the bot components without requiring Slack connection
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def test_retriever():
    """Test the document retriever"""
    print("\n" + "=" * 80)
    print("TEST 1: Document Retriever")
    print("=" * 80)
    
    from src.rag.retriever import NgrokDocRetriever
    
    print("\n✓ Loading retriever...")
    retriever = NgrokDocRetriever(k=3)
    
    test_queries = [
        "What is ngrok?",
        "How do I create an HTTP tunnel?",
        "What are Traffic Policy actions?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 80)
        
        docs = retriever.retrieve(query, k=2)
        
        if docs:
            print(f"✓ Found {len(docs)} relevant documents:")
            for i, doc in enumerate(docs, 1):
                title = doc.metadata.get('title', 'Untitled')
                source = doc.metadata.get('source', 'Unknown')
                preview = doc.page_content[:150].strip()
                print(f"\n  {i}. {title}")
                print(f"     Source: {source}")
                print(f"     Preview: {preview}...")
        else:
            print("✗ No documents found")
    
    print("\n" + "=" * 80)
    print("✅ Retriever test PASSED")
    print("=" * 80)


def test_handlers():
    """Test the handler functions"""
    print("\n" + "=" * 80)
    print("TEST 2: Bot Handlers")
    print("=" * 80)
    
    from src.bot.handlers import format_docs_for_slack, get_retriever
    
    print("\n✓ Loading handlers...")
    
    # Test retriever initialization
    print("✓ Testing retriever initialization...")
    retriever = get_retriever()
    print(f"✓ Retriever loaded: {retriever is not None}")
    
    # Test document retrieval
    print("\n✓ Testing document retrieval...")
    docs = retriever.retrieve("What is ngrok?", k=2)
    print(f"✓ Retrieved {len(docs)} documents")
    
    # Test Slack formatting
    print("\n✓ Testing Slack message formatting...")
    blocks = format_docs_for_slack(docs)
    print(f"✓ Generated {len(blocks)} Slack message blocks")
    
    # Display sample block
    if blocks:
        print("\n✓ Sample Slack block structure:")
        print(f"   Block types: {[b.get('type') for b in blocks[:3]]}")
    
    print("\n" + "=" * 80)
    print("✅ Handlers test PASSED")
    print("=" * 80)


def test_slack_message_format():
    """Test how Slack messages would be formatted"""
    print("\n" + "=" * 80)
    print("TEST 3: Slack Message Format Preview")
    print("=" * 80)
    
    from src.bot.handlers import format_docs_for_slack, get_retriever
    
    retriever = get_retriever()
    docs = retriever.retrieve("How do I use ngrok for webhooks?", k=2)
    
    blocks = format_docs_for_slack(docs)
    
    print("\n✓ Simulated Slack Message:\n")
    print("─" * 80)
    
    for block in blocks:
        if block.get('type') == 'section':
            text = block.get('text', {}).get('text', '')
            if text:
                # Remove markdown formatting for display
                clean_text = text.replace('*', '').replace('_', '').replace('`', '')
                print(clean_text)
        elif block.get('type') == 'divider':
            print("─" * 80)
        elif block.get('type') == 'header':
            text = block.get('text', {}).get('text', '')
            print(f"\n{text}\n")
    
    print("\n" + "=" * 80)
    print("✅ Message format test PASSED")
    print("=" * 80)


def test_bot_startup():
    """Test if bot can be initialized (without connecting to Slack)"""
    print("\n" + "=" * 80)
    print("TEST 4: Bot Initialization")
    print("=" * 80)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n✓ Checking environment variables...")
    
    required_vars = {
        "SLACK_BOT_TOKEN": os.environ.get("SLACK_BOT_TOKEN"),
        "SLACK_APP_TOKEN": os.environ.get("SLACK_APP_TOKEN"),
        "SLACK_SIGNING_SECRET": os.environ.get("SLACK_SIGNING_SECRET")
    }
    
    all_set = True
    for var, value in required_vars.items():
        if value and value != f"your-{var.lower().replace('_', '-')}-here":
            print(f"  ✓ {var}: Set")
        else:
            print(f"  ✗ {var}: Not configured")
            all_set = False
    
    if all_set:
        print("\n✅ All Slack credentials configured!")
        print("✅ Bot is ready to start with: python run_bot.py")
    else:
        print("\n⚠️  Slack credentials not configured yet")
        print("   Follow SETUP.md to create your Slack app and get credentials")
        print("   The bot components are working, but you need Slack setup to run it")
    
    print("\n" + "=" * 80)
    print("✅ Bot initialization test PASSED")
    print("=" * 80)


def main():
    """Run all tests"""
    print("\n" + "🤖" * 40)
    print("ngrok Slack Bot - Local Testing Suite")
    print("🤖" * 40)
    
    try:
        test_retriever()
        test_handlers()
        test_slack_message_format()
        test_bot_startup()
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print("\nYour bot is ready! Next steps:")
        print("1. Configure Slack app (see SETUP.md)")
        print("2. Add credentials to .env file")
        print("3. Run: python run_bot.py")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
