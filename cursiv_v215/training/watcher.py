# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: 89afdcbc76c853f5b619ee1fb5dd27f22a4709fea73d803b9a29e59993f1796f
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: a4fdb2bdaed53ab3150f6461fd7fa3f573f4a42e756000c7f749ac810cb4dce6
# Substrate loop hash: 701cbc5444a92a5e44321679b6b31841b4062f696ccd2959d300fbca06ae0bb0
# Substrate loop logic: ΘΑΒהדהΖΕΕΕגבΓגΖזΕΕΔΓΒΗΘבדΗדΔΒאΕΒדΕΑΗΓחΗבΗההוΓבΖבוΔΑΑחדהגΑΗגזΑדדΑ
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 4aa5cc345b04c1c1e6262cd5b9fbf7691f4b6790c83e769de32e4375bb50380e
# Evolution hash: e5909c39a14310d46174e32d67b63294db8d74ad175ade615a89a6ea56e12351
# Evolution logic: זΖבΑבהΔבגΒΕΔΒΑוΕΗΒΘΕזΔΓוΗΘדΗΔΓבΕודאוΘΕגוΒΘΖגוזΗΒΖגאבגΗזגΖΗזΒΓΔΖΒ
# Binary reversed: 0001100101011111101100111101001111100110001100011010110011111010110101101000100101110111100011111101101010111011010011101111010001000101001011100000100111110111010111101100101100010000110011011001010101001001011110101001100110011100111110001110100101101111
# Greek/Hebrew/logic stamp: חΗבΘΒחΔבבבΖזבΓגבדΔΑאוΔΘגזחבΑΘΕגΓΓחΘΓווΖדחΒזזבΒΗדΖחΔΖאהΗΘהדהוחגבא
# Encoded local stamp: φΚΨδΜΩβīΥΟΘζΞξ∈ōΧψυΔ∂ο∈ΑōπωĒΡīĪΗλēΗΣ∃ΒōΦΡΩφ=
# CURSIV-CRUCIBLE-STAMP END
"""
Conversation Watcher — background training data collector.

Monitors .cursiv/memory.json for new conversation runs.
Scores each exchange using the existing Academy quality scorer.
Saves high-quality exchanges (score >= threshold) to
.cursiv/training_data.jsonl for the next LoRA training pass.

Run standalone:
    python -m cursiv_v215.training.watcher

Or import and call watch() from a background thread.
"""

from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import json
import time
import threading
from datetime import datetime
from pathlib import Path

ROOT          = Path(__file__).parent.parent.parent
CURSIV_DIR    = ROOT / ".cursiv"
MEMORY_FILE   = CURSIV_DIR / "memory.json"
TRAINING_JSONL = CURSIV_DIR / "training_data.jsonl"
SEEN_FILE     = CURSIV_DIR / "watcher_seen.json"

QUALITY_THRESHOLD = 0.65   # only collect exchanges above this quality score
POLL_INTERVAL     = 15     # seconds between memory checks


def _load_seen() -> set[str]:
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()


def _save_seen(seen: set[str]) -> None:
    CURSIV_DIR.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(list(seen)), encoding="utf-8")


def _run_id(run: dict) -> str:
    return f"{run.get('agent_id', '')}_{run.get('timestamp', 0)}"


def _collect_run(run: dict) -> bool:
    """Return True if the run was collected as a training example."""
    quality = float(run.get("quality", 0.0))
    if quality < QUALITY_THRESHOLD:
        return False

    query    = run.get("query", "").strip()
    response = run.get("response_preview", "").strip()
    if not query or not response:
        return False

    example = {
        "prompt":    query,
        "response":  response,
        "quality":   round(quality, 3),
        "agent_id":  run.get("agent_id", "unknown"),
        "timestamp": datetime.now().isoformat(),
        "source":    "auto_watcher",
    }

    TRAINING_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with TRAINING_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(example) + "\n")
    return True


def _poll_once(seen: set[str]) -> tuple[int, set[str]]:
    """Check memory for new runs. Return (collected_count, updated_seen)."""
    if not MEMORY_FILE.exists():
        return 0, seen

    try:
        mem  = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        runs = mem.get("runs", [])
    except Exception:
        return 0, seen

    collected = 0
    for run in runs:
        rid = _run_id(run)
        if rid in seen:
            continue
        seen.add(rid)
        if _collect_run(run):
            collected += 1

    return collected, seen


def watch(stop_event: threading.Event | None = None, verbose: bool = True) -> None:
    """Main watch loop. Runs until stop_event is set (or forever if None)."""
    seen  = _load_seen()
    total = 0

    if verbose:
        print(f"[Watcher] Started — polling every {POLL_INTERVAL}s | threshold={QUALITY_THRESHOLD}")

    while True:
        if stop_event and stop_event.is_set():
            break

        count, seen = _poll_once(seen)
        _save_seen(seen)

        if count and verbose:
            total += count
            print(f"[Watcher] Collected {count} new example(s). Session total: {total}")

        time.sleep(POLL_INTERVAL)


def start_background_watcher() -> threading.Event:
    """Start the watcher in a daemon thread. Returns the stop event."""
    stop = threading.Event()
    t    = threading.Thread(target=watch, args=(stop, False), daemon=True)
    t.start()
    return stop


if __name__ == "__main__":
    watch(verbose=True)
