# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: 35502075c50af6ed7c5a15c318a4513e6aa7cafbfaba01d187d25ce78f23a6ab
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 9299c559631ac34a556f771992177e55d4c3e3705e387c89822c031c9b425e92
# Substrate loop hash: 1ea262126aaecc250fbeb25825d38785fa0e874808a38c7661788efdc3bf5370
# Substrate loop logic: ΒזגΓΗΓΒΓΗגגזההΓΖΑחדזדΓΖאΓΖוΔאΘאΖחגΑזאΘΕאΑאגΔאהΘΗΗΒΘאאזחוהΔדחΖΔΘΑ
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 03219a2591a7b68f4b0a0eb2bd95084e1c99547e97b17a6d659a07374ef2f3e4
# Evolution hash: 6e197944b21e6e6477e404a3107b5f2f14181f393224aede9ad0bed25cb5c554
# Evolution logic: ΗזΒבΘבΕΕדΓΒזΗזΗΕΘΘזΕΑΕגΔΒΑΘדΖחΓחΒΕΒאΒחΔבΔΓΓΕגזוזבגוΑדזוΓΖהדΖהΖΖΕ
# Binary reversed: 1100101010100000010000001110101000111010000001011111011001111011111000111010010110001010001111001000000101010010101010001100011101100101010111100011010111111101111101011101010100001000101110000001111010110100101000110111111000011111010011000101011001011101
# Greek/Hebrew/logic stamp: דגΗגΔΓחאΘזהΖΓוΘאΒוΒΑגדגחדחגהΘגגΗזΔΒΖΕגאΒΔהΖΒגΖהΘוזΗחגΑΖהΖΘΑΓΑΖΖΔ
# Encoded local stamp: ΣυΙĪοΜ∂ēīιψ∀ΑυγΚγΧĪ∞ΕΡρηΣθΥεŌδτσχΘγĒΓφīλνĀĀ=
# CURSIV-CRUCIBLE-STAMP END
"""
Evolutionary Runtime — metrics tracker.
Records quality trends, storage usage, cycle outcomes, and drift signals.
All data goes to the metrics table; nothing is written to disk outside the DB.
"""
from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import logging
from datetime import datetime, timedelta
from typing import Optional

from . import db
from .config import config

log = logging.getLogger("cursiv.metrics")


def record_cycle(
    *,
    ingested: int,
    embedded: int,
    clusters_found: int,
    deltas_generated: int,
    wisdom_added: int,
    pruned: int,
    db_size_bytes: int,
) -> None:
    """Snapshot one full evolution cycle into the metrics table."""
    with db.get_db() as conn:
        conn.execute(
            """INSERT INTO metric_log
               (recorded_at, metric_name, metric_value, notes)
               VALUES (?,?,?,?)""",
            (datetime.now().isoformat(), "cycle_summary",
             float(ingested),
             f"embedded={embedded} clusters={clusters_found} deltas={deltas_generated} "
             f"wisdom={wisdom_added} pruned={pruned} db_bytes={db_size_bytes}"),
        )


def record_value(name: str, value: float, notes: str = "") -> None:
    """Store a single named metric data point."""
    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO metric_log (recorded_at, metric_name, metric_value, notes) VALUES (?,?,?,?)",
            (datetime.now().isoformat(), name, value, notes),
        )


def get_trend(metric_name: str, days: int = 7) -> list[tuple[str, float]]:
    """Return (recorded_at, value) pairs for a metric over the last N days."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with db.get_db() as conn:
        rows = conn.execute(
            "SELECT recorded_at, metric_value FROM metric_log "
            "WHERE metric_name = ? AND recorded_at > ? ORDER BY recorded_at",
            (metric_name, cutoff),
        ).fetchall()
    return [(r["recorded_at"], r["metric_value"]) for r in rows]


def quality_drift() -> Optional[float]:
    """
    Compare average quality of last 50 summaries vs. previous 50.
    Returns delta (positive = improving). None if not enough data.
    """
    with db.get_db() as conn:
        rows = conn.execute(
            "SELECT quality_score FROM summaries ORDER BY id DESC LIMIT 100"
        ).fetchall()

    scores = [r["quality_score"] for r in rows]
    if len(scores) < 20:
        return None

    half = len(scores) // 2
    recent = scores[:half]
    older  = scores[half:]
    drift  = round(sum(recent) / len(recent) - sum(older) / len(older), 4)
    return drift


def storage_health() -> dict:
    """Return storage utilisation as a dict."""
    from pathlib import Path
    p = config.db_path
    size_bytes = p.stat().st_size if p.exists() else 0
    size_mb    = size_bytes / 1_048_576
    pct        = round((size_mb / config.max_storage_mb) * 100, 1) if config.max_storage_mb else 0
    return {
        "db_size_bytes": size_bytes,
        "db_size_mb":    round(size_mb, 2),
        "budget_mb":     config.max_storage_mb,
        "used_pct":      pct,
        "over_budget":   size_mb > config.max_storage_mb,
    }


def wisdom_health() -> dict:
    """Return wisdom ledger utilisation."""
    with db.get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM wisdom_ledger").fetchone()[0]
        avg_q = conn.execute(
            "SELECT AVG(quality_score) FROM wisdom_ledger"
        ).fetchone()[0] or 0.0
    return {
        "entries":      count,
        "max_entries":  config.wisdom_max_entries,
        "used_pct":     round((count / config.wisdom_max_entries) * 100, 1),
        "avg_quality":  round(float(avg_q), 3),
    }


def summary_counts() -> dict:
    """Quick counts for the dashboard."""
    with db.get_db() as conn:
        interactions = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
        summaries    = conn.execute("SELECT COUNT(*) FROM summaries").fetchone()[0]
        pending      = conn.execute(
            "SELECT COUNT(*) FROM evolution_log WHERE status='pending'"
        ).fetchone()[0]
        approved     = conn.execute(
            "SELECT COUNT(*) FROM evolution_log WHERE status='approved'"
        ).fetchone()[0]
    return {
        "interactions": interactions,
        "summaries":    summaries,
        "pending_deltas":  pending,
        "approved_deltas": approved,
    }


def full_report() -> dict:
    """Aggregate everything into one status dict."""
    drift = quality_drift()
    return {
        "counts":   summary_counts(),
        "storage":  storage_health(),
        "wisdom":   wisdom_health(),
        "drift":    drift,
        "drift_direction": (
            "improving" if drift and drift > 0.02
            else "declining" if drift and drift < -0.02
            else "stable"
        ),
    }
