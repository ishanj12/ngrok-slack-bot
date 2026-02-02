import os
from typing import List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from src.rag.retriever import NgrokDocRetriever

load_dotenv()


class NgrokRAGGenerator:
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        retriever: NgrokDocRetriever = None
    ):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
        
        self.retriever = retriever if retriever else NgrokDocRetriever()
        
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert ngrok support assistant. Your role is to help users understand and use ngrok effectively.

Use the following documentation context to answer the user's question. If you can provide code examples or YAML configurations from the context, include them in your response.

If the answer is not in the provided context, say "I don't have enough information in the documentation to answer that question. You may want to check the official ngrok documentation at https://ngrok.com/docs or contact ngrok support."

Be concise, helpful, and accurate. Format your responses clearly with proper markdown.

Context:
{context}"""),
            ("user", "{question}")
        ])
        
        self.yaml_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert ngrok configuration assistant specializing in YAML configurations.

Based on the provided ngrok documentation context, help the user create or understand YAML configurations for ngrok.

Provide complete, valid YAML configurations with explanations. Include comments in the YAML to explain each section.

If the context doesn't contain enough information to create the requested configuration, explain what information is missing.

Context:
{context}"""),
            ("user", "{question}")
        ])
        
        self.qa_chain = (
            {"context": self._format_docs, "question": RunnablePassthrough()}
            | self.qa_prompt
            | self.llm
            | StrOutputParser()
        )
    
    def _format_docs(self, question: str) -> str:
        docs = self.retriever.retrieve(question)
        return "\n\n".join([doc.page_content for doc in docs])
    
    def generate_answer(self, question: str) -> str:
        return self.qa_chain.invoke(question)
    
    def generate_yaml_config(self, request: str) -> str:
        docs = self.retriever.retrieve(request)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        response = self.yaml_prompt.invoke({
            "context": context,
            "question": request
        })
        
        return self.llm.invoke(response).content
    
    def chat(self, message: str, is_yaml_request: bool = False) -> str:
        if is_yaml_request or any(keyword in message.lower() for keyword in ['yaml', 'config', 'configuration']):
            return self.generate_yaml_config(message)
        else:
            return self.generate_answer(message)


if __name__ == "__main__":
    print("Initializing RAG Generator...")
    generator = NgrokRAGGenerator()
    
    print("\n" + "=" * 60)
    print("Testing RAG Pipeline")
    print("=" * 60 + "\n")
    
    test_questions = [
        "What is ngrok?",
        "How do I create an HTTP tunnel?",
        "Show me a YAML configuration example"
    ]
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        print("-" * 60)
        answer = generator.chat(question)
        print(f"\nAnswer:\n{answer}")
        print("\n" + "=" * 60)
