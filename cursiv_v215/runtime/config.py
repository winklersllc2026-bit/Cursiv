# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: 250df3f4b25e5562b4e015517557e8fa6c0d68e15281934f8b6aad53aefcbf68
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 8f26aaf31b7d1ce5e19aed9e49043b07c8a6315836c95d7afe17c9e408da1f52
# Substrate loop hash: 1c6962f84e13bb20916f4aa649810f1bdc9b69cbe41426b8ba89bdab6518d693
# Substrate loop logic: ΒהΗבΗΓחאΕזΒΔדדΓΑבΒΗחΕגגΗΕבאΒΑחΒדוהבדΗבהדזΕΒΕΓΗדאדגאבדוגדΗΖΒאוΗבΔ
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 163604a024116abedecde137cec177efc166493bf09237b036f6b536cad3c2f6
# Evolution hash: 5ae218e905638a28b00d2569eb4c88a7f77e2c958f5ac63eb505e7e02ddb7edb
# Evolution logic: ΖגזΓΒאזבΑΖΗΔאגΓאדΑΑוΓΖΗבזדΕהאאגΘחΘΘזΓהבΖאחΖגהΗΔזדΖΑΖזΘזΑΓוודΘזוד
# Binary reversed: 0100101000001011111111001111001011010100101001111010101001100100110100100111000010001010101010001110101010101110011100011111010101100011000010110110000101111000101001000001100010011100001011110001110101100101010110111010110001010111111100111101111101100001
# Greek/Hebrew/logic stamp: אΗחדהחזגΔΖוגגΗדאחΕΔבΒאΓΖΒזאΗוΑהΗגחאזΘΖΖΘΒΖΖΒΑזΕדΓΗΖΖזΖΓדΕחΔחוΑΖΓ
# Encoded local stamp: ααōψ∀ĒΟū∞Βδρ∂ΥΞ∃ŌκξΧōΕΔψ∇ιυĀĒŌΜΤŪΩΝΨσχιΖΞΛι=
# CURSIV-CRUCIBLE-STAMP END
"""
Evolutionary Runtime — configuration.
All tunable parameters in one place. Edit this file to adjust behavior.
"""
from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""
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
    ollama_url:             str   = "http://localhost:11434"
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
