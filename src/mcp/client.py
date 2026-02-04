"""
MCP Client for ngrok-mcp server.
Connects to the ngrok-mcp server via stdio and provides methods to interact with ngrok documentation.
"""

import json
import os
from typing import Any

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class NgrokMCPClient:
    """
    MCP client that connects to the ngrok-mcp server.
    
    Provides async methods to search, list, and retrieve ngrok documentation.
    """
    
    _instance: "NgrokMCPClient | None" = None
    _session: ClientSession | None = None
    _session_context: ClientSession | None = None
    _stdio_context = None
    _read = None
    _write = None
    _connected: bool = False
    
    def __new__(cls) -> "NgrokMCPClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_server_params(cls) -> StdioServerParameters:
        """Get the stdio server parameters for ngrok-mcp."""
        env = os.environ.copy()
        if "NGROK_API_KEY" in os.environ:
            env["NGROK_API_KEY"] = os.environ["NGROK_API_KEY"]
        
        # Use local ngrok-mcp installation
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        mcp_path = os.path.join(project_root, "ngrok-mcp", "dist", "index.js")
        
        return StdioServerParameters(
            command="node",
            args=[mcp_path],
            env=env,
        )
    
    @classmethod
    async def connect(cls) -> "NgrokMCPClient":
        """Connect to the ngrok-mcp server and return the client instance."""
        instance = cls()
        if instance._connected:
            return instance
        
        server_params = cls.get_server_params()
        
        instance._stdio_context = stdio_client(server_params)
        instance._read, instance._write = await instance._stdio_context.__aenter__()
        
        instance._session_context = ClientSession(instance._read, instance._write)
        instance._session = await instance._session_context.__aenter__()
        
        await instance._session.initialize()
        instance._connected = True
        
        return instance
    
    @classmethod
    async def disconnect(cls) -> None:
        """Disconnect from the ngrok-mcp server."""
        instance = cls._instance
        if instance is None or not instance._connected:
            return
        
        if instance._session_context:
            await instance._session_context.__aexit__(None, None, None)
        if instance._stdio_context:
            await instance._stdio_context.__aexit__(None, None, None)
        
        instance._session = None
        instance._connected = False
    
    @property
    def session(self) -> ClientSession:
        """Get the active MCP session."""
        if self._session is None:
            raise RuntimeError("MCP client not connected. Call connect() first.")
        return self._session
    
    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Call an MCP tool and return the result."""
        result = await self.session.call_tool(name, arguments=arguments or {})
        
        if result.content:
            content = result.content[0]
            if isinstance(content, types.TextContent):
                return content.text
            elif isinstance(content, types.EmbeddedResource):
                if isinstance(content.resource, types.TextResourceContents):
                    return content.resource.text
        
        return result.structured_content or str(result.content)
    
    async def list_tools(self) -> list[str]:
        """List available tools from the ngrok-mcp server."""
        result = await self.session.list_tools()
        return [tool.name for tool in result.tools]
    
    async def search_docs(self, query: str, max_results: int = 3) -> list[dict]:
        """
        Search ngrok documentation using index_docs + get_doc for precise retrieval.
        Falls back to search_ngrok_docs if no indexed results found.
        """
        results = []
        
        # First, search the doc index for relevant docs
        indexed_docs = await self._search_index(query, max_results=max_results)
        
        if indexed_docs:
            # Fetch full content for the top docs
            for doc in indexed_docs[:max_results]:
                try:
                    content = await self._get_doc_content(doc.get("mdUrl") or doc.get("url"))
                    if content:
                        results.append({
                            "title": doc.get("title", "ngrok Documentation"),
                            "link": doc.get("mdUrl") or doc.get("url", ""),
                            "content": content[:2000],  # More content since we're fetching directly
                            "tags": doc.get("tags", [])
                        })
                except Exception:
                    continue
        
        # Fall back to search_ngrok_docs if no indexed results
        if not results:
            raw = await self.call_tool("search_ngrok_docs", {"query": query})
            results = self._parse_search_results(raw, max_results)
        
        return results
    
    async def _search_index(self, query: str, max_results: int = 5) -> list[dict]:
        """Search the doc index for relevant documents."""
        try:
            # Determine relevant tags based on query
            tags = self._infer_tags(query)
            
            raw = await self.call_tool("index_docs", {
                "query": query,
                "tags": tags if tags else None,
                "limit": max_results
            })
            
            data = json.loads(raw) if isinstance(raw, str) else raw
            return data.get("docs", [])
        except Exception:
            return []
    
    async def _get_doc_content(self, url: str) -> str | None:
        """Fetch full content of a specific doc."""
        if not url:
            return None
        try:
            raw = await self.call_tool("get_doc", {"url": url, "max_length": 4000})
            data = json.loads(raw) if isinstance(raw, str) else raw
            return data.get("content", "")
        except Exception:
            return None
    
    def _infer_tags(self, query: str) -> list[str]:
        """Infer relevant doc tags from the query."""
        query_lower = query.lower()
        tags = []
        
        tag_keywords = {
            "traffic-policy": ["traffic policy", "policy", "rule", "action", "phase"],
            "actions": ["rewrite", "redirect", "rate limit", "restrict", "forward", "deny", "header", "jwt", "oauth"],
            "endpoints": ["endpoint", "cloud endpoint", "agent endpoint"],
            "cel": ["expression", "variable", "cel", "macro", "conn.", "req."],
            "auth": ["oauth", "oidc", "saml", "jwt", "authentication", "sso"],
            "tls": ["tls", "https", "certificate", "mtls", "ssl"],
            "agent": ["agent", "ngrok.yml", "upstream", "local", "tunnel"],
        }
        
        for tag, keywords in tag_keywords.items():
            if any(kw in query_lower for kw in keywords):
                tags.append(tag)
        
        return tags[:3]  # Limit to top 3 tags
    
    def _parse_search_results(self, raw: str, max_results: int = 3) -> list[dict]:
        """Parse raw MCP search results into structured format."""
        results = []
        
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            
            if isinstance(data, dict) and "content" in data:
                for item in data["content"][:max_results]:
                    if item.get("type") == "text":
                        text = item.get("text", "")
                        result = self._parse_doc_text(text)
                        if result:
                            results.append(result)
            elif isinstance(data, list):
                for item in data[:max_results]:
                    if isinstance(item, dict):
                        results.append(item)
                    elif isinstance(item, str):
                        result = self._parse_doc_text(item)
                        if result:
                            results.append(result)
        except (json.JSONDecodeError, TypeError):
            # If not JSON, treat as plain text
            result = self._parse_doc_text(str(raw))
            if result:
                results.append(result)
        
        return results
    
    def _parse_doc_text(self, text: str) -> dict | None:
        """Parse a single doc text block into structured format."""
        if not text.strip():
            return None
        
        lines = text.strip().split('\n')
        title = ""
        link = ""
        content_lines = []
        
        for line in lines:
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
            elif line.startswith("Link:"):
                link = line.replace("Link:", "").strip()
            elif line.startswith("Content:"):
                content_lines.append(line.replace("Content:", "").strip())
            else:
                content_lines.append(line)
        
        content = '\n'.join(content_lines).strip()
        
        # Extract code examples if present
        code_example = ""
        if "on_http_request:" in content or "on_tcp_connect:" in content:
            # Find YAML block
            import re
            yaml_match = re.search(r'(on_(?:http_request|tcp_connect):.*?)(?:\n\n|\Z)', content, re.DOTALL)
            if yaml_match:
                code_example = yaml_match.group(1).strip()
        
        return {
            "title": title or "ngrok Documentation",
            "link": link,
            "content": content[:500] if len(content) > 500 else content,
            "code_example": code_example
        }
    
    async def ask(self, question: str, max_results: int = 8) -> str:
        """
        Ask a question and get a synthesized answer from the documentation.
        Uses LLM to generate a concise response from search results.
        """
        results = await self.search_docs(question, max_results=max_results)
        
        if not results:
            return "I couldn't find relevant documentation for your question."
        
        # Build context from results
        context_parts = []
        for i, r in enumerate(results, 1):
            part = f"[{i}] {r.get('title', 'Doc')}\n"
            if r.get('link'):
                part += f"URL: {r['link']}\n"
            part += r.get('content', '')
            if r.get('code_example'):
                part += f"\n\nExample:\n```yaml\n{r['code_example']}\n```"
            context_parts.append(part)
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Synthesize with LLM if available
        if HAS_OPENAI and os.environ.get("OPENAI_API_KEY"):
            return await self._synthesize_answer(question, context, results)
        else:
            # Fallback: return best result with code example
            best = results[0]
            answer = f"**{best.get('title', 'Answer')}**\n\n"
            answer += best.get('content', '')[:500]
            if best.get('code_example'):
                answer += f"\n\n```yaml\n{best['code_example']}\n```"
            if best.get('link'):
                answer += f"\n\n🔗 {best['link']}"
            return answer
    
    async def _synthesize_answer(self, question: str, context: str, results: list[dict]) -> str:
        """Use OpenAI to synthesize a concise answer from search results."""
        client = AsyncOpenAI()
        
        system_prompt = """ngrok docs expert. Answer based ONLY on the provided documentation context.

