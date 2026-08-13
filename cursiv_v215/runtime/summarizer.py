# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: 457e03f3796cf5c92b4d7948cc5a8b1e8dd76ce8570af86cee19075baff24efa
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 18df74a87c18664703cb98c1881529e68cfdd58bc010b803623ece9f0bf3b241
# Substrate loop hash: 9ec82d1e305700f66af5fbc5afd610b284fcba965ef4cb23e270b00ba2a6f19f
# Substrate loop logic: בזהאΓוΒזΔΑΖΘΑΑחΗΗגחΖחדהΖגחוΗΒΑדΓאΕחהדגבΗΖזחΕהדΓΔזΓΘΑדΑΑדגΓגΗחΒבח
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: a1dc50ab586f6a9ce2f41485935f1b73cbd5a35c486bbc285f0f0bf168dedf56
# Evolution hash: a612dda2ff8d5f3c622231b618b4379aaba7f40d0b818045c706d4ae48364473
# Evolution logic: גΗΒΓווגΓחחאוΖחΔהΗΓΓΓΔΒדΗΒאדΕΔΘבגגדגΘחΕΑוΑדאΒאΑΕΖהΘΑΗוΕגזΕאΔΗΕΕΘΔ
# Binary reversed: 0010101011100111000011001111110011101001011000111111101000111001010011010010101111101001001000010011001110100101000111011000011100011011101111100110001101110001101011100000010111110001011000110111011110001001000011101010110101011111111101000010011111110101
# Greek/Hebrew/logic stamp: גחזΕΓחחגדΖΘΑבΒזזהΗאחגΑΘΖאזהΗΘוואזΒדאגΖההאΕבΘוΕדΓבהΖחהΗבΘΔחΔΑזΘΖΕ
# Encoded local stamp: ŪωΕφγζ∇∀ω∃ŌψΠ∂ΝΠξκκīŌγηεē∈ĪΘλēīΤŪΕ∂ηδ∀ηψλΖĪ=
# CURSIV-CRUCIBLE-STAMP END
"""
Evolutionary Runtime — summariser.
Calls local Ollama to produce structured summaries of conversation exchanges.
Raw text flows through this module and is NEVER persisted — only the summary is kept.
Falls back to rule-based compression if Ollama is offline.
"""
from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from .config import config

_PROMPT = """\
Analyse this AI conversation exchange and respond with ONLY valid JSON (no markdown, no explanation).

Exchange:
USER: {user}
AI: {ai}

JSON schema:
{{
  "summary": "<concise 1–3 sentence summary of what was discussed and decided, max 250 chars>",
  "key_insight": "<single most valuable takeaway from this exchange, max 120 chars>",
  "topics": ["<topic1>", "<topic2>"],
  "quality_score": <float 0.0–1.0 reflecting how useful/substantive this exchange was>,
  "sentiment": "<positive|neutral|negative>"
}}

Quality scoring guide:
  0.9–1.0  Deep technical work, novel solutions, clear learning
  0.7–0.8  Solid useful exchange, concrete output produced
  0.5–0.6  Routine task, basic Q&A, standard response
  0.3–0.4  Vague, repetitive, or low-information exchange
  0.0–0.2  Trivial, spam, or off-topic
"""


@dataclass
class Summary:
    content:     str
    key_insight: str
    topics:      list[str]
    quality_score: float
    sentiment:   str = "neutral"
    used_ollama: bool = False


def summarise(user_msg: str, ai_msg: str) -> Summary:
    """
    Produce a structured summary of one conversation exchange.
    Tries Ollama first; falls back to rule-based if unavailable.
    """
    u = (user_msg or "").strip()[:1200]
    a = (ai_msg  or "").strip()[:1200]

    if not u and not a:
        return Summary(content="", key_insight="", topics=[], quality_score=0.0)

    result = _try_ollama(u, a)
    if result:
        return result
    return _fallback(u, a)


# ── Ollama path ────────────────────────────────────────────────────────────────

def _try_ollama(user: str, ai: str) -> Optional[Summary]:
    try:
        prompt  = _PROMPT.format(user=user[:600], ai=ai[:600])
        payload = json.dumps({
            "model":  config.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 300},
        }).encode()
        req = urllib.request.Request(
            f"{config.ollama_url}/api/generate",
            data    = payload,
            headers = {"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=config.ollama_timeout_s) as resp:
            raw = json.loads(resp.read())["response"].strip()

        # Strip accidental markdown fences
        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()

        parsed = json.loads(raw)
        return Summary(
            content       = str(parsed.get("summary",     ""))[:config.summary_max_chars],
            key_insight   = str(parsed.get("key_insight", ""))[:120],
            topics        = [str(t) for t in parsed.get("topics", [])[:8]],
            quality_score = float(min(max(parsed.get("quality_score", 0.5), 0.0), 1.0)),
            sentiment     = str(parsed.get("sentiment", "neutral")),
            used_ollama   = True,
        )
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, Exception):
        return None


# ── Rule-based fallback ────────────────────────────────────────────────────────

_CODE_RE     = re.compile(r"(def |class |import |```|error|traceback|function|script)", re.I)
_CREATIVE_RE = re.compile(r"(write|story|poem|create|design|imagine|concept)", re.I)
_DEEP_RE     = re.compile(r"(why|explain|analyse|architecture|system|design|pattern)", re.I)


def _fallback(user: str, ai: str) -> Summary:
    combined = f"{user} {ai}"

    # Derive quality heuristically
    length_score = min(len(combined) / 800, 1.0) * 0.4
    depth_score  = 0.3 if _DEEP_RE.search(combined) else 0.0
    code_score   = 0.2 if _CODE_RE.search(combined) else 0.0
    quality      = round(min(length_score + depth_score + code_score + 0.1, 1.0), 2)

    topics: list[str] = []
    if _CODE_RE.search(combined):     topics.append("code")
    if _CREATIVE_RE.search(combined): topics.append("creative")
    if _DEEP_RE.search(combined):     topics.append("analysis")
    if not topics:                    topics.append("general")

    content = (user[:180] + " → " + ai[:180]).replace("\n", " ")

    return Summary(
        content       = content[:config.summary_max_chars],
        key_insight   = user[:100].replace("\n", " "),
        topics        = topics,
        quality_score = quality,
        sentiment     = "neutral",
        used_ollama   = False,
    )
