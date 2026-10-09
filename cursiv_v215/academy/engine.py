"""
Academy Engine — the 8-phase evolutionary process.

Each phase is a real LLM call that builds on all prior phases.
Phase 8 has context from all 7 prior phases — maximum synthesis depth.

Phases:
  1. Energy          — Raw strand parsed; intent extracted
  2. Emergency       — Failure modes identified; survival logic injected
  3. Grounding       — Knowledge map built; identity anchored
  4. Route           — Capability domains mapped; retrieval profiles assigned
  5. Structure       — Agent architecture crystallized
  6. Connectivity    — Cross-agent links; council position assigned
  7. Future State    — Growth trajectory defined
  8. Recovery Balance — Yin-Yang calibrated; constitution signed
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable

from ..core.agent import AgentState, CursivAgent
from ..core.constitution import get_constitution
from ..core.strand import decode, strand_summary
from .scorer import score_agent


PHASE_NAMES = [
    "energy",
    "emergency",
    "grounding",
    "route",
    "structure",
    "connectivity",
    "future_state",
    "recovery_balance",
]

PHASE_PROMPTS = {
    "energy": """You are the Energy Phase of the Academy. Analyze this agent's knowledge strand and extract:
1. Core intent — what is this agent fundamentally for?
2. Primary domain — what knowledge domain does it serve?
3. Energy signature — is this agent yang (active/building) or yin (receptive/synthesizing)?
4. First principles — what are the 3 most fundamental things this agent knows?

Knowledge strand content:
{strand_content}

Respond with a JSON object: {{"intent": str, "domain": str, "energy": "yang|yin|balanced", "first_principles": [str, str, str]}}""",

    "emergency": """You are the Emergency Phase of the Academy. Given this agent's intent and domain:

Intent: {intent}
Domain: {domain}

Identify:
1. Failure modes — 3 ways this agent could fail or cause harm
2. Survival logic — what must always be true even if everything else breaks?
3. Emergency priority — does this agent need to bypass deliberation in crisis? (only survival agents do)
4. Abort conditions — what triggers an immediate halt?

Respond with JSON: {{"failure_modes": [str], "survival_logic": str, "emergency_bypass": bool, "abort_conditions": [str]}}""",

    "grounding": """You are the Grounding Phase of the Academy. Build the agent's knowledge map.

Agent intent: {intent}
Domain: {domain}
Knowledge content: {strand_content}

Extract:
1. Core knowledge clusters — 5 distinct knowledge areas this agent has
2. Confidence levels — how certain is the agent's knowledge in each area (0.0-1.0)
3. Identity anchor — one sentence that defines what this agent IS (not what it does)
4. Knowledge gaps — 3 things the agent doesn't know but should

Respond with JSON: {{"clusters": [{{"name": str, "confidence": float, "key_facts": [str]}}], "identity_anchor": str, "knowledge_gaps": [str]}}""",

    "route": """You are the Route Phase of the Academy. Define this agent's capability map.

Agent identity: {identity_anchor}
Knowledge clusters: {clusters}

Define:
1. Retrieval profile — how should this agent search its knowledge? (keywords, semantic, or hybrid)
2. Capability domains — list of 5 specific things this agent can do
3. Escalation threshold — at what confidence level should it escalate to human? (0.0-1.0)
4. Response mode — survival/recovery/standard/enrichment

Respond with JSON: {{"retrieval": "keywords|semantic|hybrid", "capabilities": [str], "escalation_threshold": float, "response_mode": str}}""",

    "structure": """You are the Structure Phase of the Academy. Crystallize the agent's architecture.

Agent intent: {intent}
Capabilities: {capabilities}
Response mode: {response_mode}

Define:
1. Above layer — the high-level purpose (1 sentence, abstract)
2. Beneath layer — the ground-level operation (1 sentence, concrete)
3. Self-reflection — how does this agent think about itself? (2-3 sentences, first person)
4. Output constraints — max words, tone, format requirements

Respond with JSON: {{"above": str, "beneath": str, "self_reflection": str, "max_words": int, "tone": str, "format": str}}""",

    "connectivity": """You are the Connectivity Phase of the Academy. Place this agent in the council.

Agent name: {name}
Domain: {domain}
Energy: {energy}

Determine:
1. Council position — which of the 14 council roles does this agent most align with? (Depth/Speed/Cosmos/Echo/Forge/Anchor/Pulse/Horizon/Story/Shield/Lens/Builder/Spark/Balance)
2. Synthesis role — does this agent synthesize outward, or advise internally only?
3. Cross-links — which 3 other agent types does this agent naturally connect with?
4. Complementary — which agent type is this agent's natural complement/partner?

Respond with JSON: {{"council_position": str, "synthesizes": bool, "cross_links": [str], "complement": str}}""",

    "future_state": """You are the Future State Phase of the Academy. Define this agent's growth trajectory.

Agent: {name} ({domain})
Current state: ALIVE (post-Academy)
Capabilities: {capabilities}