RULES:
- Brief answer (1-2 sentences), then code examples from context
- ONLY use information from the provided documentation
- For agent configs: ALWAYS use version: 3 format (never version: 2 or "tunnels:")
- Include source URL when available
- If context lacks answer: "I don't have docs for that. Check https://ngrok.com/docs"
"""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {question}\n\nDocumentation Context:\n{context}"}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content

    async def generate_yaml(self, request: str) -> str:
        """
        Generate a custom ngrok YAML configuration based on user requirements.
        Uses LLM with doc context from MCP to craft configs.
        """
        if not HAS_OPENAI or not os.environ.get("OPENAI_API_KEY"):
            return "Error: OpenAI API key required for YAML generation."
        
        # Pre-warm relevant doc packs
        try:
            await self.call_tool("warm_docs", {"pack": "traffic_policy", "limit": 5})
            if any(kw in request.lower() for kw in ["endpoint", "internal", "load balance", "upstream"]):
                await self.call_tool("warm_docs", {"pack": "endpoint_create", "limit": 5})
        except Exception:
            pass  # Non-critical, continue without warming
        
        # Search docs for relevant context - fetch more for better coverage
        results = await self.search_docs(request, max_results=8)
        
        context_parts = []
        for r in results:
            if r.get('content'):
                context_parts.append(f"# {r.get('title', 'Doc')}\n{r.get('content', '')}")
        
        doc_context = "\n\n".join(context_parts) if context_parts else ""
        
        client = AsyncOpenAI()
        
        system_prompt = """ngrok config expert.

