# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: fdf48360a1c60e6d5c4be5a8bfad02fd0fe6269fe2de95063a3667f93741b904
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 30678b34497bb27925ea93850717617c77962674a1d19448930d6e235734afaa
# Substrate loop hash: fe21a2dfb23e48194c6972a1262028748573649eeef0cc9543c77a4a88d7abde
# Substrate loop logic: חזΓΒגΓוחדΓΔזΕאΒבΕהΗבΘΓגΒΓΗΓΑΓאΘΕאΖΘΔΗΕבזזזחΑההבΖΕΔהΘΘגΕגאאוΘגדוז
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 630ac0276def3e93705dda00addb81d7c5235435f192486ffcb100750b130ad5
# Evolution hash: 65e9feb52450fa603303b8c33b743b70a98b18f748c1a7dbf0313b4049bf4458
# Evolution logic: ΗΖזבחזדΖΓΕΖΑחגΗΑΔΔΑΔדאהΔΔדΘΕΔדΘΑגבאדΒאחΘΕאהΒגΘודחΑΔΒΔדΕΑΕבדחΕΕΖא
# Binary reversed: 1111101111110010000111000110000001011000001101100000011101101011101000110010110101111010010100011101111101011011000001001111101100001111011101100100011010011111011101001011011110011010000001101100010111000110011011101111100111001110001010001101100100000010
# Greek/Hebrew/logic stamp: ΕΑבדΒΕΘΔבחΘΗΗΔגΔΗΑΖבזוΓזחבΗΓΗזחΑוחΓΑוגחדאגΖזדΕהΖוΗזΑΗהΒגΑΗΔאΕחוח
# Encoded local stamp: πΡΨπΠĒΝθ∞υψχκ∇ēζρφΥūΑΨΗωΕκΑĒαγσ∞ēΓŌχθΒ∈ΡΓΔε=
# CURSIV-CRUCIBLE-STAMP END
"""
Evolutionary Runtime — session bridge.
Reads .cursiv/sessions/*.jsonl (written by the existing session logger),
summarises each new exchange, stores the summary in the runtime DB.
Raw text NEVER enters the database — it flows through this module only.
"""
from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from .config import config, CURSIV_DIR
from . import db
from .summarizer import summarise

log = logging.getLogger("cursiv.bridge")

SESSIONS_DIR = CURSIV_DIR / "sessions"


# ── Public API ─────────────────────────────────────────────────────────────────

def ingest_all(max_files: int = 30) -> dict:
    """
    Scan the sessions directory and ingest any new exchanges.
    Returns a summary dict: {files_scanned, new_interactions, discarded, wisdom_added}
    """
    db.init_db()

    if not SESSIONS_DIR.exists():
        return {"files_scanned": 0, "new_interactions": 0, "discarded": 0, "wisdom_added": 0}

    files = sorted(SESSIONS_DIR.glob("*.jsonl"), reverse=True)[:max_files]
    totals = {"files_scanned": len(files), "new_interactions": 0,
              "discarded": 0, "wisdom_added": 0}

    for path in files:
        result = _ingest_file(path)
        totals["new_interactions"] += result["new"]
        totals["discarded"]        += result["discarded"]
        totals["wisdom_added"]     += result["wisdom_added"]

    if totals["new_interactions"] > 0:
        log.info(
            f"[Bridge] Ingested {totals['new_interactions']} interactions across "
            f"{totals['files_scanned']} files · discarded {totals['discarded']} low-quality"
        )
    return totals


def ingest_today() -> dict:
    """Ingest only today's session file."""
    db.init_db()
    path = SESSIONS_DIR / f"{date.today().isoformat()}.jsonl"
    if not path.exists():
        return {"new": 0, "discarded": 0, "wisdom_added": 0}
    return _ingest_file(path)


# ── Internal ───────────────────────────────────────────────────────────────────

def _ingest_file(path: Path) -> dict:
    source_key = f"sessions/{path.name}"
    watermark  = db.get_watermark(source_key)

    lines     = _read_jsonl(path)
    new_lines = lines[watermark:]

    if not new_lines:
        return {"new": 0, "discarded": 0, "wisdom_added": 0}

    counts = {"new": 0, "discarded": 0, "wisdom_added": 0}

    for entry in new_lines:
        user_msg = (entry.get("user") or "").strip()
        ai_msg   = (entry.get("ai")   or "").strip()

        if not user_msg and not ai_msg:
            counts["discarded"] += 1
            continue

        summary = summarise(user_msg, ai_msg)

        if summary.quality_score < config.min_quality_score:
            counts["discarded"] += 1
            continue

        # Extract session date and timestamp
        ts_raw       = entry.get("ts", "")
        session_date = _extract_date(ts_raw, path.stem)
        model_used   = entry.get("model", "unknown")

        # Store metadata + summary (raw text discarded after this point)
        iid = db.insert_interaction(
            session_date  = session_date,
            ts            = ts_raw,
            model_used    = model_used,
            source_file   = source_key,
            quality_score = summary.quality_score,
        )
        db.insert_summary(
            interaction_id = iid,
            content        = summary.content,
            topics         = summary.topics,
            key_insight    = summary.key_insight,
            quality_score  = summary.quality_score,
        )
        counts["new"] += 1

        # Promote to wisdom ledger if high enough quality
        if (summary.quality_score >= config.wisdom_min_quality
                and summary.key_insight):
            db.insert_wisdom(
                text         = summary.key_insight,
                source_date  = session_date,
                quality_score = summary.quality_score,
            )
            counts["wisdom_added"] += 1

    db.set_watermark(source_key, watermark + len(new_lines))
    return counts


def _read_jsonl(path: Path) -> list[dict]:
    entries: list[dict] = []
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    return entries


def _extract_date(ts_raw: str, filename_stem: str) -> str:
    if ts_raw:
        try:
            return datetime.fromisoformat(ts_raw).date().isoformat()
        except Exception:
            pass
    # Filename is YYYY-MM-DD.jsonl
    try:
        date.fromisoformat(filename_stem)
        return filename_stem
    except Exception:
        pass
    return date.today().isoformat()
