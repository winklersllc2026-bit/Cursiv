"""
LoRA training — fine-tunes a small local base model on your own collected
training data (.cursiv/training_data.jsonl, the same file watcher.py fills
automatically and the Training Data dialog's image/notes/manual-JSON entries
all feed into).

Deliberately scoped small: Qwen2.5-1.5B-Instruct, LoRA r=8 alpha=16 (mirrors
the checkpoint convention already referenced in
cursiv_v215/codex/system_prompt.md). Produces a portable PEFT adapter folder
under .cursiv/lora_checkpoints/<timestamp>/ -- not merged into a full model
or converted to GGUF/Ollama, to keep the dependency surface and the number
of steps that can fail to a minimum for a first working version.

Heavy ML packages (torch, transformers, peft, accelerate, datasets) are NOT
bundled in the installer -- same reasoning as Winkler-Codex's Ollama models:
multi-GB, best installed on demand into a real system Python, in a visible
terminal, not silently inside the frozen app. check_requirements() below is
pure stdlib + psutil (already bundled) specifically so the GUI can show real
disk/RAM/package numbers before anything heavy is imported or downloaded.

Run standalone once requirements are met:
    python -m cursiv_v215.training.lora_trainer [--epochs N]
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Callable, Optional

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

from cursiv_v215.training.watcher import TRAINING_JSONL, CURSIV_DIR

BASE_MODEL   = "Qwen/Qwen2.5-1.5B-Instruct"
LORA_R       = 8
LORA_ALPHA   = 16
LORA_DROPOUT = 0.05
# Standard PEFT target modules for the Qwen2/Llama attention + MLP blocks.
LORA_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]

REQUIRED_PACKAGES = ("torch", "transformers", "peft", "accelerate", "datasets")

MIN_FREE_DISK_GB = 8.0     # ~3GB model download + tokenizer/cache + adapter + margin
MIN_FREE_RAM_GB  = 8.0     # bf16 base weights + LoRA optimizer state + activations
MIN_EXAMPLES     = 10      # below this, a fine-tune is unlikely to move the model much
DEFAULT_EPOCHS   = 1       # kept low by default -- see CPU_SECONDS_PER_EXAMPLE below

# Measured directly: a single forward+backward pass on this base model, on a
# CPU with no CUDA, at max_length=512, took ~360s/example in testing. That's
# ~30 hours for 100 examples at 3 epochs -- not something to default someone
# into without warning them first. check_requirements() uses this to show a
# real estimate before anything starts; a CUDA GPU is dramatically faster,
# so the estimate is skipped when one's detected rather than needlessly
# alarming a user who won't hit anywhere near this number.
CPU_SECONDS_PER_EXAMPLE = 360

CHECKPOINTS_DIR = CURSIV_DIR / "lora_checkpoints"


# ── Requirements check (no heavy imports -- safe to call any time) ─────────

def missing_packages() -> list[str]:
    import importlib
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except Exception:
            missing.append(pkg)
    return missing


def find_system_python() -> Optional[str]:
    """Locate a real, standalone Python interpreter -- NOT sys.executable,
    which inside the frozen Cursiv.exe is the app itself, not a Python that
    can pip install torch/transformers/peft into its own site-packages."""
    for cmd in ("python", "python3"):
        p = shutil.which(cmd)
        if p:
            return p
    # The py.exe launcher is registered globally by python.org's official
    # Windows installer independent of PATH -- more reliable than "python"
    # alone, and what Cursiv's own full-setup bootstrap installs.
    py_launcher = shutil.which("py")
    if py_launcher:
        return py_launcher
    programs = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python"
    if programs.exists():
        for sub in sorted(programs.glob("Python3*"), reverse=True):
            exe = sub / "python.exe"
            if exe.exists():
                return str(exe)
    return None


def _gpu_info() -> tuple[bool, str]:
    try:
        import torch
        if torch.cuda.is_available():
            return True, torch.cuda.get_device_name(0)
    except Exception:
        pass
    return False, ""


def check_requirements() -> dict:
    """Real, current numbers -- disk, RAM, packages, GPU, example count --
    for the GUI to show before anything heavy is downloaded or imported."""
    disk_free_gb = shutil.disk_usage(str(Path.home())).free / (1024 ** 3)

    ram_total_gb = 0.0
    try:
        import psutil
        ram_total_gb = psutil.virtual_memory().total / (1024 ** 3)
    except Exception:
        pass

    missing = missing_packages()
    gpu_available, gpu_name = _gpu_info() if not missing else (False, "")

    examples = load_examples()
    python_exe = find_system_python()

    est_cpu_seconds = len(examples) * DEFAULT_EPOCHS * CPU_SECONDS_PER_EXAMPLE

    return {
        "disk_free_gb":   round(disk_free_gb, 1),
        "disk_ok":        disk_free_gb >= MIN_FREE_DISK_GB,
        "ram_total_gb":   round(ram_total_gb, 1),
        "ram_ok":         ram_total_gb == 0.0 or ram_total_gb >= MIN_FREE_RAM_GB,
        "gpu_available":  gpu_available,
        "gpu_name":       gpu_name,
        "missing_packages": missing,
        "packages_ok":    not missing,
        "python_exe":     python_exe,
        "python_ok":      python_exe is not None,
        "example_count":  len(examples),
        "examples_ok":    len(examples) >= MIN_EXAMPLES,
        "base_model":     BASE_MODEL,
        "default_epochs": DEFAULT_EPOCHS,
        # Only meaningful for CPU training -- a CUDA GPU is dramatically
        # faster and this fixed per-example estimate doesn't apply to it.
        "est_cpu_hours":  round(est_cpu_seconds / 3600, 1),
    }


def pip_install_torch_argv(python_exe: str) -> list[str]:
    """CPU-only torch by default -- the accessible, always-works path this
    feature is built around. A user with a CUDA GPU already has a driver
    and can swap the index URL themselves; auto-detecting CUDA reliably
    before torch is even installed isn't worth the extra failure surface.
    Kept as its own call (separate from pip_install_rest_argv) since torch's
    special --index-url shouldn't apply to the other packages."""
    return [
        python_exe, "-m", "pip", "install", "--upgrade",
        "torch", "--index-url", "https://download.pytorch.org/whl/cpu",
    ]


