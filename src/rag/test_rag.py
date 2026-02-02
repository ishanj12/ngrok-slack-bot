import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.rag.retriever import NgrokDocRetriever


def test_retrieval():
    print("Initializing retriever...")
    retriever = NgrokDocRetriever(k=3)
    
    test_queries = [
        "What is ngrok and what can I do with it?",
        "How do I create an HTTP endpoint?",
        "What are Traffic Policy actions?",
        "How do I configure authentication?",
        "What is the ngrok agent?"
    ]
    
    print("\n" + "=" * 80)
    print("TESTING NGROK DOCUMENTATION RETRIEVAL")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 80)
        
        docs = retriever.retrieve(query, k=2)
        
        for i, doc in enumerate(docs, 1):
            print(f"\n✓ Result {i}:")
            print(f"  Title: {doc.metadata.get('title', 'Untitled')}")
            print(f"  Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"  Preview: {doc.page_content[:250].strip()}...")
            print()
        
        print("=" * 80)
    
    print("\n✅ RAG retrieval system is working correctly!")
    print("\nNext steps:")
    print("  1. Add OpenAI credits to test the full RAG pipeline with LLM")
    print("  2. Or integrate with Slack bot to use retrieval-only mode")


if __name__ == "__main__":
    test_retrieval()
