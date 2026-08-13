# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: 0ac79f49102ee8945bc5dbd0429b6568e5cbd683f54b9daea19109683705a2e5
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 4c7a85b7f825e874fa5ceee33be8c52c1993cbc9219158821d615d37b68367bc
# Substrate loop hash: 56b477bba46cd6c4fdb6588b705f56e58693221ef0f3b4f7ab4f13743cce0c62
# Substrate loop logic: ΖΗדΕΘΘדדגΕΗהוΗהΕחודΗΖאאדΘΑΖחΖΗזΖאΗבΔΓΓΒזחΑחΔדΕחΘגדΕחΒΔΘΕΔההזΑהΗΓ
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 31e3641b9d64faa4949760117e62e8da1d79098bc999972bab3cfb81bc3a3416
# Evolution hash: bd3bc384b197830710a993fe40b2107733da7bda173d88c5ec89edbc04a01332
# Evolution logic: דוΔדהΔאΕדΒבΘאΔΑΘΒΑגבבΔחזΕΑדΓΒΑΘΘΔΔוגΘדוגΒΘΔואאהΖזהאבזודהΑΕגΑΒΔΔΓ
# Binary reversed: 0000010100111110100111110010100110000000010001110111000110010010101011010011101010111101101100000010010010011101011010100110000101111010001111011011011000011100111110100010110110011011010101110101100010011000000010010110000111001110000010100101010001111010
# Greek/Hebrew/logic stamp: ΖזΓגΖΑΘΔאΗבΑΒבΒגזגובדΕΖחΔאΗודהΖזאΗΖΗדבΓΕΑודוΖהדΖΕבאזזΓΑΒבΕחבΘהגΑ
# Encoded local stamp: θΑΣΡΜΙσĀΒĒΩēηυΓŪφĀε∞ΣΝΨΨηιΗτρΛΦāεΜΥγōūξκγΛΝ=
# CURSIV-CRUCIBLE-STAMP END
"""
Agent Factory — create agents from JSON knowledge packets.

Flow:
  JSON packet → strand encode → CursivAgent(NASCENT) → Academy → CursivAgent(ALIVE)
  → Council registration → Dugout storage → Ready
"""

from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import json
from pathlib import Path
from typing import Any, Callable

from ..academy.engine import AcademyEngine
from ..academy.scorer import format_scorecard, score_agent
from ..core.agent import AgentState, CursivAgent
from ..core.strand import encode, strand_summary
from ..dugout.vault import AgentVault
from .router import OracleRouter, default_router


class AgentFactory:
    def __init__(
        self,
        router: OracleRouter | None = None,
        vault: AgentVault | None = None,
    ) -> None:
        self._router = router or default_router()
        self._vault = vault or AgentVault()
        self._academy = AcademyEngine(self._router.call)

    def create_from_packet(
        self,
        packet_path: str | Path,
        on_phase: Callable[[str, int], None] | None = None,
    ) -> CursivAgent:
        """Create a fully evolved agent from a JSON knowledge packet."""
        packet = self._load_packet(Path(packet_path))
        agent = self._birth_agent(packet, str(packet_path))
        agent = self._academy.run(agent, on_phase=on_phase)
        self._vault.store(agent)
        return agent

    def create_from_dict(
        self,
        knowledge: dict[str, Any],
        name: str,
        on_phase: Callable[[str, int], None] | None = None,
    ) -> CursivAgent:
        """Create a fully evolved agent from an inline dict."""
        strand = encode(knowledge)
        agent = CursivAgent(
            name=name,
            strand=strand,
            binary_strand=strand.encode(),
            origin="inline",
        )
        agent = self._academy.run(agent, on_phase=on_phase)
        self._vault.store(agent)
        return agent

    def _load_packet(self, path: Path) -> dict[str, Any]:
        text = path.read_text(encoding="utf-8-sig")  # utf-8-sig strips BOM if present
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON packet at {path}: {e}") from e

    def _birth_agent(self, packet: dict[str, Any], origin: str) -> CursivAgent:
        name = packet.get("name") or packet.get("agent_name") or Path(origin).stem
        strand = encode(packet)
        return CursivAgent(
            name=name,
            strand=strand,
            binary_strand=strand.encode(),
            origin=origin,
            lineage=[origin],
        )

    def quick_create(self, knowledge: dict[str, Any], name: str) -> CursivAgent:
        """Fast creation — 4 phases only (energy, grounding, route, structure). No Academy seal."""
        strand = encode(knowledge)
        agent = CursivAgent(name=name, strand=strand, binary_strand=strand.encode(), origin="quick")
        agent.above = f"{name} — created via quick path"
        agent.beneath = f"Serves {name} functions"
        agent.capabilities = list(knowledge.keys())[:5]
        agent.state = AgentState.ALIVE
        self._vault.store(agent)
        return agent


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Create a Cursiv agent from a JSON packet")
    parser.add_argument("--packet", required=True, help="Path to JSON knowledge packet")
    parser.add_argument("--quick", action="store_true", help="Quick mode (skip full Academy)")
    args = parser.parse_args()

    router = OracleRouter()
    vault = AgentVault()
    factory = AgentFactory(router=router, vault=vault)

    def progress(phase: str, num: int) -> None:
        print(f"  Phase {num}/8: {phase}... [provider: {router.active_provider}]")

    print(f"\nForging agent from: {args.packet}")
    print("=" * 50)

    if args.quick:
        import json as _json
        knowledge = _json.loads(Path(args.packet).read_text(encoding="utf-8"))
        agent = factory.quick_create(knowledge, Path(args.packet).stem)
        print(f"Quick-created: {agent.name} [{agent.state.value}]")
    else:
        agent = factory.create_from_packet(args.packet, on_phase=progress)
        scores = score_agent(agent)
        print(f"\nAgent born: {agent.name}")
        print(f"State: {agent.state.value}")
        print(f"Council position: {agent.council_position}")
        print(f"Sovereign seal: {agent.sovereign_seal[:16]}...")
        print()
        print(format_scorecard(scores))

    print(f"\nStored in vault. ID: {agent.id}")


if __name__ == "__main__":
    main()