OUTPUT: One sentence, then YAML only.

VALID AGENT CONFIG FIELDS (use ONLY these):
```yaml
version: 3
endpoints:
  - name: <string>
    url: <https://domain.ngrok.app or tcp:// or tls://>
    upstream:
      url: <port or address>
    bindings:
      - public    # or internal
    traffic_policy:
      on_http_request:
        - expressions: [...]
          actions: [...]
```

FORBIDDEN (never use these):
- version: "3" → use version: 3
- type: http → INVALID FIELD
- internal: true → use bindings: ["internal"]
- tunnels: → v2 deprecated

If unsure, say "I don't have documentation for that" instead of guessing."""

        user_prompt = f"Generate an ngrok YAML configuration for: {request}"
        if doc_context:
            user_prompt += f"\n\nRelevant documentation:\n{doc_context}"
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        
        return response.choices[0].message.content

    async def get_doc(self, path: str) -> str:
        """Fetch a specific document from ngrok documentation."""
        return await self.call_tool("get_doc", {"path": path})
    
    async def list_docs(self) -> str:
        """List available docs from the catalog using index_docs tool."""
        return await self.call_tool("index_docs", {})
    
    async def warm_docs(self, pack: str) -> str:
        """Pre-fetch docs for a workflow pack."""
        return await self.call_tool("warm_docs", {"pack": pack})
    
    async def docs_cache_status(self) -> str:
        """Show the documentation cache state."""
        return await self.call_tool("docs_cache_status", {})



