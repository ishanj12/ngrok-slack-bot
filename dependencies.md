# Project Dependencies

This document outlines all the packages and libraries required for the Slack Chatbot for ngrok Documentation project.

## Core Dependencies

### Slack Integration
- **slack-bolt** - Official Slack framework for building Slack apps in Python
  - Handles authentication, token rotation, and rate limiting automatically
  - Built on top of slack-sdk
  - Provides event handlers and middleware support

- **slack-sdk** - Official Python SDK for Slack APIs
  - Installed automatically as a dependency of slack-bolt
  - Provides low-level access to Slack Web API and Socket Mode

### RAG (Retrieval-Augmented Generation) System

#### LLM Framework
- **langchain** - Framework for developing applications powered by language models
  - Provides abstractions for LLM interactions
  - Supports chains, agents, and memory
  - Core framework for building RAG pipeline

- **langchain-community** - Community-contributed integrations for LangChain
  - Additional document loaders
  - Extra vector stores and utilities
  - Community tools and integrations

- **langchain-core** - Core abstractions for LangChain
  - Installed automatically as dependency
  - Provides base classes and interfaces

- **langchain-text-splitters** - Text splitting utilities
  - Installed automatically as dependency
  - RecursiveCharacterTextSplitter for chunking documents

- **langchain-openai** - OpenAI integrations for LangChain
  - OpenAI LLM integration (GPT-4, GPT-4o-mini)
  - OpenAI embeddings (text-embedding-3-small/large)
  - Chat models and function calling

#### Vector Database
- **chromadb** - Open-source embedding database
  - Stores and retrieves vector embeddings
  - Supports similarity search
  - Provides both in-memory and persistent storage options

### Document Processing & Scraping

- **beautifulsoup4** - HTML/XML parsing library
  - Scrapes ngrok documentation from web pages
  - Extracts content, headings, code blocks
  - Navigates HTML structure

- **lxml** - XML and HTML processing library
  - Parser backend for BeautifulSoup
  - Fast and efficient parsing

- **requests** - HTTP library for Python
  - Makes HTTP requests to fetch documentation pages
  - Simple and elegant API

- **pypdf** - PDF processing library
  - Reads and extracts text from PDF files
  - Backup option if documentation is in PDF format

### LLM Utilities

- **tiktoken** - OpenAI's tokenizer library
  - Counts tokens in text for OpenAI models
  - Helps manage context window limits
  - Optimizes chunk sizes

- **openai** - Official OpenAI Python client
  - Installed automatically as dependency of langchain-openai
  - Direct access to OpenAI API

### Data Validation & Configuration

- **pydantic** - Data validation using Python type annotations
  - Validates configuration and data structures
  - Type checking and parsing
  - Settings management

- **pydantic-settings** - Settings management for Pydantic
  - Installed automatically as dependency
  - Loads settings from environment variables

- **python-dotenv** - Environment variable management
  - Loads environment variables from .env file
  - Manages API keys and secrets securely

- **pyyaml** - YAML parser and emitter
  - Validates generated YAML configurations
  - Parses YAML examples from documentation

## Supporting Dependencies

### HTTP & Networking
- **httpx** - Modern HTTP client (async support)
- **httpcore** - Low-level HTTP transport
- **urllib3** - HTTP client library
- **certifi** - SSL certificates
- **charset-normalizer** - Character encoding detection
- **idna** - Internationalized domain names support

### Data Processing
- **numpy** - Numerical computing library
- **SQLAlchemy** - SQL toolkit and ORM
- **dataclasses-json** - JSON serialization for dataclasses
- **marshmallow** - Object serialization/deserialization

### Async & Concurrency
- **aiohttp** - Async HTTP client/server
- **anyio** - Async abstraction layer
- **uvloop** - Fast asyncio event loop
- **aiohappyeyeballs** - Happy Eyeballs for asyncio

### Vector Store & Embeddings
- **onnxruntime** - ONNX runtime for ML models
- **tokenizers** - Fast tokenizers from HuggingFace
- **huggingface-hub** - HuggingFace model hub client

### Monitoring & Telemetry
- **opentelemetry-api** - OpenTelemetry API
- **opentelemetry-sdk** - OpenTelemetry SDK
- **opentelemetry-exporter-otlp-proto-grpc** - OTLP exporter
- **posthog** - Product analytics

### Cloud & Infrastructure
- **kubernetes** - Kubernetes Python client
- **grpcio** - gRPC framework
- **bcrypt** - Password hashing

### Web Server (for Chroma)
- **uvicorn** - ASGI server
- **httptools** - HTTP parser
- **watchfiles** - File watching
- **websockets** - WebSocket implementation

### Utilities
- **langsmith** - LangChain debugging and monitoring
- **tenacity** - Retry library
- **jsonpatch** - JSON patch implementation
- **packaging** - Package version handling
- **regex** - Regular expressions
- **rich** - Terminal formatting and pretty printing
- **click** - CLI creation toolkit
- **tqdm** - Progress bars
- **backoff** - Exponential backoff decorators

## Development Dependencies (Recommended)

While not currently in requirements.txt, these are recommended for development:

```bash
# Testing
pytest
pytest-asyncio
pytest-cov

# Code Quality
black  # Code formatter
flake8  # Linter
mypy  # Type checker
isort  # Import sorter

# Development Tools
ipython  # Enhanced Python shell
jupyter  # Notebooks for experimentation
```

## Installation

All dependencies are listed in `requirements.txt` and can be installed using:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables Required

The following environment variables need to be set in a `.env` file:

```bash
# Slack
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Optional: Other LLM providers
# ANTHROPIC_API_KEY=your-anthropic-key
# GOOGLE_API_KEY=your-google-key
```

## Version Compatibility

- **Python**: 3.9+
- **Operating System**: macOS, Linux, Windows
- All package versions are managed by pip and locked in the virtual environment
