#!/usr/bin/env python3
"""
Quick demo of the ngrok Documentation Bot
Runs a few example queries to show how it works
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.rag.retriever import NgrokDocRetriever


def demo():
    print("\n" + "🤖" * 40)
    print("ngrok Documentation Bot - Quick Demo")
    print("🤖" * 40 + "\n")
    
    print("Loading bot...")
    retriever = NgrokDocRetriever(k=2)
    print("✅ Bot ready!\n")
    
    demo_questions = [
        "What is ngrok?",
        "How do I create an HTTP tunnel?",
        "What are Traffic Policy actions?",
        "How do I configure authentication?",
        "Show me webhook examples"
    ]
    
    for i, question in enumerate(demo_questions, 1):
        print("\n" + "=" * 80)
        print(f"Demo Question {i}/{len(demo_questions)}: {question}")
        print("=" * 80)
        
        docs = retriever.retrieve(question, k=2)
        
        if docs:
            for j, doc in enumerate(docs, 1):
                title = doc.metadata.get('title', 'Untitled')
                source = doc.metadata.get('source', 'Unknown')
                preview = doc.page_content[:300].strip()
                
                print(f"\n📄 Result {j}:")
                print(f"   Title: {title}")
                print(f"   Source: {source}")
                print(f"\n   {preview}...")
        else:
            print("\n   No results found.")
        
        if i < len(demo_questions):
            input("\n   Press Enter for next question...")
    
    print("\n" + "=" * 80)
    print("✅ Demo complete!")
    print("=" * 80)
    print("\n💡 To use the interactive bot, run: python chat_cli.py")
    print("\n")


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
