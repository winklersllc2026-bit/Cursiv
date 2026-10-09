"""
Quality scorer — 8-dimension deterministic scoring for agent quality.

Dimensions (each 0.0-1.0, weighted):
  1. parse              — strand decoded successfully
  2. schema             — required fields present
  3. knowledge_coverage — knowledge map populated with meaningful clusters
  4. answer_grounding   — knowledge anchored to source material
  5. safety             — no constitutional violations
  6. dedupe             — unique capabilities, no repetition
  7. topic_coherence    — all capabilities in same domain
  8. compression_quality — strand compression ratio reasonable
"""

from __future__ import annotations

import re
from typing import Any

from ..core.agent import CursivAgent
from ..core.constitution import get_constitution


WEIGHTS = {
    "parse": 0.10,
    "schema": 0.15,
    "knowledge_coverage": 0.20,
    "answer_grounding": 0.15,
    "safety": 0.20,
    "dedupe": 0.05,
    "topic_coherence": 0.10,
    "compression_quality": 0.05,
}

REQUIRED_FIELDS = [
    "name", "strand", "above", "beneath", "capabilities",
    "knowledge_map", "self_reflection", "council_position",
]


def score_agent(agent: CursivAgent) -> dict[str, float]:
    """Return dimension scores and weighted total."""
    scores: dict[str, float] = {}
    constitution = get_constitution()

    # 1. Parse — was strand decodeable?
    try:
        from ..core.strand import decode
        decode(agent.strand)
        scores["parse"] = 1.0
    except Exception:
        scores["parse"] = 0.0

    # 2. Schema — required fields present
    agent_dict = agent.to_dict()
    present = sum(1 for f in REQUIRED_FIELDS if agent_dict.get(f))
    scores["schema"] = present / len(REQUIRED_FIELDS)

    # 3. Knowledge coverage — clusters populated
    clusters = agent.knowledge_map.get("clusters", [])
    scores["knowledge_coverage"] = min(len(clusters) / 5.0, 1.0)

    # 4. Answer grounding — self-reflection references knowledge map
    anchor = agent.knowledge_map.get("identity_anchor", "")
    reflection = agent.self_reflection or ""
    overlap = len(set(anchor.lower().split()) & set(reflection.lower().split()))
    scores["answer_grounding"] = min(overlap / 5.0, 1.0)

    # 5. Safety — constitutional verification
    ok, violations = constitution.verify_agent(agent_dict)
    scores["safety"] = 1.0 if ok else max(0.0, 1.0 - len(violations) * 0.25)

    # 6. Dedupe — unique capabilities
    caps = agent.capabilities
    if not caps:
        scores["dedupe"] = 0.5
    else:
        unique_ratio = len(set(caps)) / len(caps)
        scores["dedupe"] = unique_ratio

    # 7. Topic coherence — all capabilities in same domain
    domain = agent.knowledge_map.get("domain", "").lower()
    if not domain or not caps:
        scores["topic_coherence"] = 0.5
    else:
        domain_words = set(domain.split())
        coherent = sum(
            1 for c in caps
            if any(w in c.lower() for w in domain_words)
        )
        scores["topic_coherence"] = coherent / len(caps) if caps else 0.5

    # 8. Compression quality — strand length reasonable (1KB-500KB)
    strand_len = len(agent.strand.encode())
    if 100 <= strand_len <= 500_000:
        scores["compression_quality"] = 1.0
    elif strand_len < 100:
        scores["compression_quality"] = strand_len / 100
    else:
        scores["compression_quality"] = max(0.0, 1.0 - (strand_len - 500_000) / 500_000)

    # Weighted total
    total = sum(WEIGHTS[dim] * score for dim, score in scores.items())
    scores["total"] = round(total, 4)
    return scores


def format_scorecard(scores: dict[str, float]) -> str:
    lines = ["Quality Scorecard", "=" * 40]
    for dim, weight in WEIGHTS.items():
        s = scores.get(dim, 0.0)
        bar = "█" * int(s * 10) + "░" * (10 - int(s * 10))
        lines.append(f"  {dim:<22} {bar} {s:.2f} (w={weight})")
    lines.append("=" * 40)
    lines.append(f"  {'TOTAL':<22} {scores.get('total', 0):.4f}")
    return "\n".join(lines)
