"""
MCP Client for ngrok documentation.
Connects to ngrok's official MCP server at https://ngrok.com/docs/mcp via HTTP.
"""

import json
import os
import re
from typing import Any

import httpx

from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client

try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

NGROK_MCP_URL = "https://ngrok.com/docs/mcp"


class NgrokMCPClient:
    """
    MCP client that connects to ngrok's official documentation MCP server.
    """

    _instance: "NgrokMCPClient | None" = None
    _session: ClientSession | None = None
    _session_context = None
    _transport_context = None
    _connected: bool = False

    def __new__(cls) -> "NgrokMCPClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def connect(cls) -> "NgrokMCPClient":
        """Connect to the ngrok MCP server and return the client instance."""
        instance = cls()
        if instance._connected:
            return instance

        instance._transport_context = streamablehttp_client(NGROK_MCP_URL)
        read, write, _ = await instance._transport_context.__aenter__()

        instance._session_context = ClientSession(read, write)
        instance._session = await instance._session_context.__aenter__()

        await instance._session.initialize()
        instance._connected = True

        return instance

    @classmethod
    async def disconnect(cls) -> None:
        """Disconnect from the ngrok MCP server."""
        instance = cls._instance
        if instance is None or not instance._connected:
            return

        if instance._session_context:
            await instance._session_context.__aexit__(None, None, None)
        if instance._transport_context:
            await instance._transport_context.__aexit__(None, None, None)

        instance._session = None
        instance._connected = False

    @property
    def session(self) -> ClientSession:
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
        result = await self.session.list_tools()
        return [tool.name for tool in result.tools]

    # ── Search ────────────────────────────────────────────────────────────

    FILLER_WORDS = {"how", "do", "i", "can", "what", "is", "the", "a", "an", "to",
                    "my", "me", "with", "in", "on", "for", "of", "it", "does",
                    "should", "would", "could", "please", "show", "tell",
                    "about", "using", "use", "set", "up", "get", "make",
                    "protect", "secure", "configure", "setup", "create",
                    "add", "enable", "implement", "apply", "want", "need",
                    "endpoint", "endpoints", "tunnel", "tunnels",
                    "service", "services", "server", "application", "app",
                    "api", "request", "requests", "response", "connection"}

    def _extract_keywords(self, query: str) -> str:
        """Extract core topic keywords from a natural language question."""
        words = re.findall(r'[a-z0-9]+', query.lower())
        keywords = [w for w in words if w not in self.FILLER_WORDS and len(w) > 1]
        return " ".join(keywords)

    async def search_docs(self, query: str, max_results: int = 3) -> list[dict]:
        """Search ngrok docs with multi-query, k8s filtering, and page enrichment."""
        query_lower = query.lower()
        wants_k8s = any(kw in query_lower for kw in ["kubernetes", "k8s", "ingress", "operator", "crd", "helm"])

        search_queries = self._build_search_queries(query)
        results = await self._run_search_queries(search_queries, max_results)

        if not wants_k8s:
            non_k8s = [r for r in results if not self._is_k8s_doc(r)]
            if non_k8s:
                results = non_k8s
            else:
                keywords = self._extract_keywords(query)
                keyword_list = keywords.split()
                retry_queries = [f"{keywords} action"]
                if len(keyword_list) > 1:
                    for word in keyword_list:
                        retry_queries.append(f"{word} action")
                retry_queries.append(keywords)
                retry_results = await self._run_search_queries(retry_queries, max_results)
                retry_non_k8s = [r for r in retry_results if not self._is_k8s_doc(r)]
                if retry_non_k8s:
                    results = retry_non_k8s

        results.sort(key=lambda r: self._score_result(r, query), reverse=True)
        results = results[:max_results]
        results = await self._enrich_results(results)
        return results

    async def _run_search_queries(self, queries: list[str], max_results: int) -> list[dict]:
        """Run a list of search queries and return deduplicated results."""
        seen_links: set[str] = set()
        results = []
        for q in queries:
            try:
                raw = await self.call_tool("SearchNgrokDocumentation", {"query": q})
                for r in self._parse_search_results(raw, max_results):
                    link = r.get("link", "")
                    if link not in seen_links:
                        seen_links.add(link)
                        results.append(r)
            except Exception:
                continue
            if len(results) >= max_results * 2:
                break
        return results

    def _build_search_queries(self, query: str) -> list[str]:
        keywords = self._extract_keywords(query)
        queries = [keywords]
        if keywords != query:
            queries.append(query)
        return queries

    def _is_k8s_doc(self, result: dict) -> bool:
        title = result.get("title", "").lower()
        link = result.get("link", "").lower()
        k8s_indicators = ["kubernetes", "k8s", "/k8s/", "operator", "ingress", "helm", "crd"]
        return any(kw in title or kw in link for kw in k8s_indicators)

    def _score_result(self, result: dict, query: str) -> float:
        """Score a result's relevance to the query based on keyword overlap."""
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) >= 3]

        title = result.get("title", "").lower()
        link = result.get("link", "").lower()
        content = result.get("content", "").lower()

        score = 0.0

        for word in query_words:
            if word in title:
                score += 3.0
            if word in link:
                score += 2.0
            if word in content:
                score += 1.0

        if query_lower in title:
            score += 10.0
        elif query_lower in content:
            score += 5.0

        title_words = set(re.findall(r'[a-z0-9]+', title))
        link_words = set(re.findall(r'[a-z0-9]+', link))
        doc_specific_words = (title_words | link_words) - {"ngrok", "docs", "http", "https", "com", "the", "and", "for", "with", "how"}
        query_word_set = set(query_words)
        for doc_word in doc_specific_words:
            if len(doc_word) >= 4 and doc_word not in query_word_set and not any(doc_word in qw or qw in doc_word for qw in query_word_set):
                score -= 1.5

        if query_words:
            matched = sum(1 for w in query_words if w in title or w in link)
            score += (matched / len(query_words)) * 5.0

        return score

    # ── Page enrichment ───────────────────────────────────────────────────

    async def _fetch_doc_page(self, url: str) -> str | None:
        md_url = url.rstrip("/") + ".md"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(md_url, follow_redirects=True)
                if resp.status_code == 200:
                    return resp.text
        except Exception:
            pass
        return None

    def _extract_yaml_blocks(self, markdown: str) -> list[str]:
        return re.findall(r'```ya?ml[^\n]*\n(.*?)```', markdown, re.DOTALL)

    async def _enrich_results(self, results: list[dict]) -> list[dict]:
        for r in results:
            link = r.get("link", "")
            if not link:
                continue
            page = await self._fetch_doc_page(link)
            if not page:
                continue
            yaml_blocks = self._extract_yaml_blocks(page)
            if yaml_blocks:
                r["yaml_examples"] = yaml_blocks
            r["full_content"] = page[:4000]
        return results

    # ── Parse MCP response ────────────────────────────────────────────────

    def _parse_search_results(self, raw: str, max_results: int = 3) -> list[dict]:
        results = []
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(data, dict) and "content" in data:
                for item in data["content"][:max_results]:
                    if item.get("type") == "text":
                        result = self._parse_doc_text(item.get("text", ""))
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
            result = self._parse_doc_text(str(raw))
            if result:
                results.append(result)
        return results

    def _parse_doc_text(self, text: str) -> dict | None:
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
        return {
            "title": title or "ngrok Documentation",
            "link": link,
            "content": content[:500] if len(content) > 500 else content,
        }

    # ── Context building ──────────────────────────────────────────────────

    def _build_doc_context(self, results: list[dict]) -> str:
        context_parts = []
        for i, r in enumerate(results, 1):
            part = f"[{i}] {r.get('title', 'Doc')}\n"
            if r.get('link'):
                part += f"URL: {r['link']}\n"
            content = r.get('full_content') or r.get('content', '')
            part += content
            if r.get('yaml_examples'):
                part += "\n\nYAML examples from this doc:\n"
                for yaml_block in r['yaml_examples']:
                    part += f"\n```yaml\n{yaml_block.strip()}\n```\n"
            context_parts.append(part)
        return "\n\n---\n\n".join(context_parts)

    # ── Query classification ─────────────────────────────────────────────

    def _classify_query(self, query: str) -> str:
        """Classify what context the user is asking about to guide the LLM."""
        q = query.lower()

        if any(kw in q for kw in ["kubernetes", "k8s", "kubectl", "helm", "operator",
                                   "crd", "agentendpoint", "cloudendpoint", "manifest"]):
            return "kubernetes"

        if any(kw in q for kw in ["api", "curl", "rest", "api call", "programmatic"]):
            return "api"

        return "agent"

    def _format_context_instruction(self, category: str) -> str:
        if category == "kubernetes":
            return (
                "The user is asking about Kubernetes / k8s. "
                "Use Kubernetes-specific examples (kind:, apiVersion:, AgentEndpoint, CloudEndpoint CRDs) from the documentation. "
                "Do NOT show ngrok agent config YAML (version: 3, endpoints:) unless the user asks for it."
            )
        if category == "api":
            return (
                "The user is asking about the ngrok API. "
                "Use API examples (curl, REST endpoints) from the documentation. "
                "Do NOT show Kubernetes CRD YAML or ngrok agent config YAML unless the user asks for it."
            )
        return (
            "The user is asking about the ngrok agent / CLI. "
            "Use ngrok agent configuration examples (version: 3, endpoints:, traffic_policy:) from the documentation. "
            "Do NOT show Kubernetes examples (kind:, apiVersion:, AgentEndpoint, CloudEndpoint, metadata:, namespace:) "
            "even if they appear in the documentation context. The user did not ask about Kubernetes."
        )

    # ── Ask ────────────────────────────────────────────────────────────────

    async def ask(self, question: str, max_results: int = 8, thread_context: str = "") -> str:
        results = await self.search_docs(question, max_results=max_results)
        if not results:
            return "I couldn't find relevant documentation for your question."
        context = self._build_doc_context(results)
        category = self._classify_query(question)
        if HAS_OPENAI and os.environ.get("OPENAI_API_KEY"):
            return await self._synthesize_answer(question, context, category, thread_context=thread_context)
        else:
            best = results[0]
            answer = f"**{best.get('title', 'Answer')}**\n\n{best.get('content', '')[:500]}"
            if best.get('link'):
                answer += f"\n\n🔗 {best['link']}"
            return answer

    async def _synthesize_answer(self, question: str, doc_context: str, category: str, thread_context: str = "") -> str:
        client = AsyncOpenAI()

        context_instruction = self._format_context_instruction(category)

        system_prompt = f"""You answer ngrok questions using ONLY the Documentation Context provided.

CONTEXT: {context_instruction}

RULES:
- Be concise: 1-3 sentences of explanation
- Only include a YAML example if one appears VERBATIM in the Documentation Context (in a ```yaml block). Never generate, infer, or fabricate YAML
- If the question is conceptual or informational, just answer it - not every answer needs code
- Do NOT show multiple examples for the same thing
- Never invent fields, commands, or configuration options not in the documentation
- Include the source URL at the end
- Use prior thread conversation (if provided) to understand follow-ups
"""

        user_content = f"Question: {question}\n\nDocumentation Context:\n{doc_context}"
        if thread_context:
            user_content = f"Prior conversation in thread:\n{thread_context}\n\nFollow-up question: {question}\n\nDocumentation Context:\n{doc_context}"

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        return response.choices[0].message.content

    # ── YAML generation ───────────────────────────────────────────────────

    async def generate_yaml(self, request: str) -> str:
        if not HAS_OPENAI or not os.environ.get("OPENAI_API_KEY"):
            return "Error: OpenAI API key required for YAML generation."

        results = await self.search_docs(request, max_results=8)
        doc_context = self._build_doc_context(results)
        category = self._classify_query(request)
        context_instruction = self._format_context_instruction(category)

        client = AsyncOpenAI()

        system_prompt = f"""You generate ngrok YAML configurations by adapting examples from the documentation provided below. Do not use any prior knowledge about ngrok.

CONTEXT: {context_instruction}

RULES:
- Find YAML examples in the documentation that match the correct context (see above) and adapt them to the user's request
- ONLY use fields and syntax that appear in the documentation examples
- If the docs contain no relevant YAML examples for this topic, say "The documentation doesn't include a YAML example for this. Check https://ngrok.com/docs" and summarize what the docs say instead
- Never invent fields - if a field isn't in the doc examples, don't use it"""

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
