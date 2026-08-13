# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: 537eafa4c65a340a2fbfb8db0421eb164920f6cd86c98daf7541d140849d6e40
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: dd5490b5d3f559a5aa428fedebeb71e581843c1d519c1822014bc4daab628d27
# Substrate loop hash: 7ab756ab9782aa848a920e114b6ba5770eecb0f019cbfcb992e89fe7824b73ff
# Substrate loop logic: ΘגדΘΖΗגדבΘאΓגגאΕאגבΓΑזΒΒΕדΗדגΖΘΘΑזזהדΑחΑΒבהדחהדבבΓזאבחזΘאΓΕדΘΔחח
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: d0f78c7c4b9773304ad6c55f76e52437060f166d95425abde9ee386d0c7d9f1e
# Evolution hash: 3b96d9471600bbf979c750b6e1c034b692a0505c1566df03d24a0e255fa8a31f
# Evolution logic: ΔדבΗובΕΘΒΗΑΑדדחבΘבהΘΖΑדΗזΒהΑΔΕדΗבΓגΑΖΑΖהΒΖΗΗוחΑΔוΓΕגΑזΓΖΖחגאגΔΒח
# Binary reversed: 1010110011100111010111110101001000110110101001011100001000000101010011111101111111010001101111010000001001001000011111011000011000101001010000001111011000111011000101100011100100011011010111111110101000101000101110000010000000010010100110110110011100100000
# Greek/Hebrew/logic stamp: ΑΕזΗובΕאΑΕΒוΒΕΖΘחגואבהΗאוהΗחΑΓבΕΗΒדזΒΓΕΑדואדחדחΓגΑΕΔגΖΗהΕגחגזΘΔΖ
# Encoded local stamp: κι∂ΥŌηΞμο∞ΑΚαφΕΛξωΧΘρπλΠΜμīΙΖΤΒΓΧχβ∞λσōΓΖΣφ=
# CURSIV-CRUCIBLE-STAMP END
"""
Evolutionary Runtime — scheduler.
Runs the evolution cycle on a configurable interval in a background thread.
Also wires in the guardian storage check before each cycle.

Usage (from any Python context):
    from cursiv_v215.runtime.scheduler import start, stop, status
    start()          # kick off background thread
    status()         # dict with last-run info
    stop()           # clean shutdown
"""
from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import logging
import threading
import time
from datetime import datetime
from typing import Optional

from .config import config
from .evolution_engine import run_cycle_safe, CycleResult
from .guardian import check as guardian_check

log = logging.getLogger("cursiv.scheduler")

_thread:        Optional[threading.Thread] = None
_stop_event:    threading.Event            = threading.Event()
_last_result:   Optional[CycleResult]      = None
_last_run_at:   Optional[str]              = None
_next_run_at:   Optional[str]              = None
_cycle_count:   int                        = 0


def start(interval_hours: Optional[float] = None) -> None:
    """Start the background scheduler. Safe to call multiple times."""
    global _thread, _stop_event

    if _thread and _thread.is_alive():
        log.info("[Scheduler] Already running")
        return

    _stop_event.clear()
    hours = interval_hours or config.evolution_frequency_hours
    _thread = threading.Thread(
        target=_loop,
        args=(hours,),
        name="cursiv-evo-scheduler",
        daemon=True,
    )
    _thread.start()
    log.info(f"[Scheduler] Started — cycle every {hours}h")


def stop() -> None:
    """Signal the scheduler to stop after the current cycle (or sleep) finishes."""
    _stop_event.set()
    log.info("[Scheduler] Stop requested")


def run_now() -> CycleResult:
    """Trigger an immediate cycle (blocking). Also called by the scheduler loop."""
    global _last_result, _last_run_at, _cycle_count

    log.info("[Scheduler] Running cycle now")
    guardian_check()
    result = run_cycle_safe()
    _last_result = result
    _last_run_at = result.started_at
    _cycle_count += 1
    return result


def status() -> dict:
    return {
        "running":       _thread is not None and _thread.is_alive(),
        "cycle_count":   _cycle_count,
        "last_run_at":   _last_run_at,
        "next_run_at":   _next_run_at,
        "last_result":   _last_result.to_dict() if _last_result else None,
    }


# ── Internal ───────────────────────────────────────────────────────────────────

def _loop(interval_hours: float) -> None:
    global _next_run_at

    interval_sec = interval_hours * 3600
    log.info(f"[Scheduler] Loop running — interval={interval_hours}h")

    while not _stop_event.is_set():
        run_now()

        # Sleep in 30-second ticks so we respond to stop quickly
        wake = time.time() + interval_sec
        _next_run_at = datetime.fromtimestamp(wake).isoformat()

        while time.time() < wake:
            if _stop_event.wait(timeout=30):
                log.info("[Scheduler] Stopped mid-sleep")
                return

    log.info("[Scheduler] Loop exited cleanly")
