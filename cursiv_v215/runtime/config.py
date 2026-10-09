"""
Evolutionary Runtime — configuration.
All tunable parameters in one place. Edit this file to adjust behavior.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT       = Path(__file__).parent.parent.parent
CURSIV_DIR = ROOT / ".cursiv"
RUNTIME_DIR = CURSIV_DIR / "runtime"
CODEX_DIR   = ROOT / "cursiv_v215" / "codex"


@dataclass
class EvoConfig:
    # ── Storage ────────────────────────────────────────────────────────────────
    db_path:         Path  = field(default_factory=lambda: RUNTIME_DIR / "evo.db")
    max_storage_mb:  float = 150.0       # hard cap — guardian enforces this

    # ── Summarisation ──────────────────────────────────────────────────────────
    summary_max_chars:      int   = 800   # max chars per stored summary
    min_quality_score:      float = 0.35  # below this, interaction is discarded
    ollama_model:           str   = "llama3.1"
    ollama_url:             str   = "http://127.0.0.1:11434"
    ollama_timeout_s:       int   = 120
    ollama_num_ctx:         int   = 32768   # context window — must fit full 14-agent deliberation

    # ── Embeddings ─────────────────────────────────────────────────────────────
    embedding_model:  str = "all-MiniLM-L6-v2"   # 22 MB, CPU-fast
    embedding_dim:    int = 384

    # ── Pruning ────────────────────────────────────────────────────────────────
    retention_days_high:  int   = 90    # quality >= quality_threshold
    retention_days_low:   int   = 30    # quality < quality_threshold
    quality_threshold:    float = 0.55

    # ── Evolution cycle ────────────────────────────────────────────────────────
    evolution_frequency_hours:    int  = 24
    min_interactions_per_cycle:   int  = 5
    delta_approval_required:      bool = True   # Josh must approve before any patch applies
    max_deltas_per_cycle:         int  = 3

    # ── Wisdom ledger ──────────────────────────────────────────────────────────
    wisdom_max_entries:   int   = 500
    wisdom_min_quality:   float = 0.68
    wisdom_max_chars:     int   = 220

    # ── Pattern detection ──────────────────────────────────────────────────────
    min_cluster_size:  int = 3
    max_topics:        int = 20

    # ── System prompt file (target for delta patches) ─────────────────────────
    system_prompt_file: Path = field(
        default_factory=lambda: CODEX_DIR / "system_prompt.md"
    )
    delta_dir: Path = field(
        default_factory=lambda: RUNTIME_DIR / "deltas"
    )


# Module-level singleton — import this everywhere
config = EvoConfig()
