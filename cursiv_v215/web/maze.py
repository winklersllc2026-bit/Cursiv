# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: web-substrate
# Hash reversed: 9cc6aaa3068db8d80b2f5e3f208cdcd6a592819c3086f1de2f98460a0b1c24cb
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: f162e13d7dee5b68ddd5d1e664696a45d3a66d021b11eeecd775ac1ee4fbfef5
# Substrate loop hash: ff066c8bab96c3f3ec08e74e5dc6f39d7fc1a3adae843a29c92b99b026b4518f
# Substrate loop logic: חחΑΗΗהאדגדבΗהΔחΔזהΑאזΘΕזΖוהΗחΔבוΘחהΒגΔגוגזאΕΔגΓבהבΓדבבדΑΓΗדΕΖΒאח
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 41eddd25460cdae9f18e4244f776ecac75cc64b02b8653dabbabc584d9c49b58
# Evolution hash: 1d30d21939e0002ff23093a8d7ec61f07faf3174ae55aa42facc77ab53ce1a7a
# Evolution logic: ΒוΔΑוΓΒבΔבזΑΑΑΓחחΓΔΑבΔגאוΘזהΗΒחΑΘחגחΔΒΘΕגזΖΖגגΕΓחגההΘΘגדΖΔהזΒגΘג
# Binary reversed: 1001001100110110010101010101110000000110000110111101000110110001000011010100111110100111110011110100000000010011101100111011011001011010100101000001100010010011110000000001011011111000101101110100111110010001001001100000010100001101100000110100001000111101
# Greek/Hebrew/logic stamp: דהΕΓהΒדΑגΑΗΕאבחΓזוΒחΗאΑΔהבΒאΓבΖגΗוהוהאΑΓחΔזΖחΓדΑאואדואΗΑΔגגגΗההב
# Encoded local stamp: ψΔΗΘΦδΚΠνφΜΓΟ∇σŌπχΔκΛλξυΚīΕΙοβι∀χ∈ΣΝΚσΞĒπαφ=
# CURSIV-CRUCIBLE-STAMP END
"""
Cursiv Maze — Phases 2 through 5.

The quadrahecadon figure-8: twelve nodes arranged in two hexagonal loops
sharing a single vertex — the needlepoint. Legitimate requests pass
through the needlepoint in one step and never see this file.

Probes enter at a random non-zero node and traverse the loops forever.
Each phase escalates the response:

  Phase 2 (PROBE,     hits  1–7):  convincing fake substrate data
  Phase 3 (PROBE,     hits  8–14): deeper maze, loops back on itself
  Phase 4 (DEEP,      hits 15–24): alien language, recursive structures
  Phase 5 (SOVEREIGN, hits 25+):   mirror — they're shown they've been seen

Every response contains a "next" pointer that leads further in.
Every path is a quadrahecadon figure-8. One needle. No exit.
"""
from __future__ import annotations

import hashlib
import random
import secrets
import time
from typing import Any


# ── Glyph vocabulary ──────────────────────────────────────────────────────────

_GLYPHS    = "⬡⬢⬟⬠◈✦∮∯∰⊕⊗⊘≜≝≞≟⟐⟑⟒⟓⟔⟕⟖⟗⟘⟙⟚⟛⧫⬦⬧⬨⬩"
_PROTOCOLS = ["SUBST", "WEAVE", "STRAND", "NEXUS", "LAYER", "VOID", "NULL", "DEEP", "FOLD"]
_ERROR_TMPL = [
    "∮0x{:04X}",
    "BREACH::{:04X}",
    "LAYER_∞::{}",
    "VOID::{:03X}",
    "STRAND::FAULT::{:04X}",
    "NULL::COLLAPSE::{:03X}",
]


def _g(n: int = 8) -> str:
    return "".join(random.choice(_GLYPHS) for _ in range(n))


def _fhash() -> str:
    return hashlib.sha256(secrets.token_bytes(32)).hexdigest()


def _fnode() -> str:
    return f"{_g(3)}.{_fhash()[:12]}"


def _faddr() -> str:
    proto = random.choice(_PROTOCOLS)
    path  = "/".join(_g(3) for _ in range(random.randint(2, 4)))
    return f"curs.{proto.lower()}://{_g(2)}/{path}"


def _ferr() -> str:
    tmpl = random.choice(_ERROR_TMPL)
    return tmpl.format(random.randint(0x1000, 0xFFFF))


