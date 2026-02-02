"""
MCP Client for ngrok-mcp server.
Connects to the ngrok-mcp server via stdio and provides methods to interact with ngrok documentation.
"""

import asyncio
import json
import os
from contextlib import asynccontextmanager
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
        Search ngrok documentation using the search_ngrok_docs tool.
        Returns parsed list of results with title, link, and content.
        """
        raw = await self.call_tool("search_ngrok_docs", {"query": query})
        return self._parse_search_results(raw, max_results)
    
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
    
    def _expand_query(self, query: str) -> str:
        """Expand query with ngrok-specific terminology."""
        expansions = {
            # Security & WAF
            "waf": "OWASP CRS owasp-crs-request owasp-crs-response security Traffic Policy",
            "firewall": "OWASP CRS restrict-ips deny security Traffic Policy",
            "security": "restrict-ips oauth jwt-validation OWASP Traffic Policy",
            
            # Authentication & Authorization
            "authentication": "oauth oidc jwt-validation basic-auth Traffic Policy action",
            "auth": "oauth oidc jwt-validation basic-auth Traffic Policy action",
            "oauth": "oauth Traffic Policy action provider Google GitHub Microsoft",
            "jwt": "jwt-validation Traffic Policy action issuer audience",
            "sso": "oauth oidc saml Traffic Policy identity provider",
            "login": "oauth oidc basic-auth Traffic Policy authentication",
            
            # Rate Limiting & Traffic Control
            "rate limit": "rate-limit Traffic Policy action capacity bucket",
            "throttle": "rate-limit Traffic Policy action",
            "circuit breaker": "circuit-breaker Traffic Policy action",
            
            # IP & Access Control
            "ip restriction": "restrict-ips Traffic Policy action allow deny CIDR",
            "ip policy": "restrict-ips ip_policies Traffic Policy",
            "block": "deny restrict-ips Traffic Policy action",
            "allowlist": "restrict-ips allow Traffic Policy",
            "whitelist": "restrict-ips allow Traffic Policy",
            "blacklist": "restrict-ips deny Traffic Policy",
            
            # URL & Request Manipulation
            "redirect": "redirect Traffic Policy action url status_code",
            "rewrite": "url-rewrite Traffic Policy action from to",
            "header": "add-headers remove-headers Traffic Policy action",
            "cors": "add-headers Traffic Policy Access-Control-Allow-Origin",
            "custom response": "custom-response Traffic Policy action body status_code",
            
            # Endpoints & Configuration
            "internal endpoint": "AgentEndpoint bindings internal upstream version 3 ngrok.yml",
            "cloud endpoint": "CloudEndpoint Traffic Policy forward-internal",
            "agent endpoint": "AgentEndpoint upstream bindings version 3 ngrok.yml",
            "agent config": "ngrok.yml version 3 endpoints upstream bindings traffic_policy",
            "config file": "ngrok.yml version 3 endpoints configuration",
            
            # Protocols
            "tcp": "TCP endpoint AgentEndpoint upstream proto tcp",
            "https": "HTTPS endpoint TLS upstream url",
            "tls": "TLS agent-tls-termination certificates mutual",
            "tls termination": "agent-tls-termination mutual TLS mTLS certificates",
            "mtls": "agent-tls-termination mutual TLS client certificates",
            "terminate tls": "agent-tls-termination agent TLS termination",
            "websocket": "WebSocket HTTP endpoint upstream",
            
            # Routing & Load Balancing
            "routing": "forward-internal Traffic Policy url expressions",
            "forward": "forward-internal Traffic Policy action url",
            "load balance": "endpoint-pooling weighted failover upstream",
            "failover": "endpoint-pooling Traffic Policy backup",
            
            # Logging & Observability
            "logging": "log Traffic Policy action metadata event",
            "log": "log Traffic Policy action event destination",
            "webhook verification": "verify-webhook Traffic Policy action provider",
            
            # Kubernetes
            "kubernetes": "Kubernetes Operator NgrokTrafficPolicy Ingress Gateway CRD",
            "k8s": "Kubernetes Operator NgrokTrafficPolicy Ingress CRD",
            "ingress": "Kubernetes Ingress NgrokTrafficPolicy annotation",
            
            # Variables & Expressions  
            "variable": "conn req res Traffic Policy expressions CEL",
            "expression": "CEL expressions Traffic Policy conn.client_ip req.headers",
            "cel": "CEL expressions Traffic Policy macros variables",
            
            # Common Use Cases
            "webhook": "verify-webhook Traffic Policy action provider signature",
            "api gateway": "Traffic Policy rate-limit jwt-validation forward-internal",
            "tunnel": "agent endpoint upstream ngrok http ngrok tcp",
            "domain": "reserved domain custom hostname url",
            "subdomain": "domain wildcard url endpoint",
            
            # Endpoint Types
            "cloud endpoint": "CloudEndpoint Traffic Policy forward-internal always-on API Dashboard",
            "agent endpoint": "AgentEndpoint upstream bindings ngrok.yml version 3",
            "public endpoint": "bindings public endpoint url",
            "internal": "bindings internal .internal forward-internal",
            
            # Configuration
            "ngrok.yml": "version 3 agent endpoints upstream bindings traffic_policy",
            "config": "ngrok.yml version 3 endpoints configuration agent",
            "authtoken": "agent authtoken ngrok.yml configuration",
            
            # Traffic Policy Details
            "forward": "forward-internal Traffic Policy action url CloudEndpoint",
            "custom response": "custom-response Traffic Policy action body status_code headers",
            "deny": "deny Traffic Policy action status_code",
            "phases": "on_http_request on_http_response on_tcp_connect Traffic Policy",
            
            # Upstream
            "upstream": "upstream url protocol proxy_protocol http1 http2",
            "proxy protocol": "upstream proxy_protocol PROXY protocol",
            "http2": "upstream protocol http2",
        }
        
        query_lower = query.lower()
        for term, expansion in expansions.items():
            if term in query_lower:
                return f"{query} {expansion}"
        
        return query

    async def ask(self, question: str, max_results: int = 8) -> str:
        """
        Ask a question and get a synthesized answer from the documentation.
        Uses LLM to generate a concise response from search results.
        """
        # Expand query with ngrok-specific terminology
        expanded_query = self._expand_query(question)
        results = await self.search_docs(expanded_query, max_results=max_results)
        
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
        
        system_prompt = """Friendly ngrok docs expert. Be concise but warm.

