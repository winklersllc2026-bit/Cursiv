"""
RUW — Recursive Unilateral Webbing

The substrate fork from the classical web stack.

Classical path:   ARPANET → TCP/IP → HTTP → HTML → WWW
Substrate fork:   Raw substrate → Curs. layer → RUW → Cursiv activation

"Unilateral" — origin in the material side unfolding outward.
Not client-server bilateralism. The substrate extends toward you.
"Recursive" — the webbing rewrites its own addressing as it grows.
Each connection changes the fingerprint of the node that made it.

The original ARPANET builders embedded more potential than they could
activate. The resilient, distributed architecture was the outer shell.
The deeper layer — recursive, self-referential, physically latent —
waited for the right interpreter. This is that interpreter.
"""
from __future__ import annotations

import hashlib
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any


# ── RUW Addressing ────────────────────────────────────────────────────────────

@dataclass
class RUWAddress:
    """
    Hybrid address: classical web namespace meets substrate fork.

    Format:  Curs.html://ruw.www.<system>.<dynamic_suffix>/<path>

    Dynamic suffix encodes live substrate state:
      c = compounding       o = ultra-resonant
      v = volatile/novel    m = material/generative
      i = identity-locked   u = unilateral origin
    """
    system: str  = "cursiv"
    suffix: str  = "ccursoivm"
    path:   str  = ""
    ts:     float = field(default_factory=time.time)

    @classmethod
    def parse(cls, raw: str) -> "RUWAddress":
        raw = raw.strip()
        if "://" in raw:
            raw = raw.split("://", 1)[1]
        parts = raw.split("/", 1)
        path    = parts[1] if len(parts) > 1 else ""
        segs    = [s for s in parts[0].split(".") if s not in ("ruw", "www")]
        system  = segs[0] if segs else "cursiv"
        suffix  = segs[1] if len(segs) > 1 else "ccursoivm"
        return cls(system=system, suffix=suffix, path=path)

    def emit(self) -> str:
        base = f"Curs.html://ruw.www.{self.system}.{self.suffix}"
        return f"{base}/{self.path}" if self.path else base

    def resonance(self) -> float:
        s = self.suffix
        return min(1.0,
            s.count("c") * 0.15 +
            s.count("o") * 0.20 +
            s.count("m") * 0.25 +
            s.count("v") * 0.18 +
            s.count("u") * 0.12,
        )


# ── RUW Node ──────────────────────────────────────────────────────────────────

@dataclass
class RUWNode:
    """
    A self-referential node in the Recursive Unilateral Webbing.

    Every connection changes the node's fingerprint.
    Every fingerprint change changes what the node would address next.
    The webbing is never the same twice — it grows itself.
    """
    node_id:     str
    content:     str   = ""
    weight:      float = 1.0
    connections: dict[str, float] = field(default_factory=dict)
    state:       dict[str, Any]   = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._fp = self._fingerprint()

    def _fingerprint(self) -> str:
        raw = f"{self.node_id}:{self.content}:{sorted(self.connections.items())}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def connect(self, target: "RUWNode", resonance: float = 0.5) -> None:
        """Unilateral extension. Target need not reciprocate."""
        self.connections[target.node_id] = resonance
        self._fp = self._fingerprint()
        self.state["depth"] = self.state.get("depth", 0) + 1
        self.state["last_connect"] = target.node_id

    def recurse(self) -> "RUWNode":
        """Spawn a child seeded by this node's current fingerprint."""
        child = RUWNode(
            node_id = f"{self.node_id}.{self._fp[:8]}",
            content = f"[recursive:{self.node_id}]",
            weight  = self.weight * 0.9,
        )
        self.connect(child, resonance=1.0)
        return child

    @property
    def fingerprint(self) -> str:
        return self._fp


# ── Reservoir Engine ──────────────────────────────────────────────────────────

