import os
import json
from typing import List, Dict
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

load_dotenv()


class NgrokDocIndexer:
    def __init__(
        self,
        docs_path: str = "data/raw/ngrok_docs.json",
        vectorstore_path: str = "data/vectorstore",
        collection_name: str = "ngrok_docs"
    ):
        self.docs_path = docs_path
        self.vectorstore_path = vectorstore_path
        self.collection_name = collection_name
        print("Loading HuggingFace embeddings model (first time may take a moment)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_documents(self) -> List[Dict]:
        print(f"Loading documents from {self.docs_path}...")
        with open(self.docs_path, 'r', encoding='utf-8') as f:
            docs = json.load(f)
        print(f"Loaded {len(docs)} documents")
        return docs
    
    def create_langchain_documents(self, raw_docs: List[Dict]) -> List[Document]:
        documents = []
        
        for idx, doc in enumerate(raw_docs):
            content_parts = []
            
            if doc.get('title'):
                content_parts.append(f"# {doc['title']}\n")
            
            if doc.get('content'):
                content_parts.append(doc['content'])
            
            if doc.get('code_blocks'):
                content_parts.append("\n\n## Code Examples:\n")
                for i, code in enumerate(doc['code_blocks'][:5], 1):
                    content_parts.append(f"\n```\n{code}\n```\n")
            
            full_content = "\n".join(content_parts)
            
            if full_content.strip():
                metadata = {
                    'source': doc.get('url', ''),
                    'title': doc.get('title', 'Untitled'),
                    'doc_id': idx,
                    'has_code': len(doc.get('code_blocks', [])) > 0,
                    'has_yaml': len(doc.get('yaml_examples', [])) > 0,
                    'num_headings': len(doc.get('headings', []))
                }
                
                documents.append(Document(
                    page_content=full_content,
                    metadata=metadata
                ))
        
        print(f"Created {len(documents)} LangChain documents")
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        print("Splitting documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"Created {len(chunks)} chunks")
        return chunks
    
    def create_vectorstore(self, chunks: List[Document]) -> Chroma:
        print(f"Creating vector store at {self.vectorstore_path}...")
        print("Generating embeddings (this may take a few minutes)...")
        
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            persist_directory=self.vectorstore_path
        )
        
        print(f"Vector store created with {len(chunks)} chunks")
        return vectorstore
    
    def run(self):
        print("=" * 60)
        print("Starting ngrok Documentation Indexing")
        print("=" * 60)
        
        raw_docs = self.load_documents()
        
        documents = self.create_langchain_documents(raw_docs)
        
        chunks = self.split_documents(documents)
        
        vectorstore = self.create_vectorstore(chunks)
        
        print("\n" + "=" * 60)
        print("Indexing Complete!")
        print("=" * 60)
        print(f"Vector store location: {self.vectorstore_path}")
        print(f"Collection name: {self.collection_name}")
        print(f"Total chunks indexed: {len(chunks)}")
        
        return vectorstore


if __name__ == "__main__":
    indexer = NgrokDocIndexer()
    indexer.run()
