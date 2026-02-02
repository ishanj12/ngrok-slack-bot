import os
from typing import List
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

load_dotenv()


class NgrokDocRetriever:
    def __init__(
        self,
        vectorstore_path: str = "data/vectorstore",
        collection_name: str = "ngrok_docs",
        k: int = 5
    ):
        self.vectorstore_path = vectorstore_path
        self.collection_name = collection_name
        self.k = k
        
        print("Loading embeddings model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        print(f"Loading vector store from {vectorstore_path}...")
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=vectorstore_path
        )
        
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        print("Retriever ready!")
    
    def retrieve(self, query: str, k: int = None) -> List[Document]:
        if k is None:
            k = self.k
        
        docs = self.vectorstore.similarity_search(query, k=k)
        return docs
    
    def retrieve_with_scores(self, query: str, k: int = None) -> List[tuple]:
        if k is None:
            k = self.k
        
        docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=k)
        return docs_with_scores
    
    def format_docs(self, docs: List[Document]) -> str:
        formatted = []
        for i, doc in enumerate(docs, 1):
            formatted.append(f"--- Document {i} ---")
            formatted.append(f"Source: {doc.metadata.get('source', 'Unknown')}")
            formatted.append(f"Title: {doc.metadata.get('title', 'Untitled')}")
            formatted.append(f"\nContent:\n{doc.page_content}\n")
        return "\n".join(formatted)


if __name__ == "__main__":
    retriever = NgrokDocRetriever()
    
    test_queries = [
        "How do I install ngrok?",
        "What is an ngrok tunnel?",
        "How to configure YAML for ngrok?"
    ]
    
    print("\n" + "=" * 60)
    print("Testing Retriever")
    print("=" * 60 + "\n")
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        
        docs = retriever.retrieve(query, k=3)
        
        for i, doc in enumerate(docs, 1):
            print(f"\n[Result {i}]")
            print(f"Title: {doc.metadata.get('title', 'Untitled')}")
            print(f"Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"Preview: {doc.page_content[:200]}...")
        
        print("\n" + "=" * 60)
