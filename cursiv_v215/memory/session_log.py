# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: 7ced67b4938c17db7e196cb5161a394c98d97ba050cf76420ced794075f32b7f
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 5a1c3344cf2595fb0a27e3239ff4ac03b5cf04b65453ae1cbdc4f35853a5986a
# Substrate loop hash: 27b21a7750997fe84905652caa7453fc0c8c943757b83e7836751ff26670a16d
# Substrate loop logic: ΓΘדΓΒגΘΘΖΑבבΘחזאΕבΑΖΗΖΓהגגΘΕΖΔחהΑהאהבΕΔΘΖΘדאΔזΘאΔΗΘΖΒחחΓΗΗΘΑגΒΗו
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 83ac0483967fbcedf017ba44528ca7c5697208a4ed73c0f264db1997bb2c6c8b
# Evolution hash: a0f355bb53b16f422a3eca1f1e39a3d7858a6dd584e1fd2660a55b756b1ef962
# Evolution logic: גΑחΔΖΖדדΖΔדΒΗחΕΓΓגΔזהגΒחΒזΔבגΔוΘאΖאגΗווΖאΕזΒחוΓΗΗΑגΖΖדΘΖΗדΒזחבΗΓ
# Binary reversed: 1110001101111011011011101101001010011100000100111000111010111101111001111000100101100011110110101000011010000101110010010010001110010001101110011110110101010000101000000011111111100110001001000000001101111011111010010010000011101010111111000100110111101111
# Greek/Hebrew/logic stamp: חΘדΓΔחΖΘΑΕבΘוזהΑΓΕΗΘחהΑΖΑגדΘבואבהΕבΔגΒΗΒΖדהΗבΒזΘדוΘΒהאΔבΕדΘΗוזהΘ
# Encoded local stamp: ΣΥΝχμφŌΦγ∂ŌξοŌαμĒΟδψρψΒ∀ΛθδΞΛμυ∇λΔΩŪēΚ∀ζθφι=
# CURSIV-CRUCIBLE-STAMP END
"""
Session Logger — Cursiv v2.1.5

Persists every conversation exchange to .cursiv/sessions/YYYY-MM-DD.jsonl.
On restart the system loads the last session's context into the system prompt
and greets the user with a summary of what was happening.

Files:
  .cursiv/sessions/YYYY-MM-DD.jsonl  — one file per day, one JSON line per exchange
"""
from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import json
import time
from datetime import datetime, date
from pathlib import Path

ROOT         = Path(__file__).parent.parent.parent
CURSIV_DIR   = ROOT / ".cursiv"
SESSIONS_DIR = CURSIV_DIR / "sessions"
MEMORY_FILE  = CURSIV_DIR / "memory.json"
RATED_JSONL  = CURSIV_DIR / "rated_exchanges.jsonl"


def _append_memory_run(user_msg: str, ai_msg: str, model: str, quality: float = 0.70) -> None:
    """Write this exchange to memory.json["runs"] so the training watcher picks it up."""
    CURSIV_DIR.mkdir(parents=True, exist_ok=True)
    try:
        mem = json.loads(MEMORY_FILE.read_text(encoding="utf-8")) if MEMORY_FILE.exists() else {}
    except Exception:
        mem = {}
    runs = mem.get("runs", [])
    runs.append({
        "agent_id":         model,
        "timestamp":        time.time(),
        "quality":          round(quality, 3),
        "query":            user_msg.strip()[:500],
        "response_preview": ai_msg.strip()[:500],
    })
    if len(runs) > 500:
        runs = runs[-500:]
    mem["runs"] = runs
    try:
        MEMORY_FILE.write_text(
            json.dumps(mem, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def get_last_exchange() -> dict | None:
    """Return the most recently logged exchange, or None if no history exists."""
    files = sorted(SESSIONS_DIR.glob("*.jsonl"), reverse=True) if SESSIONS_DIR.exists() else []
    for f in files:
        entries = _load_file(f)
        if entries:
            return entries[-1]
    return None


def _today_file() -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR / f"{date.today().isoformat()}.jsonl"


def append_exchange(user_msg: str, ai_msg: str, model: str = "unknown") -> None:
    """Append a completed exchange to today's session file."""
    if not (user_msg or "").strip() or not (ai_msg or "").strip():
        return
    entry = {
        "ts":    datetime.now().isoformat(),
        "user":  user_msg.strip()[:3000],
        "ai":    ai_msg.strip()[:3000],
        "model": model,
    }
    try:
        with _today_file().open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
    _append_memory_run(user_msg, ai_msg, model)


def _load_file(path: Path) -> list[dict]:
    entries: list[dict] = []
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    return entries


def get_boot_summary() -> dict:
    """
    Return summary of the most recent session for the CLI boot greeting.
    Keys: date, count, is_today, last_topics (list[str]), last_model
    Returns empty dict if no prior sessions.
    """
    files = sorted(SESSIONS_DIR.glob("*.jsonl"), reverse=True) if SESSIONS_DIR.exists() else []
    for f in files:
        entries = _load_file(f)
        if not entries:
            continue
        try:
            session_date = date.fromisoformat(f.stem)
        except Exception:
            continue

        # Extract short topic labels from last few user messages
        topics = []
        for e in entries[-4:]:
            u = (e.get("user") or "").strip()
            if u:
                topics.append(u[:80].replace("\n", " "))

        last_model = entries[-1].get("model", "?") if entries else "?"
        return {
            "date":       f.stem,
            "count":      len(entries),
            "is_today":   session_date == date.today(),
            "last_topics": topics,
            "last_model":  last_model,
        }
    return {}


def load_session_context(max_exchanges: int = 4) -> str:
    """
    Return a formatted block for injection into the system prompt.
    Includes the last N exchanges from the most recent session.
    Returns empty string if no history exists.
    """
    files = sorted(SESSIONS_DIR.glob("*.jsonl"), reverse=True) if SESSIONS_DIR.exists() else []
    for f in files:
        entries = _load_file(f)
        if not entries:
            continue
        try:
            session_date = date.fromisoformat(f.stem)
        except Exception:
            continue

        recent = entries[-max_exchanges:]
        date_label = "today (earlier)" if session_date == date.today() else f.stem
        lines = [
            f"\n\n---\n## SESSION MEMORY ({date_label} — {len(entries)} exchanges total)\n",
            "Recent exchanges (oldest first):\n",
        ]
        for e in recent:
            ts_raw = e.get("ts", "")
            try:
                ts = datetime.fromisoformat(ts_raw).strftime("%H:%M")
            except Exception:
                ts = "--:--"
            u = (e.get("user") or "")[:200].replace("\n", " ")
            a = (e.get("ai")   or "")[:200].replace("\n", " ")
            m = e.get("model", "?")
            lines.append(f"[{ts}] You: {u}")
            lines.append(f"[{ts}] {m}: {a}\n")
        lines.append("---")
        return "\n".join(lines)
    return ""