def pip_install_rest_argv(python_exe: str) -> list[str]:
    return [python_exe, "-m", "pip", "install", "--upgrade",
            "transformers", "peft", "accelerate", "datasets"]


# ── Data loading ────────────────────────────────────────────────────────────

def load_examples() -> list[dict]:
    if not TRAINING_JSONL.exists():
        return []
    examples = []
    for line in TRAINING_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if isinstance(d, dict) and d.get("prompt") and d.get("response"):
            examples.append(d)
    return examples


def format_example(entry: dict) -> str:
    return (
        f"### Instruction:\n{entry['prompt']}\n\n"
        f"### Response:\n{entry['response']}"
    )


# ── Training (heavy imports happen only in here) ────────────────────────────

def run_training(
    epochs: int = DEFAULT_EPOCHS,
    output_dir: Optional[Path] = None,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> dict:
    """Fine-tunes BASE_MODEL with LoRA on every example currently in
    training_data.jsonl. Blocking -- run on a background thread/process."""
    def log(msg: str) -> None:
        if progress_cb:
            progress_cb(msg)
        else:
            print(msg, flush=True)

    examples = load_examples()
    if not examples:
        raise RuntimeError("No training examples found in training_data.jsonl.")
    log(f"Loaded {len(examples)} training example(s).")

    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer,
        DataCollatorForLanguageModeling, Trainer, TrainingArguments,
    )

    dtype = torch.bfloat16  # halves memory vs fp32; works on CPU and GPU alike
    log(f"Loading tokenizer and base model ({BASE_MODEL})...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, dtype=dtype)

    lora_config = LoraConfig(
        r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES, bias="none", task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    log(f"LoRA adapter attached (r={LORA_R}, alpha={LORA_ALPHA}). "
        f"Trainable params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

    texts = [format_example(e) + tokenizer.eos_token for e in examples]
    dataset = Dataset.from_dict({"text": texts})

    def _tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=512)

    dataset = dataset.map(_tokenize, batched=True, remove_columns=["text"])

    if output_dir is None:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = CHECKPOINTS_DIR / stamp
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    args = TrainingArguments(
        output_dir=str(output_dir / "_trainer_state"),
        num_train_epochs=epochs,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=1,
        save_strategy="no",
        report_to=[],
    )
    trainer = Trainer(
        model=model, args=args, train_dataset=dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )

    log(f"Starting training -- {epochs} epoch(s) over {len(examples)} example(s). "
        f"This can take a while on CPU.")
    trainer.train()

    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    log(f"Adapter saved to {output_dir}")

    return {"output_dir": str(output_dir), "example_count": len(examples), "epochs": epochs}


# ── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Cursiv LoRA training")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS,
                         help=f"Default {DEFAULT_EPOCHS} -- CPU training is slow "
                              f"(~{CPU_SECONDS_PER_EXAMPLE}s/example/epoch measured), "
                              f"so this stays low unless you raise it deliberately.")
    parser.add_argument("--force", action="store_true",
                         help="Skip the requirement pre-flight check.")
    args = parser.parse_args()

    print("")
    print("  Cursiv — LoRA Training")
    print(f"  Base model: {BASE_MODEL}  (LoRA r={LORA_R} alpha={LORA_ALPHA})")
    print("")

    if not args.force:
        req = check_requirements()
        print(f"  Free disk:     {req['disk_free_gb']} GB  "
              f"({'OK' if req['disk_ok'] else f'need {MIN_FREE_DISK_GB}+ GB'})")
        if req["ram_total_gb"]:
            print(f"  Total RAM:     {req['ram_total_gb']} GB  "
                  f"({'OK' if req['ram_ok'] else f'need {MIN_FREE_RAM_GB}+ GB'})")
        print(f"  GPU:           {req['gpu_name'] if req['gpu_available'] else 'none detected (CPU training)'}")
        print(f"  Examples:      {req['example_count']}  "
              f"({'OK' if req['examples_ok'] else f'fewer than the recommended {MIN_EXAMPLES}'})")
        if not req["gpu_available"] and req["example_count"]:
            est_hours = round(req["example_count"] * args.epochs * CPU_SECONDS_PER_EXAMPLE / 3600, 1)
            print(f"  Estimated time: ~{est_hours} hour(s) on CPU at "
                  f"{args.epochs} epoch(s) (measured ~{CPU_SECONDS_PER_EXAMPLE}s/example/epoch -- "
                  f"a GPU would be dramatically faster)")
        print("")
        if req["missing_packages"]:
            print(f"  Missing packages: {', '.join(req['missing_packages'])}")
            print("  Install them first, or re-run with --force to try anyway.")
            sys.exit(1)
        if not req["disk_ok"]:
            print("  Not enough free disk space. Free some up and try again, "
                  "or re-run with --force.")
            sys.exit(1)
        if req["example_count"] == 0:
            print("  No training examples yet -- add some in the Training Data "
                  "dialog first (upload an image, paste JSON, or type notes and "
                  "ask to translate them).")
            sys.exit(1)

    def progress(msg: str) -> None:
        print(f"  {msg}", flush=True)

    result = run_training(epochs=args.epochs, progress_cb=progress)
    print("")
    print(f"  Done. Adapter saved to: {result['output_dir']}")
    print("")


if __name__ == "__main__":
    main()