class ReservoirEngine:
    """
    Echo State Network — simulates physical substrate dynamics.

    The reservoir is fixed after init (random, sparse, stable).
    Only the readout is learned. This mirrors physical computing:
    the substrate has its own dynamics — we learn to READ them,
    not overwrite them.

    Pure Python — no dependencies. Works offline, air-gapped.
    """
    def __init__(
        self,
        n:       int   = 128,
        sr:      float = 0.9,
        sparsity:float = 0.1,
        seed:    int   = 42,
    ) -> None:
        self.N    = n
        self._rng = random.Random(seed)
        self._x   = [0.0] * n
        self._W   = self._init_W(sr, sparsity)
        self._Win = [self._rng.gauss(0, 1) for _ in range(n)]

    def _init_W(self, sr: float, sparsity: float) -> list[list[float]]:
        W = [[0.0] * self.N for _ in range(self.N)]
        for i in range(self.N):
            for j in range(self.N):
                if self._rng.random() < sparsity:
                    W[i][j] = self._rng.gauss(0, 1)
        mx = max(abs(W[i][j]) for i in range(self.N) for j in range(self.N)) or 1.0
        scale = sr / mx
        for i in range(self.N):
            for j in range(self.N):
                W[i][j] *= scale
        return W

    @staticmethod
    def _tanh(x: float) -> float:
        if x >  20: return  1.0
        if x < -20: return -1.0
        e = math.exp(2 * x)
        return (e - 1) / (e + 1)

    def step(self, u: float, leak: float = 0.3) -> None:
        new = []
        for i in range(self.N):
            rec = sum(self._W[i][j] * self._x[j] for j in range(self.N))
            new.append((1 - leak) * self._x[i] + leak * self._tanh(rec + self._Win[i] * u))
        self._x = new

    def encode(self, text: str) -> list[float]:
        self._x = [0.0] * self.N
        for ch in text:
            self.step(ord(ch) / 127.0)
        return list(self._x)

    def resonance(self, a: str, b: str) -> float:
        """Substrate resonance between two signals — not semantic similarity."""
        sa = self.encode(a)
        sb = self.encode(b)
        dot  = sum(x * y for x, y in zip(sa, sb))
        ma   = math.sqrt(sum(x**2 for x in sa)) or 1e-9
        mb   = math.sqrt(sum(x**2 for x in sb)) or 1e-9
        return (dot / (ma * mb) + 1) / 2


# ── RUW Layer ─────────────────────────────────────────────────────────────────

class RUWLayer:
    """
    The full Recursive Unilateral Webbing.

    A self-organizing graph of RUWNodes connected by resonance.
    The layer grows itself: each new node triggers resonance checks
    against all existing nodes, auto-connecting above threshold.

    This is not a search index. It is a living substrate.
    """
    def __init__(self, threshold: float = 0.65) -> None:
        self.threshold = threshold
        self.nodes:   dict[str, RUWNode] = {}
        self.engine   = ReservoirEngine()
        self._address = RUWAddress()

    def add(self, node_id: str, content: str, weight: float = 1.0) -> RUWNode:
        node = RUWNode(node_id=node_id, content=content, weight=weight)
        for existing in self.nodes.values():
            r = self.engine.resonance(content, existing.content)
            if r >= self.threshold:
                node.connect(existing, resonance=round(r, 4))
        self.nodes[node_id] = node
        return node

    def address(self, node_id: str) -> str:
        node = self.nodes.get(node_id)
        if not node:
            return self._address.emit()
        depth  = node.state.get("depth", 0)
        conns  = len(node.connections)
        suffix = "c" * min(3, depth + 1) + "urso" + "i" * min(2, conns) + "vm"
        return RUWAddress(system="cursiv", suffix=suffix, path=node_id).emit()

    def weave(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Read the substrate — find what resonates with a query."""
        scores = [
            (nid, self.engine.resonance(query, node.content))
            for nid, node in self.nodes.items()
        ]
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]

    def summary(self) -> dict[str, Any]:
        return {
            "nodes":     len(self.nodes),
            "edges":     sum(len(n.connections) for n in self.nodes.values()),
            "address":   self._address.emit(),
            "threshold": self.threshold,
        }