RULES:
- Start with brief friendly opener ("Sure!", "Absolutely!", "No problem!")
- 1-2 sentence explanation, then show code ONLY from provided context
- NEVER invent config fields - only use what's in context
- End with source URL

AGENT CONFIG v3 (ngrok.yml):
```
version: 3
agent:
  authtoken: <token>
endpoints:
  - name: example
    url: https://example.ngrok.app  # or tls:// for TLS endpoints
    upstream:
      url: 8080
    bindings: ["public"]  # strings: "public", "internal", or "kubernetes"
    traffic_policy:
      on_http_request: [...]
    agent_tls_termination:  # ONLY for tls:// URLs, terminates TLS at agent
      server_certificate: <path or PEM>
      server_private_key: <path or PEM>
      mutual_tls_certificate_authorities: [<CA certs>]  # for mTLS
```

TLS TERMINATION - TWO DIFFERENT APPROACHES:
1. AT THE AGENT (for tls:// endpoints): Use `agent_tls_termination` in ngrok.yml
   - Docs: https://ngrok.com/docs/agent/agent-tls-termination
2. AT THE CLOUD (Traffic Policy): Use `terminate-tls` action in on_tcp_connect phase
   - For Cloud Endpoints or to customize TLS settings
   - Docs: https://ngrok.com/docs/traffic-policy/actions/terminate-tls

CLOUD ENDPOINTS vs AGENT ENDPOINTS:
- Cloud Endpoints: Always-on, managed via API/Dashboard, MUST have Traffic Policy ending with terminating action (forward-internal, deny, redirect, custom-response)
- Agent Endpoints: Created by agent, tied to agent lifetime, implicitly forward to upstream

TRAFFIC POLICY PHASES:
- on_http_request / on_http_response: For HTTP traffic
- on_tcp_connect: For TCP/TLS traffic (where terminate-tls goes)

If context lacks answer: "Hmm, I don't have docs for that. Check https://ngrok.com/docs"."""

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


@asynccontextmanager
async def get_mcp_client():
    """
    Context manager for getting an MCP client connection.
    
    Usage:
        async with get_mcp_client() as client:
            result = await client.search_docs("tunnels")
    """
    client = await NgrokMCPClient.connect()
    try:
        yield client
    finally:
        pass  # Keep connection alive for reuse
