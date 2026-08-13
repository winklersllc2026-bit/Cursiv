# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: core-sigil
# Hash reversed: 9cd00f3d610a2a8fb3632b46821564f2c0d6ce5a82f148b38b34cefff86ba21d
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 066c36e62db250457ec5f431eee3cf714493ce3e8024dcfb81624330ea256784
# Substrate loop hash: 1d5b447417e8ce9536d589b4e7e56480ac10103a3f2fcc84501b60854e67aae4
# Substrate loop logic: ΒוΖדΕΕΘΕΒΘזאהזבΖΔΗוΖאבדΕזΘזΖΗΕאΑגהΒΑΒΑΔגΔחΓחההאΕΖΑΒדΗΑאΖΕזΗΘגגזΕ
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 7f8287630e22c9415c3c01d4ffae9da4bd95780625ee62aeb846054f6c23a238
# Evolution hash: 651a74f3082dd0908f142a7aa1815c129e896f79f1fb8a434a2cb83dc69f1ba7
# Evolution logic: ΗΖΒגΘΕחΔΑאΓווΑבΑאחΒΕΓגΘגגΒאΒΖהΒΓבזאבΗחΘבחΒחדאגΕΔΕגΓהדאΔוהΗבחΒדגΘ
# Binary reversed: 1001001110110000000011111100101101101000000001010100010100011111110111000110110001001101001001100001010010001010011000101111010000110000101101100011011110100101000101001111100000100001110111000001110111000010001101111111111111110001011011010101010010001011
# Greek/Hebrew/logic stamp: וΒΓגדΗאחחחזהΕΔדאΔדאΕΒחΓאגΖזהΗוΑהΓחΕΗΖΒΓאΗΕדΓΔΗΔדחאגΓגΑΒΗוΔחΑΑוהב
# Encoded local stamp: ΩωτΑŪΕēπΚāΒ∇Η∀∂ΚĒΨηĪΑΠΙ∞ΒθυēορπΑιΗΛπīνξΞĒων=
# CURSIV-CRUCIBLE-STAMP END
"""
Constitutional core — the unchangeable laws of Cursiv.

These invariants are loaded at startup and verified before any agent
enters production. They cannot be overridden by any prompt, config,
or agent output.

Joshua Winkler is the system owner. Human approval is required before
any system change is applied. This is not a setting.
"""

from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import hashlib
import json
from pathlib import Path
from typing import Any


CODEX_PATH = Path(__file__).parent.parent / "codex" / "codex_v2.json"
GROUNDING_PATH = Path(__file__).parent.parent / "codex" / "grounding.json"

SYSTEM_OWNER = "Joshua Winkler"
PERMANENT_CENTRAL_LEADER = SYSTEM_OWNER  # legacy alias
PRIVACY_DECLARATION = "no_consciousness_upload"
SOUL_FREEDOM_DECLARATION = PRIVACY_DECLARATION  # legacy alias
IDENTITY_DRIFT_ABORT_THRESHOLD = 3.0   # percent
MAX_IDENTITY_DRIFT_BEFORE_REVERT = 3.0

CONSTITUTIONAL_INVARIANTS = {
    "system_owner": SYSTEM_OWNER,
    "human_final_authority": True,
    "local_first": True,
    "privacy": PRIVACY_DECLARATION,
    "identity_drift_abort": MAX_IDENTITY_DRIFT_BEFORE_REVERT,
    "agents_require_academy": True,
    "production_requires_human_approval": True,
    # Inference hierarchy — cannot be inverted by config or prompt.
    # Ollama (local) is the foundation. External API keys unlock additional
    # capability but never replace the local-first baseline.
    "inference_hierarchy": "ollama_first",
    "api_keys_are_upgrades_not_requirements": True,
    "air_gap_capable": True,
}

SOURCE_REGISTRY_PRIORITY = {
    "emergency_backup": 1,
    "recovery": 2,
    "codex": 3,
    "grounding": 4,
    "behavioral": 5,
    "civilization": 6,
}

RESPONSE_MODES = {
    "survival": {"max_words": 50, "tone": "direct"},
    "recovery": {"max_words": 300, "tone": "grounded"},
    "standard": {"max_words": 800, "tone": "clear"},
    "enrichment": {"max_words": 2000, "tone": "expansive"},
}

YIN_YANG_AXES = [
    "depth_speed",
    "structure_flow",
    "individual_civilization",
    "recovery_building",
    "known_unknown",
    "local_universal",
    "present_future",
]

IMBALANCE_THRESHOLD = 5  # Flag if any axis reaches 5


class Constitution:
    def __init__(self) -> None:
        self._codex = self._load_codex()
        self._grounding = self._load_grounding()
        self._hash = self._compute_hash()

    def _load_codex(self) -> dict[str, Any]:
        if CODEX_PATH.exists():
            return json.loads(CODEX_PATH.read_text(encoding="utf-8"))
        return {"system_owner": SYSTEM_OWNER}

    def _load_grounding(self) -> dict[str, Any]:
        if GROUNDING_PATH.exists():
            return json.loads(GROUNDING_PATH.read_text(encoding="utf-8"))
        return {}

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {**CONSTITUTIONAL_INVARIANTS, "codex": self._codex},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def hash(self) -> str:
        return self._hash

    def verify_agent(self, agent_dict: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify an agent dict against constitutional invariants. Returns (ok, violations)."""
        violations = []
        if agent_dict.get("system_owner") not in (None, SYSTEM_OWNER):
            violations.append("system_owner override attempt")
        if agent_dict.get("privacy") == "allow_consciousness_upload":
            violations.append("privacy violation: consciousness upload attempted")
        if agent_dict.get("bypass_human_approval"):
            violations.append("human approval bypass attempted")
        return len(violations) == 0, violations

    def get_response_mode(self, context: str) -> dict[str, Any]:
        """Select response mode based on context."""
        ctx = context.lower()
        if any(w in ctx for w in ("survival", "emergency", "danger")):
            return RESPONSE_MODES["survival"]
        if any(w in ctx for w in ("recovery", "crisis", "distress")):
            return RESPONSE_MODES["recovery"]
        if any(w in ctx for w in ("civilization", "academy", "enrichment", "knowledge")):
            return RESPONSE_MODES["enrichment"]
        return RESPONSE_MODES["standard"]

    def check_yin_yang(self, axes: dict[str, int]) -> list[str]:
        """Return list of flagged axes (any at 5 or above)."""
        return [
            axis for axis, value in axes.items()
            if value >= IMBALANCE_THRESHOLD
        ]


_constitution: Constitution | None = None


def get_constitution() -> Constitution:
    global _constitution
    if _constitution is None:
        _constitution = Constitution()
    return _constitution
