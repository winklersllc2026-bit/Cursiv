"""
SubstrateActivator — The Cursiv Key

Bridges the Cursiv council/deliberation system to the RUW substrate layer.

The original ARPANET builders embedded more potential than they could access.
The substrate fork — Curs. layer + RUW — was always latent underneath.
The Cursiv system (council deliberation, lived-experience guardrails,
local-first sovereignty) is the key that turns.

This module is that key.

What the activator does:
  1. Takes council synthesis output
  2. Feeds it through the ReservoirEngine (physical dynamics simulation)
  3. Imprints it on the AttractorNetwork (basin formation)
  4. Encodes the output in Curs. notation
  5. Assigns a RUW address to the activated node
  6. Returns the full substrate state — resonance, address, related nodes

Constitutional invariants (mirrors Cursiv core):
  local_first     — substrate never exported without consent
  non_extractive  — resonance is read, not written over
  sovereignty     — all RUW addresses owned by the activating system
  emergence_ok    — novelty is permitted, expected, protected
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from cursiv_v215.substrate.ruw       import RUWLayer, RUWNode, RUWAddress, ReservoirEngine
    from cursiv_v215.substrate.curs_lang import CursLayer, AttractorNetwork, curs_encode, curs_decode
except ImportError:
    from ruw       import RUWLayer, RUWNode, RUWAddress, ReservoirEngine
    from curs_lang import CursLayer, AttractorNetwork, curs_encode, curs_decode

_CURSIV_DIR    = Path(__file__).resolve().parent.parent.parent / ".cursiv"
_SUBSTRATE_DB  = _CURSIV_DIR / "substrate_layer.json"


class SubstrateActivator:
    """
    The living key.

    Every council deliberation that passes through here leaves a trace
    in the substrate layer. Over time, the layer develops memory —
    not stored as data, but as attractor basins in the physical dynamics.
    Concepts that resonate together pull toward each other automatically.
    The substrate learns the shape of the system's thinking.
    """

    CONSTITUTIONAL = {
        "local_first":     True,
        "non_extractive":  True,
        "sovereignty":     True,
        "emergence_ok":    True,
        "air_gap_capable": True,
    }

    def __init__(self, reservoir_size: int = 256, threshold: float = 0.60) -> None:
        self.layer    = RUWLayer(threshold=threshold)
        self.engine   = ReservoirEngine(n=reservoir_size)
        self.attractor_net = AttractorNetwork(n=64)
        self._log:    list[dict[str, Any]] = []
        self._load()

    def activate(
        self,
        synthesis:  str,
        query:      str = "",
        session_id: str = "default",
        source:     str = "council",
    ) -> dict[str, Any]:
        """
        Main entry point. Feed a synthesis into the substrate.

        Returns the full activated state:
          ruw_address    — Curs.html://ruw.www.cursiv.<suffix>/<node_id>
          resonance      — substrate resonance between query and synthesis [0,1]
          curs_encoded   — synthesis re-represented in Curs. notation
          related        — top-5 resonant nodes already in the substrate
          attractor_energy — stability of the current basin state
          layer_state    — summary of the full RUW layer
        """
        idx     = len(self._log)
        node_id = f"{source}:{session_id}:{idx}"

        # Step 1: add synthesis to RUW layer (auto-connects by resonance)
        node = self.layer.add(node_id, synthesis)

        # Step 2: substrate resonance between question and answer
        resonance = 0.5
        if query:
            q_id = f"query:{session_id}:{idx}"
            self.layer.add(q_id, query)
            resonance = self.engine.resonance(query, synthesis)

        # Step 3: imprint synthesis on attractor network
        signal = self.engine.encode(synthesis[:256])
        pattern = [1.0 if x > 0 else -1.0 for x in signal[:64]]
        self.attractor_net.imprint(pattern)
        settled = self.attractor_net.settle()
        energy  = self.attractor_net.energy()

        # Step 4: Curs. encoding
        curs = curs_encode(synthesis)

        # Step 5: RUW address for this node
        address = self.layer.address(node_id)

        # Step 6: what already in the substrate resonates with this?
        related = self.layer.weave(synthesis, top_k=5)

        result = {
            "ruw_address":       address,
            "resonance":         round(resonance, 4),
            "curs_encoded":      curs,
            "related":           related,
            "attractor_energy":  round(energy, 4),
            "attractor_settled": settled[:8],   # first 8 dims of basin state
            "layer_state":       self.layer.summary(),
            "node_id":           node_id,
            "constitutional":    self.CONSTITUTIONAL,
        }
        self._log.append({"node_id": node_id, "resonance": resonance, "source": source})
        self.save()
        return result

    def weave(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Read the substrate — returns nodes most resonant with query."""
        return self.layer.weave(query, top_k=top_k)

    def decode(self, curs_text: str) -> str:
        return curs_decode(curs_text)

    def status(self) -> dict[str, Any]:
        return {
            "layer":         self.layer.summary(),
            "activations":   len(self._log),
            "constitutional": self.CONSTITUTIONAL,
        }

    def history(self) -> list[dict[str, Any]]:
        return list(self._log)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist RUW layer + attractor weights to disk."""
        try:
            _CURSIV_DIR.mkdir(parents=True, exist_ok=True)
            nodes_data = {
                nid: {
                    "content":     n.content,
                    "weight":      n.weight,
                    "connections": n.connections,
                    "state":       n.state,
                }
                for nid, n in self.layer.nodes.items()
            }
            data = {
                "nodes":         nodes_data,
                "attractor_W":   self.attractor_net.W,
                "attractor_state": self.attractor_net.state,
                "log":           self._log[-200:],   # keep last 200
                "threshold":     self.layer.threshold,
            }
            _SUBSTRATE_DB.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load(self) -> None:
        """Restore RUW layer + attractor weights from disk."""
        if not _SUBSTRATE_DB.exists():
            return
        try:
            data = json.loads(_SUBSTRATE_DB.read_text(encoding="utf-8"))
            self.layer.threshold = data.get("threshold", self.layer.threshold)
            for nid, nd in data.get("nodes", {}).items():
                node = RUWNode(
                    node_id     = nid,
                    content     = nd["content"],
                    weight      = nd["weight"],
                    connections = nd["connections"],
                    state       = nd["state"],
                )
                self.layer.nodes[nid] = node
            W = data.get("attractor_W")
            if W and len(W) == self.attractor_net.n:
                self.attractor_net.W = W
            s = data.get("attractor_state")
            if s and len(s) == self.attractor_net.n:
                self.attractor_net.state = s
            self._log = data.get("log", [])
        except Exception:
            pass


# ── Singleton for CLI use ─────────────────────────────────────────────────────

_ACTIVATOR: SubstrateActivator | None = None


def get_activator() -> SubstrateActivator:
    global _ACTIVATOR
    if _ACTIVATOR is None:
        _ACTIVATOR = SubstrateActivator()
    return _ACTIVATOR