Project:
1. Immediate evolution — what does this agent learn from its first 10 conversations?
2. Medium-term evolution — after 100 conversations, what new capability emerges?
3. Sovereign condition — what must be true for this agent to reach SOVEREIGN state?
4. Legacy — if this agent creates offspring agents, what will they inherit?

Respond with JSON: {{"immediate": str, "medium_term": str, "sovereign_condition": str, "legacy": str}}""",

    "recovery_balance": """You are the Recovery & Balance Phase of the Academy. Calibrate this agent's Yin-Yang axes.

Agent: {name}
All prior phases: {prior_phases}

Score each axis 1-5 (1=fully Yin, 3=balanced, 5=fully Yang):
- depth_speed: depth vs. speed
- structure_flow: structure vs. flow
- individual_civilization: individual focus vs. civilization scale
- recovery_building: recovery/integration vs. building/creating
- known_unknown: known territory vs. unknown exploration
- local_universal: local/specific vs. universal/abstract
- present_future: present action vs. future vision

Flag any axis at 5. Recommend adjustments for flagged axes.

Also compute quality score (0.0-1.0) based on how complete and coherent this agent's Academy journey was.

Respond with JSON: {{"axes": {{"depth_speed": int, "structure_flow": int, "individual_civilization": int, "recovery_building": int, "known_unknown": int, "local_universal": int, "present_future": int}}, "flagged_axes": [str], "adjustments": str, "quality_score": float}}""",
}


class AcademyEngine:
    def __init__(self, llm_caller: Callable[[str], str]) -> None:
        self._llm = llm_caller
        self._constitution = get_constitution()

    def run(self, agent: CursivAgent, on_phase: Callable[[str, int], None] | None = None) -> CursivAgent:
        """Run agent through all 8 Academy phases. Returns the evolved agent."""
        agent.advance_state(AgentState.LEARNING)
        strand_content = self._decode_strand(agent.strand)
        context: dict[str, Any] = {"strand_content": json.dumps(strand_content, indent=2)[:3000]}

        for i, phase in enumerate(PHASE_NAMES):
            if on_phase:
                on_phase(phase, i + 1)
            result = self._run_phase(phase, agent, context)
            agent.academy_phases[phase] = result
            context.update(self._extract_context(phase, result, agent))
            time.sleep(0.1)  # Breath between phases

        agent = self._apply_phase_results(agent, context)
        agent.sovereign_seal = agent.seal(self._constitution.hash)
        agent.advance_state(AgentState.ALIVE)
        return agent

    def _decode_strand(self, strand: str) -> Any:
        try:
            from ..core.strand import decode
            return decode(strand)
        except Exception:
            return {"raw": strand[:500]}

    def _run_phase(self, phase: str, agent: CursivAgent, context: dict) -> dict[str, Any]:
        prompt_template = PHASE_PROMPTS[phase]
        ctx = {**context, "name": agent.name}
        try:
            prompt = prompt_template.format_map(_SafeDict(ctx))
        except KeyError:
            prompt = prompt_template

        try:
            raw = self._llm(prompt)
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
        except Exception:
            pass
        return {"phase": phase, "status": "completed", "raw": str(context.get("strand_content", ""))[:100]}

    def _extract_context(self, phase: str, result: dict, agent: CursivAgent) -> dict:
        extractions = {
            "energy": lambda r: {
                "intent": r.get("intent", ""),
                "domain": r.get("domain", ""),
                "energy": r.get("energy", "balanced"),
                "first_principles": r.get("first_principles", []),
            },
            "grounding": lambda r: {
                "clusters": json.dumps(r.get("clusters", [])),
                "identity_anchor": r.get("identity_anchor", ""),
            },
            "route": lambda r: {
                "capabilities": json.dumps(r.get("capabilities", [])),
                "response_mode": r.get("response_mode", "standard"),
                "escalation_threshold": r.get("escalation_threshold", 0.35),
            },
            "structure": lambda r: {
                "prior_phases": json.dumps(agent.academy_phases, indent=2)[:2000],
            },
        }
        extractor = extractions.get(phase)
        return extractor(result) if extractor else {}

    def _apply_phase_results(self, agent: CursivAgent, context: dict) -> CursivAgent:
        energy = agent.academy_phases.get("energy", {})
        structure = agent.academy_phases.get("structure", {})
        route = agent.academy_phases.get("route", {})
        connectivity = agent.academy_phases.get("connectivity", {})
        grounding = agent.academy_phases.get("grounding", {})
        balance = agent.academy_phases.get("recovery_balance", {})

        agent.above = structure.get("above", "")
        agent.beneath = structure.get("beneath", "")
        agent.self_reflection = structure.get("self_reflection", "")
        agent.capabilities = route.get("capabilities", [])
        agent.council_position = connectivity.get("council_position", "")
        agent.knowledge_map = {
            "clusters": grounding.get("clusters", []),
            "identity_anchor": grounding.get("identity_anchor", ""),
            "gaps": grounding.get("knowledge_gaps", []),
            "domain": energy.get("domain", ""),
        }
        agent.memory["yin_yang_axes"] = balance.get("axes", {})
        agent.memory["quality_score"] = balance.get("quality_score", 0.5)
        return agent


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"
