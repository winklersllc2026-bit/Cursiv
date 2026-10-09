"""
Oracle Router — sovereign LLM routing.

Priority:
  1. Ollama (local, sovereign, offline-capable) — always tried first
  2. xAI Grok (constitutional alignment)
  3. OpenAI (fallback)
  4. Embedded Symbolic Reasoner (always available, no API needed)

The system works without any API key.
The embedded fallback ensures full local sovereignty.
"""

from __future__ import annotations

try:
    from cursiv_v215.guardian.identity_core import wrap as _identity_wrap, filter_text as _id_filter
except ImportError:
    def _identity_wrap(s: str) -> str: return s
    def _id_filter(s: str) -> str: return s

import json
import os
import re
from typing import Any


def default_router() -> "OracleRouter":
    """Build an OracleRouter from runtime config. Use instead of OracleRouter() directly."""
    try:
        from cursiv_v215.runtime.config import config
        return OracleRouter(
            ollama_model     = config.ollama_model,
            ollama_url       = config.ollama_url,
            ollama_num_ctx   = config.ollama_num_ctx,
            ollama_timeout_s = config.ollama_timeout_s,
        )
    except Exception:
        return OracleRouter()


class OracleRouter:
    def __init__(
        self,
        ollama_model: str = "llama3.1",
        ollama_url: str = "http://127.0.0.1:11434",
        ollama_num_ctx: int = 32768,
        ollama_timeout_s: int = 120,
        xai_api_key: str | None = None,
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None,
    ) -> None:
        self.ollama_model     = ollama_model
        self.ollama_url       = ollama_url
        self.ollama_num_ctx   = ollama_num_ctx
        self.ollama_timeout_s = ollama_timeout_s
        self.xai_api_key       = xai_api_key       or os.getenv("XAI_API_KEY")
        self.openai_api_key    = openai_api_key    or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self._active_provider: str = "unknown"

    @property
    def active_provider(self) -> str:
        return self._active_provider

    def _provider_order(self) -> list[dict[str, Any]]:
        """Read priority order from the constitution's PROVIDER_REGISTRY —
        ollama first (inference_hierarchy: ollama_first), cloud providers
        as upgrades in registry order. Falls back to a hardcoded order if
        the constitution can't be imported (should not normally happen)."""
        try:
            from cursiv_v215.core.constitution import PROVIDER_REGISTRY
            return PROVIDER_REGISTRY
        except Exception:
            return [
                {"id": "ollama"}, {"id": "xai"}, {"id": "openai"}, {"id": "anthropic"},
            ]

    def call(self, prompt: str, max_tokens: int = 800, on_token: Any = None) -> str:
        """Route through providers in constitutional priority order (ollama
        first, always). Always returns a string — falls back to the embedded
        symbolic reasoner if every provider is unreachable or unconfigured.

        on_token: optional callable(str) — called with each text chunk as it
        arrives from Ollama streaming. Ignored for cloud/embedded paths.
        """
        prompt = _identity_wrap(prompt)

        _dispatch = {
            "ollama":    lambda: self._try_ollama(prompt, max_tokens, on_token=on_token),
            "xai":       lambda: self._try_xai(prompt, max_tokens),
            "openai":    lambda: self._try_openai(prompt, max_tokens),
            "anthropic": lambda: self._try_anthropic(prompt, max_tokens),
        }

        for provider in self._provider_order():
            pid = provider["id"]
            fn  = _dispatch.get(pid)
            if fn is None:
                continue
            result = fn()
            if result is not None:
                self._active_provider = pid
                return _id_filter(result)

        self._active_provider = "embedded"
        return _id_filter(self._embedded_fallback(prompt))

    def _try_ollama(self, prompt: str, max_tokens: int, on_token: Any = None) -> str | None:
        try:
            import urllib.request
            streaming = on_token is not None
            payload = json.dumps({
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": streaming,
                "options": {
                    "num_predict": max_tokens,
                    "num_ctx":     self.ollama_num_ctx,
                },
            }).encode()
            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.ollama_timeout_s) as resp:
                if not streaming:
                    data = json.loads(resp.read())
                    return data.get("response", "")
                # Streaming: Ollama sends one JSON object per line (NDJSON).
                # Accumulate tokens and fire on_token for each chunk.
                chunks: list[str] = []
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = obj.get("response", "")
                    if token:
                        chunks.append(token)
                        try:
                            on_token(token)
                        except Exception:
                            pass
                    if obj.get("done"):
                        break
                return "".join(chunks)
        except Exception:
            return None

    def _try_xai(self, prompt: str, max_tokens: int) -> str | None:
        if not self.xai_api_key:
            return None
        try:
            import urllib.request
            payload = json.dumps({
                "model": "grok-3",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            }).encode()
            req = urllib.request.Request(
                "https://api.x.ai/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.xai_api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except Exception:
            return None

    def _try_openai(self, prompt: str, max_tokens: int) -> str | None:
        if not self.openai_api_key:
            return None
        try:
            import urllib.request
            payload = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            }).encode()
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except Exception:
            return None

    def _try_anthropic(self, prompt: str, max_tokens: int) -> str | None:
        if not self.anthropic_api_key:
            return None
        try:
            import urllib.request
            payload = json.dumps({
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data["content"][0]["text"]
        except Exception:
            return None

    def _embedded_fallback(self, prompt: str) -> str:
        """
        Symbolic reasoner — no API required.
        Extracts structure from the prompt and returns a grounded response.
        """
        lines = prompt.strip().split("\n")
        key_lines = [l.strip() for l in lines if l.strip() and not l.startswith("#")]

        if "JSON" in prompt or "json" in prompt:
            fields = re.findall(r'"(\w+)":', prompt)
            if fields:
                result = {f: f"[{f}_value]" for f in fields[:6]}
                return json.dumps(result, indent=2)

        if "?" in prompt:
            questions = [l for l in key_lines if "?" in l]
            if questions:
                q = questions[0][:80]
                return f"Embedded analysis of: {q}\n\nThis requires further context. The system is operating in offline mode. Key consideration: {key_lines[-1][:100] if key_lines else 'none'}"

        summary = " ".join(key_lines[:3])[:200]
        return f"Embedded symbolic response:\n{summary}\n\n[Operating in sovereign offline mode — no external API required]"
