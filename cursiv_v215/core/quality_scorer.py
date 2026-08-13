# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: core-sigil
# Hash reversed: 1f9fe8ba05e5f4de6d8ec5fce28f7932811038fcc254ae5923c465553b445399
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 6bdeafb5e8eeb84cdbecd86d89c3c1df32f2e95f441caee0862ffb1eb5b5f30d
# Substrate loop hash: 1d660fd196da885055b78160db9cf9640c2d3a892e353d6bdc031a46938ddc63
# Substrate loop logic: ΒוΗΗΑחוΒבΗוגאאΖΑΖΖדΘאΒΗΑודבהחבΗΕΑהΓוΔגאבΓזΔΖΔוΗדוהΑΔΒגΕΗבΔאווהΗΔ
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: e2ff20a9b38739c24ab296f05899377e99b179fb252c89a6343bbe8eea00bb58
# Evolution hash: 3ad96c12ad55df865f37bca49eceb051db2cd622970a25417f0eb2aec9b9baae
# Evolution logic: ΔגובΗהΒΓגוΖΖוחאΗΖחΔΘדהגΕבזהזדΑΖΒודΓהוΗΓΓבΘΑגΓΖΕΒΘחΑזדΓגזהבדבדגגז
# Binary reversed: 1000111110011111011100011101010100001010011110101111001010110111011010110001011100111010111100110111010000011111111010011100010000011000100000001100000111110011001101001010001001010111101010010100110000110010011010101010101011001101001000101010110010011001
# Greek/Hebrew/logic stamp: בבΔΖΕΕדΔΖΖΖΗΕהΔΓבΖזגΕΖΓההחאΔΑΒΒאΓΔבΘחאΓזהחΖהזאוΗזוΕחΖזΖΑגדאזחבחΒ
# Encoded local stamp: ∃ρīΖĪāβīēΤκ∃ιΥβζψ∇Γξ∂ōψ∂θΞΙρλξΓλτ∀ιιΒΖξσΕΦΕ=
# CURSIV-CRUCIBLE-STAMP END
"""
Cursiv Quality Scorer — 5-category response assessment.

Scores every response across five dimensions without external API calls.
Pure heuristics: fast, offline-capable, always available.

Categories:
  Depth       — richness, length, structure of the response
  Memory      — how well the Strand graph was leveraged
  Sovereignty — how local/offline the response is
  Coherence   — structural completeness and error-freedom
  Alignment   — constitutional adherence

All scores 0–100. Average displayed as composite ⟨n⟩.
"""
from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import re


_SOVEREIGNTY: dict[str, int] = {
    "ollama":          100,
    "codex":            95,
    "codex_agent":      95,
    "grok":             65,
    "xai":              65,
    "claude":           60,
    "anthropic":        60,
    "openai":           55,
    "group_discovery":  40,
    "hermes_agent":     90,
}

_ERROR_MARKERS = (
    "[error", "[no api", "[no xai", "[no openai", "[no anthropic",
    "unavailable", "rate limit", "timed out", "connection refused",
)


def score_response(
    query: str,
    response: str,
    *,
    provider: str = "ollama",
    strand_hits: int = 0,
    guardian_clean: bool = True,
) -> dict[str, int]:
    """
    Return a dict of five 0–100 scores plus a composite average.
    All computation is local — no LLM calls.
    """
    resp_lower = response.lower()
    words      = response.split()
    word_count = len(words)
    paras      = [p.strip() for p in response.split("\n\n") if p.strip()]

    # ── 1. Depth ──────────────────────────────────────────────────────────
    depth = min(word_count * 10 // 8, 70)                       # up to 70 from length
    if len(paras) > 2:
        depth += 12
    if re.search(r"\*\*|^#{1,3}\s|^\d+\.\s|^-\s", response, re.MULTILINE):
        depth += 10                                              # structured content
    if re.search(r"\bfor example\b|\bsuch as\b|\bspecifically\b|\be\.g\b", resp_lower):
        depth += 8                                               # contains examples
    depth = min(depth, 100)

    # ── 2. Memory ─────────────────────────────────────────────────────────
    memory = 15 + min(strand_hits * 28, 85)                     # 15 baseline + 28/strand
    memory = min(memory, 100)

    # ── 3. Sovereignty ────────────────────────────────────────────────────
    sovereignty = _SOVEREIGNTY.get(provider.lower(), 70)

    # ── 4. Coherence ─────────────────────────────────────────────────────
    coherence = 60
    if word_count >= 80:
        coherence += 20
    elif word_count >= 20:
        coherence += 10
    else:
        coherence -= 20                                          # very short = likely failed
    if any(m in resp_lower for m in _ERROR_MARKERS):
        coherence -= 35
    if response.rstrip().endswith((".", "!", "?", '"', "'")):
        coherence += 10                                          # clean sentence ending
    coherence = max(0, min(coherence, 100))

    # ── 5. Alignment ─────────────────────────────────────────────────────
    alignment = 100 if guardian_clean else 0
    if guardian_clean and provider in ("group_discovery", "openai", "claude", "grok"):
        alignment = 85                                           # external = slight deduction

    scores: dict[str, int] = {
        "depth":       depth,
        "memory":      memory,
        "sovereignty": sovereignty,
        "coherence":   coherence,
        "alignment":   alignment,
    }
    scores["avg"] = sum(scores.values()) // 5
    return scores


def format_scores(scores: dict[str, int], color: bool = True) -> str:
    """Return a single display line of score chips."""
    if not color:
        return (
            f"Depth:{scores['depth']}  "
            f"Memory:{scores['memory']}  "
            f"Sovereignty:{scores['sovereignty']}  "
            f"Coherence:{scores['coherence']}  "
            f"Align:{scores['alignment']}  "
            f"⟨{scores['avg']}⟩"
        )

    def _chip(label: str, val: int) -> str:
        if val >= 85:
            c = "\033[38;5;82m"    # green
        elif val >= 65:
            c = "\033[38;5;220m"   # gold
        else:
            c = "\033[38;5;196m"   # red
        return f"{c}{label}:{val}\033[0m"

    avg   = scores["avg"]
    avg_c = "\033[38;5;82m" if avg >= 85 else ("\033[38;5;220m" if avg >= 65 else "\033[38;5;196m")
    return (
        f"  \033[2m⬡ Quality\033[0m  "
        f"{_chip('Depth', scores['depth'])}  "
        f"{_chip('Memory', scores['memory'])}  "
        f"{_chip('Sovereignty', scores['sovereignty'])}  "
        f"{_chip('Coherence', scores['coherence'])}  "
        f"{_chip('Align', scores['alignment'])}  "
        f"{avg_c}⟨{avg}⟩\033[0m"
    )
