"""
Ngrok Assistant - High-level wrapper for MCP client.

Provides a simple interface for handlers to search and retrieve ngrok documentation.
"""

import asyncio
import threading
from dataclasses import dataclass
from typing import Any, Coroutine

from .client import NgrokMCPClient


# Background event loop for MCP operations
_loop: asyncio.AbstractEventLoop | None = None
_thread: threading.Thread | None = None
_lock = threading.Lock()


def _get_event_loop() -> asyncio.AbstractEventLoop:
    """Get or create a background event loop for MCP operations."""
    global _loop, _thread
    
    with _lock:
        if _loop is None or not _loop.is_running():
            _loop = asyncio.new_event_loop()
            _thread = threading.Thread(target=_loop.run_forever, daemon=True)
            _thread.start()
    
    return _loop


def run_in_background(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run a coroutine in the background event loop and wait for result."""
    loop = _get_event_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=60)


def shutdown_background_loop():
    """Shutdown the background event loop."""
    global _loop, _thread
    
    with _lock:
        if _loop is not None and _loop.is_running():
            _loop.call_soon_threadsafe(_loop.stop)
            if _thread is not None:
                _thread.join(timeout=2)
            _loop = None
            _thread = None


@dataclass
class DocResult:
    """A documentation search result."""
    title: str
    content: str
    link: str = ""
    code_example: str = ""
    source: str = "ngrok-mcp"
    
    @classmethod
    def from_dict(cls, data: dict) -> "DocResult":
        """Create DocResult from parsed dict."""
        return cls(
            title=data.get("title", "ngrok Documentation"),
            content=data.get("content", ""),
            link=data.get("link", ""),
            code_example=data.get("code_example", ""),
        )


class NgrokAssistant:
    """
    High-level assistant for ngrok documentation queries.
    
    Wraps the MCP client with a simpler interface for common operations.
    """
    
    _client: NgrokMCPClient | None = None
    
    @classmethod
    async def initialize(cls) -> "NgrokAssistant":
        """Initialize the assistant and connect to MCP server."""
        assistant = cls()
        assistant._client = await NgrokMCPClient.connect()
        return assistant
    
    @classmethod
    async def shutdown(cls) -> None:
        """Shutdown the assistant and disconnect from MCP server."""
        await NgrokMCPClient.disconnect()
    
    @property
    def client(self) -> NgrokMCPClient:
        """Get the MCP client."""
        if self._client is None:
            raise RuntimeError("Assistant not initialized. Call initialize() first.")
        return self._client
    
    async def search_docs(self, query: str, max_results: int = 3) -> list[DocResult]:
        """
        Search ngrok documentation for the given query.
        
        Returns a list of DocResult objects with the search results.
        """
        try:
            results = await self.client.search_docs(query, max_results=max_results)
            return [DocResult.from_dict(r) for r in results]
        except Exception as e:
            return [DocResult(title="Error", content=f"Error searching documentation: {e}")]
    
    async def get_doc(self, path: str) -> DocResult:
        """
        Fetch a specific document by path.
        
        Args:
            path: The document path (e.g., "docs/http" or "api/endpoints")
        
        Returns:
            DocResult with the document content.
        """
        try:
            result = await self.client.get_doc(path)
            return DocResult(title=path, content=str(result), source=path)
        except Exception as e:
            return DocResult(title="Error", content=f"Error fetching document: {e}", source=path)
    
    async def list_docs(self) -> list[str]:
        """List available documentation topics from the catalog."""
        try:
            result = await self.client.list_docs()
            if isinstance(result, str):
                return result.split('\n')
            return [str(result)]
        except Exception as e:
            return [f"Error listing docs: {e}"]


_assistant: NgrokAssistant | None = None


def get_assistant() -> NgrokAssistant:
    """Get or create the global assistant instance (sync wrapper)."""
    global _assistant
    if _assistant is None:
        _assistant = run_in_background(NgrokAssistant.initialize())
    return _assistant


def ask_ngrok(query: str, thread_context: str = "") -> str:
    """Sync wrapper to ask a question and get a synthesized answer."""
    try:
        return run_in_background(_ask_ngrok_async(query, thread_context))
    except Exception as e:
        return f"Error: {e}"


async def _ask_ngrok_async(query: str, thread_context: str = "") -> str:
    """Async implementation of ask_ngrok."""
    client = await NgrokMCPClient.connect()
    return await client.ask(query, thread_context=thread_context)


def generate_ngrok_yaml(request: str) -> str:
    """Sync wrapper to generate a custom ngrok YAML configuration."""
    try:
        return run_in_background(_generate_yaml_async(request))
    except Exception as e:
        return f"Error: {e}"


async def _generate_yaml_async(request: str) -> str:
    """Async implementation of generate_ngrok_yaml."""
    client = await NgrokMCPClient.connect()
    return await client.generate_yaml(request)
