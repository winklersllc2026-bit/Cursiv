# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: c8cd70a7b1ecf277cdc4cceaf03f5c4f6538370a4042e207d0d11fc0ae1aac44
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: eec925f194b38bc48dbe6d296e9be959ddebc99140bc9240e6605fa0cce8e664
# Substrate loop hash: 4e6bc0bcd43f49f044aacd2229b77cee1a8167f657738665c164553af364ec66
# Substrate loop logic: ΕזΗדהΑדהוΕΔחΕבחΑΕΕגגהוΓΓΓבדΘΘהזזΒגאΒΗΘחΗΖΘΘΔאΗΗΖהΒΗΕΖΖΔגחΔΗΕזהΗΗ
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 1e381c236752857b31724671b1984c64bfee9c992c38f4075bd5ba35914570c0
# Evolution hash: cf2aee1be1fdf84e8c95595afa8891303e38a0f21045a6150885f8dd703ff058
# Evolution logic: החΓגזזΒדזΒחוחאΕזאהבΖΖבΖגחגאאבΒΔΑΔזΔאגΑחΓΒΑΕΖגΗΒΖΑאאΖחאווΘΑΔחחΑΖא
# Binary reversed: 0011000100111011111000000101111011011000011100111111010011101110001110110011001000110011011101011111000011001111101000110010111101101010110000011100111000000101001000000010010001110100000011101011000010111000100011110011000001010111100001010101001100100010
# Greek/Hebrew/logic stamp: ΕΕהגגΒזגΑהחΒΒוΑוΘΑΓזΓΕΑΕגΑΘΔאΔΖΗחΕהΖחΔΑחגזההΕהוהΘΘΓחהזΒדΘגΑΘוהאה
# Encoded local stamp: ē∈ēΙ∂αūχμΦλΓεūΨωχηαΛτŪΛξΞφθΤσ∇Τυ∂ĒπψωρΜβχχΦ=
# CURSIV-CRUCIBLE-STAMP END
"""
Codex Agent — Winkler Personal Coding Specialist

Wraps the Winkler_Codex_AI system as a first-class Cursiv agent.
Handles all code generation and interpretation tasks.
Fully offline-capable (Phi-4 + LoRA deliberation protocol, no cloud API).

Discovery order:
  1. CURSIV_CODEX_PATH env var (absolute path to Winkler_Codex_AI root)
  2. Sibling directory: ../Winkler_Codex_AI relative to the Cursiv-v3 root
"""
from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import os
import sys
from pathlib import Path
from typing import Any, Optional

_CURSIV_ROOT = Path(__file__).resolve().parent.parent.parent

_CODEX_ROOT: Optional[Path] = None
for _candidate in [
    Path(os.environ["CURSIV_CODEX_PATH"]) if os.environ.get("CURSIV_CODEX_PATH") else None,
    _CURSIV_ROOT.parent / "Winkler_Codex_AI",
]:
    if _candidate and (_candidate / "Codex-Tool" / "cursiv_bridge" / "codex_tool_bridge.py").exists():
        _CODEX_ROOT = _candidate
        break

_AVAILABLE = False
_tool: Any = None

if _CODEX_ROOT:
    _bridge_path = str(_CODEX_ROOT / "Codex-Tool" / "cursiv_bridge")
    _codex_tool_path = str(_CODEX_ROOT / "Codex-Tool")
    for _p in [_bridge_path, _codex_tool_path]:
        if _p not in sys.path:
            sys.path.insert(0, _p)
    try:
        from codex_tool_bridge import CodexCodingTool  # type: ignore
        _tool = CodexCodingTool()
        _AVAILABLE = True
    except Exception:
        pass


def is_available() -> bool:
    """True if the Codex AI was discovered and loaded successfully."""
    return _AVAILABLE


def generate(prompt: str) -> str:
    """
    Generate code using the Winkler Codex deliberation protocol.

    Always returns output in two-section contract format:
      1. READY-TO-RUN CODE
      2. JSON FILES
    """
    if not _AVAILABLE or _tool is None:
        hint = (
            f"Set CURSIV_CODEX_PATH env var to the Winkler_Codex_AI root."
            if not _CODEX_ROOT else
            f"Codex found at {_CODEX_ROOT} but failed to load."
        )
        return f"[Codex Agent unavailable — {hint}]"
    try:
        return _tool.generate(prompt)
    except Exception as e:
        return f"[Codex Agent error: {e}]"


def codex_path() -> str:
    return str(_CODEX_ROOT) if _CODEX_ROOT else "not found"


def status() -> dict[str, Any]:
    base: dict[str, Any] = {"available": _AVAILABLE, "path": codex_path()}
    if not _AVAILABLE:
        return base
    try:
        return {**base, **_tool.status()}
    except Exception as e:
        return {**base, "error": str(e)}
