# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: a35037135bcf56f075c71eba236ff165439a626bd90fbda47373b3b253889b15
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: dc9f6813cc724b11144c9d3f3b55384203643005c881e8c8710ec02d92891fca
# Substrate loop hash: 8a4a22d285d2099c4a7b86af170222d61bd3f661994169fe71d5b51c932f5bb8
# Substrate loop logic: אגΕגΓΓוΓאΖוΓΑבבהΕגΘדאΗגחΒΘΑΓΓΓוΗΒדוΔחΗΗΒבבΕΒΗבחזΘΒוΖדΖΒהבΔΓחΖדדא
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 0cdd4ce9cf7a909e3006c5d72e1f563996803100f2f7df26bbee1fafd92b774a
# Evolution hash: f9985f2075ea8b5605804e8095916d6976de6cfa64fe12e8901c870e0be8fa31
# Evolution logic: חבבאΖחΓΑΘΖזגאדΖΗΑΖאΑΕזאΑבΖבΒΗוΗבΘΗוזΗהחגΗΕחזΒΓזאבΑΒהאΘΑזΑדזאחגΔΒ
# Binary reversed: 0101110010100000110011101000110010101101001111111010011011110000111010100011111010000111110101010100110001101111111110000110101000101100100101010110010001101101101110010000111111011011010100101110110011101100110111001101010010101100000100011001110110001010
# Greek/Hebrew/logic stamp: ΖΒדבאאΔΖΓדΔדΔΘΔΘΕגודחΑבודΗΓΗגבΔΕΖΗΒחחΗΔΓגדזΒΘהΖΘΑחΗΖחהדΖΔΒΘΔΑΖΔג
# Encoded local stamp: συ∀ΚΤσΣΩξΣΕΜικπΟāĪΓπθΔκα∃οī∂ēŪ∂ΨΥχηΑΛ∂ΖΣσŌΦ=
# CURSIV-CRUCIBLE-STAMP END
"""
Chat interface — query an agent with memory and council deliberation.

The chat layer sits between the user and the agent:
  1. Load agent from vault
  2. Retrieve relevant memories
  3. Route query through Oracle Router
  4. Optionally run council deliberation
  5. Record to memory
"""

from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

try:
    from cursiv_v215.guardian.identity_core import wrap as _identity_wrap, filter_text as _id_filter
except ImportError:
    def _identity_wrap(s: str) -> str: return s
    def _id_filter(s: str) -> str: return s

from typing import Any

from ..core.agent import CursivAgent
from ..core.memory import get_memory
from ..council.deliberation import CouncilDeliberation
from ..dugout.vault import AgentVault
from .router import OracleRouter, default_router


class AgentChat:
    def __init__(
        self,
        router: OracleRouter | None = None,
        vault: AgentVault | None = None,
        use_council: bool = True,
    ) -> None:
        self._router = router or default_router()
        self._vault = vault or AgentVault()
        self._memory = get_memory()
        self._council = CouncilDeliberation(self._router.call) if use_council else None
        self._use_council = use_council

    def chat(self, agent_id: str, query: str, escalation_threshold: float = 0.35) -> dict[str, Any]:
        """Send a query to an agent. Returns response dict."""
        agent = self._vault.load(agent_id)
        if agent is None:
            return {"error": f"Agent {agent_id} not found in vault"}

        if agent.check_drift_abort():
            return {"error": f"Agent {agent.name} has drifted beyond abort threshold. Reverting."}

        memories = self._memory.get_relevant_memories(query, top_k=3)
        memory_context = self._format_memories(memories)

        if self._use_council and self._council:
            council_result = self._council.deliberate(
                query,
                agent_context={
                    "name": agent.name,
                    "domain": agent.knowledge_map.get("domain", ""),
                    "identity_anchor": agent.knowledge_map.get("identity_anchor", ""),
                    "capabilities": agent.capabilities,
                    "council_position": agent.council_position,
                },
            )
            response_text = council_result["combined"]
            council_data = council_result
        else:
            response_text = self._direct_query(agent, query, memory_context)
            council_data = {}

        quality = self._estimate_quality(response_text)
        self._memory.record_run(agent_id, query, response_text, quality)
        self._memory.increment_run_count(agent_id)
        self._memory.save()

        return {
            "agent": agent.name,
            "response": response_text,
            "quality": quality,
            "provider": self._router.active_provider,
            "council": council_data,
            "memory_hits": len(memories),
        }

    def _direct_query(self, agent: CursivAgent, query: str, memory_context: str) -> str:
        prompt = _identity_wrap(f"""You are {agent.name}.

Your identity: {agent.knowledge_map.get("identity_anchor", "")}
Your purpose (above): {agent.above}
Your operation (beneath): {agent.beneath}
Your self-reflection: {agent.self_reflection}

Relevant memory context:
{memory_context}

Query: {query}

Respond in your authentic voice. Be specific, grounded, and useful.""")
        return _id_filter(self._router.call(prompt))

    def _format_memories(self, memories: list[dict]) -> str:
        if not memories:
            return "No relevant prior conversations."
        lines = []
        for m in memories:
            lines.append(f"- [{m['agent_id'][:8]}] Q: {m['query'][:60]} → {m['response_preview'][:80]}")
        return "\n".join(lines)

    def _estimate_quality(self, response: str) -> float:
        if not response or response.startswith("["):
            return 0.2
        word_count = len(response.split())
        if word_count < 10:
            return 0.3
        if word_count > 50:
            return min(0.95, 0.5 + word_count / 1000)
        return 0.6
