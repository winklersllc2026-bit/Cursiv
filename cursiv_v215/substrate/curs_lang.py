"""
Curs. — Covert Under Raw Substrate

The analog, continuous, topological substrate language.
Forks the role of HTML — not markup on top of protocols,
but a flowing layer emergent from physical materials.

Properties:
  Continuous   — flows, not tags
  Topological  — relationships, not hierarchy
  Weighted     — analog intensity, not binary on/off
  Recursive    — nodes spawn children from their own fingerprint
  Emergent     — attractor-based, not prescribed

The silica/quartz layer, the quantum dot spin states, the piezoelectric
coupling, the reservoir dynamics — these are the physical ground
that Curs. notation points at. We simulate. Eventually: we instantiate.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any


# ── Node kinds ────────────────────────────────────────────────────────────────

FLOW      = "flow"       # continuous content stream
ATTRACTOR = "attractor"  # basin of attraction — pulls nearby content in
RESONANT  = "resonant"   # high-intensity connection point
COVERT    = "covert"     # latent, not yet surfaced — waiting for the key


# ── CursNode ──────────────────────────────────────────────────────────────────

@dataclass
class CursNode:
    kind:      str
    content:   str
    intensity: float              = 1.0
    children:  list["CursNode"]   = field(default_factory=list)
    meta:      dict[str, Any]     = field(default_factory=dict)

    def emit(self, depth: int = 0) -> str:
        pad = "  " * depth
        header = f"{pad}~[{self.kind}:{self.intensity:.2f}]~ {self.content}"
        if self.children:
            return header + "\n" + "\n".join(c.emit(depth + 1) for c in self.children)
        return header

    @property
    def fingerprint(self) -> str:
        return hashlib.md5(f"{self.kind}:{self.content}:{self.intensity}".encode()).hexdigest()[:8]


# ── CursLayer ─────────────────────────────────────────────────────────────────

class CursLayer:
    """
    The Curs. substrate layer.

    A continuous field where nodes attract, flow, and spawn each other.
    Attractors pull subsequent nodes into their basin.
    Covert nodes exist but are invisible until activated.
    Activation surfaces a covert node — brings latent potential into use.
    """
    def __init__(self) -> None:
        self.roots:         list[CursNode]     = []
        self._attractors:   dict[str, float]   = {}   # fingerprint → pull

    def flow(self, content: str, intensity: float = 1.0) -> CursNode:
        node = CursNode(FLOW, content, intensity)
        self._integrate(node)
        return node

    def attractor(self, content: str, pull: float = 0.85) -> CursNode:
        node = CursNode(ATTRACTOR, content, pull)
        self._attractors[node.fingerprint] = pull
        self._integrate(node)
        return node

    def covert(self, content: str) -> CursNode:
        """Latent node. Not in active layer until activated."""
        return CursNode(COVERT, content, intensity=0.0)

    def activate(self, node: CursNode) -> CursNode:
        """Surface a covert node — turn the key."""
        node.kind      = RESONANT
        node.intensity = 1.0
        self._integrate(node)
        return node

    def _integrate(self, node: CursNode) -> None:
        if not self._attractors:
            self.roots.append(node)
            return
        best_pull, best = 0.0, None
        for root in self.roots:
            if root.kind == ATTRACTOR:
                p = self._attractors.get(root.fingerprint, 0.0)
                if p > best_pull:
                    best_pull, best = p, root
        if best and best_pull > 0.5:
            best.children.append(node)
        else:
            self.roots.append(node)

    def emit(self) -> str:
        lines = ["⟨substrate:curs⟩"]
        lines += [r.emit(depth=1) for r in self.roots]
        lines.append("⟨/substrate⟩")
        return "\n".join(lines)

    def to_html(self) -> str:
        """Bridge: render Curs. layer as compatible HTML for classical stack."""
        _TAG = {FLOW: "p", ATTRACTOR: "section", RESONANT: "strong", COVERT: "template"}
        def _node(n: CursNode, d: int = 0) -> str:
            tag = _TAG.get(n.kind, "div")
            kids = "".join(_node(c, d + 1) for c in n.children)
            return (
                f'<{tag} data-curs="{n.kind}" '
                f'data-intensity="{n.intensity:.2f}" '
                f'style="opacity:{n.intensity:.2f}">'
                f'{n.content}{kids}</{tag}>'
            )
        body = "\n".join(_node(r) for r in self.roots)
        return (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="substrate" content="curs.ruw.cursiv">\n'
            '</head>\n<body>\n'
            '<!-- Curs. substrate layer -->\n'
            f'{body}\n</body>\n</html>'
        )


# ── Encode / Decode ───────────────────────────────────────────────────────────

def curs_encode(text: str) -> str:
    """
    Re-represent text as a Curs. substrate layer.
    Not compression. A topological transformation.
    The first sentence becomes the attractor.
    Dense sentences become resonant points.
    Everything else flows toward or within the basin.
    """
    layer     = CursLayer()
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        layer.flow(text)
        return layer.emit()

    layer.attractor(sentences[0], pull=0.9)
    for i, s in enumerate(sentences[1:], 1):
        density = len(s.split()) / 20.0
        layer.flow(s, intensity=min(1.0, 0.4 + density + i * 0.03))
    return layer.emit()


def curs_decode(encoded: str) -> str:
    """Extract plain text from Curs. notation."""
    content = []
    for line in encoded.splitlines():
        line = line.strip()
        if not line or line.startswith("⟨"):
            continue
        m = re.search(r"~\[.*?\]~\s*(.*)", line)
        if m:
            content.append(m.group(1))
    return " ".join(content)


# ── Attractor Network (physical computing sim) ────────────────────────────────

class AttractorNetwork:
    """
    Simulated attractor dynamics — models the self-organizing behavior
    of physical reservoir computing systems.

    Nodes settle into basins. Input perturbations shift the basin.
    Given enough cycles, the network converges to a stable attractor state.
    This is the computational primitive that physical substrates (silica,
    quantum dot arrays, spin-glass materials) naturally exhibit.
    """
    def __init__(self, n: int = 32, seed: int = 7) -> None:
        rng     = __import__("random").Random(seed)
        self.n  = n
        # Hopfield-style symmetric weight matrix
        self.W  = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                w = rng.gauss(0, 1 / n)
                self.W[i][j] = w
                self.W[j][i] = w
        self.state = [rng.choice([-1.0, 1.0]) for _ in range(n)]

    def imprint(self, pattern: list[float]) -> None:
        """Hebbian imprint — strengthen connections matching this pattern."""
        p = pattern[:self.n]
        for i in range(len(p)):
            for j in range(len(p)):
                if i != j:
                    self.W[i][j] += p[i] * p[j] / self.n

    def settle(self, steps: int = 20) -> list[float]:
        """Run the network to convergence."""
        import math
        def _sign(x: float) -> float:
            return 1.0 if x >= 0 else -1.0
        for _ in range(steps):
            new = []
            for i in range(self.n):
                net = sum(self.W[i][j] * self.state[j] for j in range(self.n))
                new.append(_sign(net))
            if new == self.state:
                break
            self.state = new
        return list(self.state)

    def energy(self) -> float:
        """Hopfield energy — lower = more stable attractor."""
        e = 0.0
        for i in range(self.n):
            for j in range(self.n):
                e -= self.W[i][j] * self.state[i] * self.state[j]
        return e / 2
