"""
Where training data and LoRA adapters live. Examples get into
training_data.jsonl only on purpose: "Save to Training", the Training Data
window (images, notes, pasted JSON), or the chat's notes-to-JSON command.
"""
from __future__ import annotations

from pathlib import Path

ROOT           = Path(__file__).parent.parent.parent
CURSIV_DIR     = ROOT / ".cursiv"
TRAINING_JSONL = CURSIV_DIR / "training_data.jsonl"
