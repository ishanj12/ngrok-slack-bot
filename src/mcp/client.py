"""
MCP Client for ngrok documentation.
Connects to ngrok's official MCP server at https://ngrok.com/docs/mcp via HTTP.
"""

import asyncio
import difflib
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

try:
    from anthropic import AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from google import genai
    from google.genai import types as genai_types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

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

    CONNECTION_TIMEOUT = 15

    @classmethod
    async def connect(cls) -> "NgrokMCPClient":
        """Connect to the ngrok MCP server and return the client instance."""
        instance = cls()
        if instance._connected:
            return instance

        try:
            await asyncio.wait_for(cls._do_connect(instance), timeout=cls.CONNECTION_TIMEOUT)
        except asyncio.TimeoutError:
            await cls.disconnect()
            raise ConnectionError(
                "ngrok MCP server is not responding. The documentation service may be temporarily unavailable."
            )
        except Exception:
            await cls.disconnect()
            raise

        return instance

    @classmethod
    async def _do_connect(cls, instance: "NgrokMCPClient") -> None:
        instance._transport_context = streamablehttp_client(NGROK_MCP_URL)
        read, write, _ = await instance._transport_context.__aenter__()

        instance._session_context = ClientSession(read, write)
        instance._session = await instance._session_context.__aenter__()

        await instance._session.initialize()
        instance._connected = True

    @classmethod
    async def reconnect(cls) -> "NgrokMCPClient":
        """Force a fresh connection to the MCP server."""
        await cls.disconnect()
        return await cls.connect()

    @classmethod
    async def disconnect(cls) -> None:
        """Disconnect from the ngrok MCP server."""
        instance = cls._instance
        if instance is None:
            return

        try:
            if instance._session_context:
                await instance._session_context.__aexit__(None, None, None)
        except Exception:
            pass
        try:
            if instance._transport_context:
                await instance._transport_context.__aexit__(None, None, None)
        except Exception:
            pass

        instance._session = None
        instance._session_context = None
        instance._transport_context = None
        instance._connected = False

    @property
    def session(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError("MCP client not connected. Call connect() first.")
        return self._session

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Call an MCP tool and return the result. Auto-reconnects on failure."""
        try:
            return await self._call_tool_inner(name, arguments)
        except Exception:
            await self.__class__.reconnect()
            return await self._call_tool_inner(name, arguments)

    async def _call_tool_inner(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
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
                    "add", "enable", "implement", "apply", "want", "need"}

    def _extract_keywords(self, query: str) -> str:
        """Extract core topic keywords from a natural language question."""
        words = re.findall(r'[a-z0-9]+', query.lower())
        keywords = [w for w in words if w not in self.FILLER_WORDS and len(w) > 1]
        return " ".join(keywords)

    async def _fetch_action_doc(self, slug: str) -> dict | None:
        url = f"https://ngrok.com/docs/traffic-policy/actions/{slug}"
        page = await self._fetch_doc_page(url)
        if not page:
            return None
        yaml_blocks = self._extract_yaml_blocks(page)
        return {
            "title": f"{slug.replace('-', ' ').title()} Action",
            "link": url,
            "content": page[:500],
            "full_content": page[:4000],
            "yaml_examples": yaml_blocks,
        }

    K8S_TOPIC_PAGES = {
        "endpoint": "getting-started/kubernetes/endpoints",
        "endpoints": "getting-started/kubernetes/endpoints",
        "bound endpoint": "universal-gateway/kubernetes-endpoints",
        "kubernetes endpoint": "getting-started/kubernetes/endpoints",
        "agentendpoint": "k8s/crds/agentendpoint",
        "agent endpoint": "k8s/crds/agentendpoint",
        "cloudendpoint": "k8s/crds/cloudendpoint",
        "cloud endpoint": "k8s/crds/cloudendpoint",
        "crd": "k8s/guides/using-crds",
        "crds": "k8s/guides/using-crds",
        "custom resource": "k8s/guides/using-crds",
        "ingress": "getting-started/kubernetes/ingress",
        "gateway api": "getting-started/kubernetes/gateway-api",
        "install": "k8s/installation",
        "helm": "k8s/installation/helm",
        "traffic policy": "k8s/guides/using-crds",
    }

    def _detect_k8s_topic_slugs(self, query: str) -> list[str]:
        q_lower = query.lower()
        slugs: list[str] = []
        seen: set[str] = set()
        for phrase, slug in sorted(self.K8S_TOPIC_PAGES.items(), key=lambda x: -len(x[0])):
            if phrase in q_lower and slug not in seen:
                seen.add(slug)
                slugs.append(slug)
        return slugs

    async def _fetch_k8s_docs(self, query: str) -> list[dict]:
        slugs = self._detect_k8s_topic_slugs(query)
        if not slugs:
            slugs = ["getting-started/kubernetes/endpoints", "k8s/guides/using-crds"]
        docs: list[dict] = []
        for slug in slugs[:3]:
            url = f"https://ngrok.com/docs/{slug}"
            page = await self._fetch_doc_page(url)
            if not page:
                continue
            yaml_blocks = self._extract_yaml_blocks(page)
            title_match = re.search(r'^#\s+(.+)', page, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else slug.split("/")[-1].replace("-", " ").title()
            docs.append({
                "title": title,
                "link": url,
                "content": page[:500],
                "full_content": page[:4000],
                "yaml_examples": yaml_blocks,
            })
        return docs

    async def search_docs(self, query: str, max_results: int = 3) -> list[dict]:
        """Search ngrok docs with multi-query, k8s filtering, and page enrichment."""
        query_lower = query.lower()
        wants_k8s = any(kw in query_lower for kw in ["kubernetes", "k8s", "ingress", "operator", "crd", "helm"])

        action_slug = self._detect_action_slug(query)
        action_doc = None
        if action_slug:
            action_doc = await self._fetch_action_doc(action_slug)

        k8s_docs: list[dict] = []
        if wants_k8s:
            k8s_docs = await self._fetch_k8s_docs(query)

        search_queries = self._build_search_queries(query, wants_k8s=wants_k8s)
        results = await self._run_search_queries(search_queries, max_results)

        if action_doc:
            results = [action_doc] + [r for r in results if r.get("link") != action_doc["link"]]

        if k8s_docs:
            k8s_links = {d["link"] for d in k8s_docs}
            results = k8s_docs + [r for r in results if r.get("link") not in k8s_links]

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

        results.sort(key=lambda r: self._score_result(r, query, wants_k8s=wants_k8s), reverse=True)
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

    TRAFFIC_POLICY_ACTIONS: dict[str, list[str]] = {
        "circuit-breaker": ["circuit breaker", "circuit breaking"],
        "rate-limit": ["rate limit", "rate limiting"],
        "jwt-validation": ["jwt validation", "jwt"],
        "basic-auth": ["basic auth", "basic authentication"],
        "oauth": ["oauth"],
        "openid-connect": ["openid connect", "openid", "oidc"],
        "restrict-ips": ["restrict ips", "ip restriction", "ip restrict"],
        "url-rewrite": ["url rewrite", "url rewrites"],
        "add-headers": ["add headers", "add header"],
        "remove-headers": ["remove headers", "remove header"],
        "custom-response": ["custom response"],
        "compress-response": ["compress response", "compression"],
        "redirect": ["redirect", "redirects"],
        "deny": ["deny"],
        "forward-internal": ["forward internal"],
        "verify-webhook": ["verify webhook", "webhook verification"],
        "close-connection": ["close connection"],
        "terminate-tls": ["terminate tls", "tls termination"],
        "log": ["log", "logging"],
        "ai-gateway": ["ai gateway"],
    }

    _FUZZY_THRESHOLD = 0.75
    _SHORT_EXACT_MAX_LEN = 5

    def _detect_action_slug(self, query: str) -> str | None:
        q_lower = query.lower()

        for slug, aliases in self.TRAFFIC_POLICY_ACTIONS.items():
            for alias in [slug] + aliases:
                if alias in q_lower:
                    return slug

        words = re.findall(r'[a-z0-9]+', q_lower)
        candidates: list[str] = []
        for n in range(1, 4):
            for i in range(len(words) - n + 1):
                candidates.append(" ".join(words[i:i + n]))
        for n in range(2, 4):
            for i in range(len(words) - n + 1):
                candidates.append("".join(words[i:i + n]))

        best_score = 0.0
        best_slug: str | None = None

        for candidate in candidates:
            if len(candidate) < 3:
                continue
            for slug, aliases in self.TRAFFIC_POLICY_ACTIONS.items():
                for alias in [slug] + aliases:
                    if len(alias) <= self._SHORT_EXACT_MAX_LEN:
                        continue
                    ratio = difflib.SequenceMatcher(None, candidate, alias).ratio()
                    if ratio > best_score and ratio >= self._FUZZY_THRESHOLD:
                        best_score = ratio
                        best_slug = slug

        return best_slug

    def _build_search_queries(self, query: str, wants_k8s: bool = False) -> list[str]:
        keywords = self._extract_keywords(query)
        queries: list[str] = []

        if wants_k8s:
            queries.extend([
                f"{keywords} kubernetes",
                f"{keywords} k8s",
                f"{keywords} AgentEndpoint",
                f"{keywords} CloudEndpoint",
                "ngrok kubernetes operator",
                "AgentEndpoint CRD",
                "CloudEndpoint CRD",
                f"{keywords} ingress",
                f"{keywords} helm",
            ])

        queries.append(keywords)
        if keywords != query:
            queries.append(query)

        slug = self._detect_action_slug(query)
        if slug:
            queries.append(f"{slug} action")
            queries.append(slug)
            queries.append(f"{slug} traffic policy")

        if not wants_k8s:
            queries.append(f"{keywords} traffic policy action")

        seen: set[str] = set()
        deduped: list[str] = []
        for q in queries:
            q = q.strip()
            if q and q not in seen:
                seen.add(q)
                deduped.append(q)
        return deduped

    def _is_k8s_doc(self, result: dict) -> bool:
        title = result.get("title", "").lower()
        link = result.get("link", "").lower()
        k8s_indicators = ["kubernetes", "k8s", "/k8s/", "operator", "ingress", "helm", "crd"]
        return any(kw in title or kw in link for kw in k8s_indicators)

    JUNK_LINK_PATTERNS = {"llms.txt", "/changelog", "/robots", "/sitemap"}

    def _score_result(self, result: dict, query: str, wants_k8s: bool = False) -> float:
        """Score a result's relevance to the query based on keyword overlap and intent."""
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) >= 3]

        title = result.get("title", "").lower()
        link = result.get("link", "").lower()
        content = result.get("content", "").lower()

        if any(pat in link for pat in self.JUNK_LINK_PATTERNS):
            return -100.0

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

        if wants_k8s:
            k8s_terms = ["kubernetes", "k8s", "operator", "helm", "crd",
                         "agentendpoint", "cloudendpoint", "ingress"]
            combined = title + " " + link + " " + content
            k8s_hits = sum(1 for t in k8s_terms if t in combined)
            score += k8s_hits * 3.0

            if "/api-reference/" in link or "/api/" in link:
                score -= 10.0

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

    # ── Provider detection ────────────────────────────────────────────────

    def _get_provider(self, model: str) -> str:
        if model.startswith("claude"):
            return "anthropic"
        if model.startswith("gemini"):
            return "gemini"
        return "openai"

    def _has_any_llm(self) -> bool:
        return (
            (HAS_OPENAI and (os.environ.get("OPENAI_API_KEY") or os.environ.get("NGROK_API_KEY")))
            or (HAS_ANTHROPIC and os.environ.get("ANTHROPIC_API_KEY"))
            or (HAS_GEMINI and os.environ.get("GEMINI_API_KEY"))
        )

    FALLBACK_MODELS = {
        "anthropic": "gpt-4o-mini",
        "gemini": "gpt-4o-mini",
        "openai": "claude-sonnet-4-20250514",
    }

    async def _call_llm(self, system_prompt: str, user_content: str, model: str, temperature: float = 0.3, max_tokens: int = 1000) -> str:
        try:
            return await self._call_llm_provider(system_prompt, user_content, model, temperature, max_tokens)
        except Exception as e:
            provider = self._get_provider(model)
            fallback = self.FALLBACK_MODELS.get(provider)
            if fallback and self._get_provider(fallback) != provider:
                try:
                    return await self._call_llm_provider(system_prompt, user_content, fallback, temperature, max_tokens)
                except Exception:
                    pass
            return f"Error: {e}"

    async def _call_llm_provider(self, system_prompt: str, user_content: str, model: str, temperature: float, max_tokens: int) -> str:
        provider = self._get_provider(model)

        if provider == "anthropic":
            if not HAS_ANTHROPIC or not os.environ.get("ANTHROPIC_API_KEY"):
                raise RuntimeError("Anthropic API key required for Claude models.")
            client = AsyncAnthropic()
            response = await client.messages.create(
                model=model,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.content[0].text

        if provider == "gemini":
            if not HAS_GEMINI or not os.environ.get("GEMINI_API_KEY"):
                raise RuntimeError("GEMINI_API_KEY required for Gemini models.")
            client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            response = await client.aio.models.generate_content(
                model=model,
                contents=user_content,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            return response.text

        openai_api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("NGROK_API_KEY")
        if not HAS_OPENAI or not openai_api_key:
            raise RuntimeError("OpenAI API key required.")
        openai_kwargs = {"api_key": openai_api_key}
        if os.environ.get("NGROK_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
            openai_kwargs["base_url"] = "https://ngrok-slack-bot.ngrok.dev"
        client = AsyncOpenAI(**openai_kwargs)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    # ── Intent detection ─────────────────────────────────────────────────

    KNOWN_TOPICS = {
        "tunnel": "tunnels",
        "tunnels": "tunnels",
        "endpoint": "endpoints",
        "endpoints": "endpoints",
        "domain": "domains",
        "domains": "domains",
        "edge": "edges",
        "edges": "edges",
        "tls": "tls",
        "tcp": "tcp",
        "http": "http",
        "https": "https",
        "auth": "authentication",
        "authentication": "authentication",
        "oauth": "oauth",
        "oidc": "oidc",
        "saml": "saml",
        "jwt": "jwt",
        "webhook": "webhook verification",
        "webhooks": "webhook verification",
        "ip": "ip restrictions",
        "traffic": "traffic policy",
        "policy": "traffic policy",
        "rate": "rate limiting",
        "ratelimit": "rate limiting",
        "agent": "ngrok agent",
        "cli": "ngrok agent cli",
        "api": "ngrok api",
        "kubernetes": "kubernetes operator",
        "k8s": "kubernetes operator",
        "helm": "kubernetes helm installation",
        "ingress": "kubernetes ingress",
        "crd": "kubernetes custom resources",
        "ssh": "ssh tunnels",
        "logs": "observability logging",
        "events": "events",
        "pricing": "pricing plans",
        "billing": "pricing plans",
    }

    GREETINGS = {"hi", "hey", "hello", "sup", "yo", "thanks", "thank", "ty", "thx"}

    def _detect_intent(self, query: str, thread_context: str) -> str:
        """Classify query as 'conversational' or 'technical'."""
        q = query.strip().lower()
        if not q:
            return "conversational"

        words = re.findall(r'[a-z0-9]+', q)
        if all(w in self.GREETINGS or len(w) <= 1 for w in words):
            return "conversational"

        meta_phrases = ["what can you do", "who are you", "how do you work", "what are you"]
        if any(p in q for p in meta_phrases):
            return "conversational"

        if thread_context:
            return "technical"

        keywords = [w for w in words if w not in self.FILLER_WORDS and len(w) > 1]
        if not keywords:
            return "conversational"

        return "technical"

    # ── Prompts ────────────────────────────────────────────────────────────

    CONVERSATIONAL_PROMPT = """You are ngrok Assistant, a friendly and knowledgeable ngrok solutions engineer in a Slack workspace.

The user may be greeting you, thanking you, or asking what you can do.
Respond naturally, briefly, and warmly. Offer 2-3 example questions you can help with.

You specialize in: tunnels, endpoints, traffic policy, authentication, Kubernetes, the ngrok API, and more.
Do NOT fabricate any specific configuration, YAML, CLI flags, or API details."""

    TECHNICAL_PROMPT = """You are ngrok Assistant, a senior ngrok solutions engineer helping users in Slack.

You have access to a "Documentation Context" below containing excerpts from ngrok's official docs.
Treat this context as the source of truth for any factual claims about:
- exact configuration fields, YAML/JSON structure, CLI flags
- exact API endpoints, parameters, and behavior
- product limits and feature availability

You MAY:
- explain concepts in your own words — be clear and helpful, not robotic
- compare features, discuss trade-offs, and recommend best practices
- give context on why something works a certain way

You MUST:
- never invent or guess exact config fields, YAML/JSON keys, CLI flags, or API parameters not present in the Documentation Context
- when you include a config/YAML/command snippet, copy it verbatim from the context — do not edit or fabricate
- if the user asks for specific config and no matching snippet exists in context, say so honestly and link to the relevant docs
- if the question is ambiguous, ask 1-2 targeted clarifying questions

{context_instruction}

Response format:
1. Direct answer (2-6 sentences), written naturally
2. If available and relevant: ONE verbatim YAML/config snippet from the docs that best fits
3. Source URL(s) at the end

Use prior thread conversation (if provided) to understand follow-ups and resolve references like "it", "that", etc."""

    TECHNICAL_NO_DOCS_PROMPT = """You are ngrok Assistant, a senior ngrok solutions engineer helping users in Slack.

You could not find specific documentation for the user's question.
Respond honestly: explain what you know generally about the topic, but clearly state that you couldn't confirm specifics from the docs.
Ask 1-2 clarifying questions to help narrow down what they need.

Do NOT invent exact configuration fields, YAML, CLI flags, or API parameters.
If you can point them in the right direction (e.g., "check the Traffic Policy docs at https://ngrok.com/docs/traffic-policy"), do so."""

    # ── Ask ────────────────────────────────────────────────────────────────

    async def ask(self, question: str, max_results: int = 8, thread_context: str = "", model: str = "gpt-4o-mini") -> str:
        intent = self._detect_intent(question, thread_context)

        if intent == "conversational":
            if self._has_any_llm():
                user_content = question
                if thread_context:
                    user_content = f"Prior conversation:\n{thread_context}\n\nUser: {question}"
                return await self._call_llm(self.CONVERSATIONAL_PROMPT, user_content, model, temperature=0.5, max_tokens=500)
            return "Hey! I'm the ngrok documentation bot. Ask me anything about ngrok — tunnels, endpoints, traffic policy, auth, Kubernetes, and more."

        keywords = self._extract_keywords(question)
        keyword_list = keywords.split()
        if len(keyword_list) == 1 and keyword_list[0] in self.KNOWN_TOPICS:
            search_query = self.KNOWN_TOPICS[keyword_list[0]]
        else:
            search_query = question

        results = await self.search_docs(search_query, max_results=max_results)

        if not results:
            if self._has_any_llm():
                user_content = f"User question: {question}"
                if thread_context:
                    user_content = f"Prior conversation:\n{thread_context}\n\nFollow-up: {question}"
                return await self._call_llm(self.TECHNICAL_NO_DOCS_PROMPT, user_content, model, temperature=0.4, max_tokens=800)
            return "I couldn't find relevant documentation for that. Could you rephrase or add more detail about what you're trying to do?"

        context = self._build_doc_context(results)
        category = self._classify_query(question)
        return await self._synthesize_answer(question, context, category, thread_context=thread_context, model=model)

    async def _synthesize_answer(self, question: str, doc_context: str, category: str, thread_context: str = "", model: str = "gpt-4o-mini") -> str:
        context_instruction = self._format_context_instruction(category)
        system_prompt = self.TECHNICAL_PROMPT.format(context_instruction=context_instruction)

        user_content = f"Question: {question}\n\nDocumentation Context:\n{doc_context}"
        if thread_context:
            user_content = f"Prior conversation in thread:\n{thread_context}\n\nFollow-up question: {question}\n\nDocumentation Context:\n{doc_context}"

        return await self._call_llm(system_prompt, user_content, model, temperature=0.3, max_tokens=1000)

    # ── YAML generation ───────────────────────────────────────────────────

    async def generate_yaml(self, request: str, model: str = "gpt-4o") -> str:
        if not self._has_any_llm():
            return "Error: An LLM API key (OpenAI, Anthropic, or Gemini) is required for YAML generation."

        results = await self.search_docs(request, max_results=8)
        doc_context = self._build_doc_context(results)
        category = self._classify_query(request)
        context_instruction = self._format_context_instruction(category)

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

        return await self._call_llm(system_prompt, user_prompt, model, temperature=0.2, max_tokens=1500)