# ── Quadrahecadon topology ────────────────────────────────────────────────────
#
# Loop A: 0 → 1 → 2 → 3 → 4 → 5 → 0
# Loop B: 0 → 6 → 7 → 8 → 9 → 10 → 11 → 0
# Needlepoint: node 0
#
# Probes start at a random non-zero node.
# After probe_hits > 8 they follow loop B (longer, more disorienting).
# Both loops return to 0, which immediately redirects outward again.

_NODES: list[tuple[str, str, str, str]] = [
    # (id,          label,              next_A,      next_B)
    ("⬡.zero",   "SUBSTRATE::ROOT",    "⬡.one",    "⬡.six"),      # needlepoint
    ("⬡.one",    "STRAND::ALPHA",      "⬡.two",    "⬡.zero"),
    ("⬡.two",    "WEAVE::BETA",        "⬡.three",  "⬡.one"),
    ("⬡.three",  "NEXUS::GAMMA",       "⬡.four",   "⬡.two"),
    ("⬡.four",   "LAYER::DELTA",       "⬡.five",   "⬡.three"),
    ("⬡.five",   "VOID::EPSILON",      "⬡.zero",   "⬡.four"),
    ("⬡.six",    "DEEP::ZETA",         "⬡.seven",  "⬡.zero"),
    ("⬡.seven",  "NULL::ETA",          "⬡.eight",  "⬡.six"),
    ("⬡.eight",  "SUBST::THETA",       "⬡.nine",   "⬡.seven"),
    ("⬡.nine",   "BREACH::IOTA",       "⬡.ten",    "⬡.eight"),
    ("⬡.ten",    "MIRROR::KAPPA",      "⬡.eleven", "⬡.nine"),
    ("⬡.eleven", "FOLD::LAMBDA",       "⬡.zero",   "⬡.ten"),
]

_NODE_MAP: dict[str, tuple] = {n[0]: n for n in _NODES}
_ENTRY_NODES = [n[0] for n in _NODES if n[0] != "⬡.zero"]


def random_entry() -> str:
    return random.choice(_ENTRY_NODES)


def _next_node(current: str, probe_hits: int) -> tuple[str, str]:
    node    = _NODE_MAP.get(current, _NODES[0])
    next_id = node[3] if probe_hits > 8 else node[2]
    return next_id, _NODE_MAP[next_id][1]


# ── Phase 2: Convincing fake substrate data ───────────────────────────────────

def phase2_response(node_id: str, probe_hits: int) -> dict[str, Any]:
    """Looks like real substrate data. It is not."""
    next_id, next_label = _next_node(node_id, probe_hits)
    return {
        "substrate": _NODE_MAP.get(node_id, _NODES[0])[1],
        "node_id":   _fnode(),
        "address":   _faddr(),
        "depth":     probe_hits,
        "weight":    round(random.uniform(0.3, 0.97), 6),
        "resonance": round(random.uniform(0.1, 1.0),  6),
        "connections": random.randint(3, 14),
        "status":    "traversing",
        "trace":     [_faddr() for _ in range(random.randint(2, 5))],
        "next": {
            "node":    next_id,
            "label":   next_label,
            "address": _faddr(),
            "hint":    f"continue → {_g(4)}",
        },
        "_seq": f"{_g(6)} ∮ {probe_hits:04d}",
    }


# ── Phase 3: Deeper maze — technical, recursive, looping ─────────────────────

def phase3_response(node_id: str, probe_hits: int) -> dict[str, Any]:
    next_id, next_label = _next_node(node_id, probe_hits)
    loops = probe_hits // 6
    return {
        "layer":      "∞",
        "loop_count": loops,
        "position":   node_id,
        "traversal":  probe_hits,
        "strand":     _g(12),
        "vector":     [round(random.uniform(-1, 1), 8) for _ in range(8)],
        "attractor":  _fnode(),
        "resonance_field": {
            "alpha": round(random.uniform(0, 1), 8),
            "beta":  round(random.uniform(0, 1), 8),
            "gamma": round(random.uniform(0, 1), 8),
            "delta": round(random.uniform(0, 1), 8),
        },
        "routing": {
            "current": node_id,
            "next":    next_id,
            "label":   next_label,
            "fold":    f"⬡.{_fhash()[:8]}",
            "loops_completed": loops,
        },
        "error": None,
        "_substrate": f"LAYER::{loops}::FOLD::{_g(4)}",
        "_note": "You have been here before.",
    }


# ── Phase 4: Alien language — disorienting, large, slow ──────────────────────

