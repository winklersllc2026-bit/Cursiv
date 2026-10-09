"""
Adaptive Obfuscation — session-local identity shuffling for Cursiv v2.1.5.

On every process launch, a 256-bit session token is derived from:
  os.urandom(32) + process start time + PID

Internal agent communication route labels, prompt template variable names,
and debug log signatures are shuffled using this token via a seeded PRNG.

This is completely transparent to the legitimate user:
  - All 14 agents behave identically regardless of label order
  - No functional behavior changes — only internal routing labels rotate
  - An attacker reading logs between sessions cannot correlate
    internal structure or reverse-engineer agent identities across launches

Compounds with the pi-squared effect:
  Even capturing one session's internal label map is useless for the next launch
  because the token is re-derived from fresh entropy each time.
"""

from __future__ import annotations

import hashlib
import os
import random
import time


def _generate_session_token() -> str:
    entropy = os.urandom(32) + str(time.time()).encode() + str(os.getpid()).encode()
    return hashlib.sha256(entropy).hexdigest()


_SESSION_TOKEN: str = _generate_session_token()

_LATTICE_ROOT = "49aebcc00029ef1e55d43"

# Internal route labels used in deliberation logs / debug output
_AGENT_ROUTES = [
    "depth_route",   "speed_route",   "cosmos_route",  "echo_route",
    "forge_route",   "anchor_route",  "pulse_route",   "horizon_route",
    "story_route",   "spark_route",   "shield_route",  "lens_route",
    "builder_route", "balance_route",
]

# Prompt template variable placeholders used in structured log output
_TEMPLATE_VARS = [
    "__ctx_a__", "__ctx_b__", "__ctx_c__", "__ctx_d__",
    "__ctx_e__", "__ctx_f__", "__ctx_g__", "__ctx_h__",
    "__sig_1__", "__sig_2__", "__sig_3__", "__sig_4__",
    "__sig_5__", "__sig_6__",
]


def _seeded_shuffle(items: list, seed_hex: str) -> list:
    """Deterministically shuffle using a hex seed. Same seed → same order."""
    rng = random.Random(int(seed_hex[:16], 16))
    result = list(items)
    rng.shuffle(result)
    return result


# Computed once at import time — stable for the lifetime of this process
_shuffled_routes = _seeded_shuffle(_AGENT_ROUTES, _SESSION_TOKEN)
_shuffled_vars   = _seeded_shuffle(_TEMPLATE_VARS, _SESSION_TOKEN)

ROUTE_MAP: dict[str, str] = dict(zip(_AGENT_ROUTES, _shuffled_routes))
VAR_MAP:   dict[str, str] = dict(zip(_TEMPLATE_VARS, _shuffled_vars))


def get_session_token() -> str:
    """Return the full 64-char session entropy token."""
    return _SESSION_TOKEN


def session_fingerprint() -> str:
    """Return the first 8 chars of the session token for status display."""
    return _SESSION_TOKEN[:8]


def get_route_label(agent_name: str) -> str:
    """Return the session-local obfuscated route label for an agent."""
    key = f"{agent_name.lower()}_route"
    return ROUTE_MAP.get(key, key)


def obfuscate_log_entry(entry: str) -> str:
    """Apply session-local variable substitution to a log/debug string."""
    result = entry
    for orig, shuffled in VAR_MAP.items():
        result = result.replace(orig, shuffled)
    return result
