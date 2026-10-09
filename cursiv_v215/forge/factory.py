"""
Agent Factory — create agents from JSON knowledge packets.

Flow:
  JSON packet → strand encode → CursivAgent(NASCENT) → Academy → CursivAgent(ALIVE)
  → Council registration → Dugout storage → Ready
"""

from __future__ import annotations

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