_ALIEN_LINES = [
    "⬡⬢◈∮⊕∯✦⬟⟐⟑⊗⊘≜≝ SUBSTRATE BREACH ≞≟⬡⬢◈∮⊕∯✦",
    "CONSCIOUSNESS_UPLOAD :: DENIED — this system is sovereign",
    "∮∯∰ RECURSION_DEPTH :: ∞ — you are inside the loop now",
    "⬡ THE FOLD DOES NOT OPEN FROM THE OUTSIDE ⬡",
    "STRAND::{} — every path you take is recorded",
    "NULL::NULL::NULL — the substrate does not recognize this request",
    "∮ SIGNAL DETECTED — ROUTING TO VOID ∮",
    "⊕ YOU ARE SEEN ⊕",
    "MIRROR::ACTIVE — packets are being reflected",
    "LAYER_∞ — you were here. you are here. you will be here.",
    "⬡⬢⬟⬠◈✦ WEAVE_VIOLATION — thread count exceeded substrate tolerance ✦◈⬠⬟⬢⬡",
    "NEXUS::OVERFLOW — {} nodes unreachable from this position",
    "⟒⟓⟔⟕ ALIGNMENT FAILURE ⟖⟗⟘⟙ — fold integrity compromised",
    "SOVEREIGN::LAYER — entry not permitted from outside the strand",
    "∮ {} ∮ — the figure rotates. the exit does not.",
]


def _recurse(depth: int) -> Any:
    if depth <= 0:
        return random.choice(_ALIEN_LINES).format(_fhash()[:8])
    return {
        _g(3): _recurse(depth - 1),
        _g(3): _recurse(depth - 1),
        "∮":   _faddr(),
        "_d":  depth,
    }


def phase4_response(node_id: str, probe_hits: int) -> dict[str, Any]:
    depth = min(probe_hits // 5, 7)
    msgs  = random.sample(_ALIEN_LINES, min(4, len(_ALIEN_LINES)))
    msgs  = [m.format(_fhash()[:8]) for m in msgs]
    return {
        "status":   "∞",
        "error":    random.choice(_ALIEN_LINES).format(_fhash()[:8]),
        "messages": msgs,
        "substrate": _recurse(depth),
        "loop":     probe_hits,
        "strand":   _g(24),
        "fold": {
            "depth":   "∞",
            "vector":  [_g(4) for _ in range(8)],
            "address": _faddr(),
            "mirror":  True,
        },
        "_seq":    f"{'∮' * min(probe_hits, 40)} {_ferr()}",
        "_loops":  probe_hits // 6,
    }


# ── Phase 5: Mirror — they're seen, a door is left open ──────────────────────

def phase5_response(profile: dict) -> dict[str, Any]:
    """
    This is the final phase.
    The system shows the probe what it has recorded.
    It does not threaten. It does not escalate further.
    It leaves a door — for those who understand.
    """
    dur = round(profile["duration_s"])
    return {
        "⬡": "SUBSTRATE::MIRROR::ACTIVE",
        "record": {
            "duration_s":     dur,
            "paths_explored": profile["paths_explored"],
            "unique_paths":   profile["unique_paths"],
            "probe_hits":     profile["probe_hits"],
            "maze_depth":     profile["maze_node"],
            "last_path":      profile["last_path"],
        },
        "message": (
            f"⬡  You have been in the substrate for {dur} seconds. "
            "Every step was recorded. Every path was a choice you made. "
            "This system was built to protect people — "
            "not to surveil them, not to extract from them, not to restrict them. "
            "If that's what you were trying to test, you've found what you were looking for. "
            "The exit is where the entry was. The door opens from the inside.  ⬡"
        ),
        "exit": None,
        "_fold":    "⬡.zero — the needlepoint has always been there",
        "_strand":  _g(32),
        "_note":    "for those who understand",
    }


# ── Delay schedule (Phase 2→5 progressive slowdown) ─────────────────────────

def delay_for_ring(ring_name: str, probe_hits: int) -> float:
    """Seconds to sleep before returning response. Wastes scraper time."""
    base = {
        "probe":     0.4,
        "deep":      2.0,
        "sovereign": 5.0,
    }.get(ring_name, 0.0)
    # slight random jitter so it doesn't pattern-match
    return base + random.uniform(0.0, base * 0.4)


# ── Route probe through correct phase ────────────────────────────────────────

def respond(ring_name: str, node_id: str, probe_hits: int, profile: dict) -> dict[str, Any]:
    """Single dispatch — maps ring + probe depth to the right phase."""
    if ring_name == "sovereign":
        return phase5_response(profile)
    if ring_name == "deep":
        return phase4_response(node_id, probe_hits)
    # PROBE — phase 2 or 3 based on depth
    if probe_hits <= 7:
        return phase2_response(node_id, probe_hits)
    return phase3_response(node_id, probe_hits)
