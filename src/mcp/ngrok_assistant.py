"""
Ngrok Assistant - High-level wrapper for MCP client.

Provides a simple interface for handlers to search and retrieve ngrok documentation.

Each MCP request runs in its own thread with its own event loop via
``asyncio.run()``.  This guarantees that the ``anyio`` cancel-scopes
inside ``streamablehttp_client`` are entered and exited within the same
task, avoiding the cross-task RuntimeError that occurs when multiple
requests share a single event loop.
"""

import asyncio
import concurrent.futures
import threading
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from .client import NgrokMCPClient


# Thread pool for running MCP requests.  Each request gets its own thread
# and its own ``asyncio.run()`` event loop, so anyio cancel-scopes never
# cross task boundaries.
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)


def _run_in_own_loop(coro_factory: Callable[[], Coroutine[Any, Any, Any]]) -> Any:
    """Run a coroutine factory in a fresh event loop (called inside a pool thread)."""
    return asyncio.run(coro_factory())


def run_in_background(coro_factory: Callable[[], Coroutine[Any, Any, Any]]) -> Any:
    """Submit work to the thread pool and block for the result.

    Each call gets its own thread + event loop, so ``anyio`` scopes are
    fully isolated between concurrent requests.
    """
    future = _executor.submit(_run_in_own_loop, coro_factory)
    return future.result(timeout=120)


def shutdown_background_loop():
    """Shutdown the thread pool."""
    _executor.shutdown(wait=False)


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
        _assistant = run_in_background(lambda: NgrokAssistant.initialize())
    return _assistant


def get_ngrok_intent(query: str, thread_context: str = "") -> str:
    """Get the intent classification without making an MCP call."""
    client = NgrokMCPClient()
    return client._detect_intent(query, thread_context)


def ask_ngrok(query: str, thread_context: str = "", model: str = "gpt-4o-mini") -> str:
    """Sync wrapper to ask a question and get a synthesized answer."""
    try:
        return run_in_background(
            lambda: _ask_ngrok_async(query, thread_context, model)
        )
    except Exception as e:
        return f"Error: {e}"


async def _ask_ngrok_async(query: str, thread_context: str = "", model: str = "gpt-4o-mini") -> str:
    """Async implementation of ask_ngrok.

    Uses a per-request connection within the single worker task so the
    transport's anyio cancel-scope is never crossed between tasks.
    Conversational queries (no MCP docs needed) skip the connection.
    """
    client = NgrokMCPClient()
    intent = client._detect_intent(query, thread_context)
    if intent == "conversational":
        return await client.ask(query, thread_context=thread_context, model=model)
    async with NgrokMCPClient() as client:
        return await client.ask(query, thread_context=thread_context, model=model)


def generate_ngrok_yaml(request: str, model: str = "gpt-4o") -> str:
    """Sync wrapper to generate a custom ngrok YAML configuration."""
    try:
        return run_in_background(
            lambda: _generate_yaml_async(request, model)
        )
    except Exception as e:
        return f"Error: {e}"


async def _generate_yaml_async(request: str, model: str = "gpt-4o") -> str:
    """Async implementation of generate_ngrok_yaml."""
    async with NgrokMCPClient() as client:
        return await client.generate_yaml(request, model=model)
