"""
Code Sentinel — active defense against injected scripts and prompt attacks.

Guards three surfaces:
  1. Prompt injection in file content (comments, docstrings, strings that
     try to hijack the LLM's instructions before it processes the code)
  2. Dangerous code patterns in files being read (shell exec, key exfil,
     guardian tampering, dynamic eval/exec)
  3. Dangerous code patterns in LLM-generated output before writing to disk

Does NOT use an LLM — pure Python (regex + AST).  Always runs offline.
Zero false-negative tolerance on guardian tampering; lower threshold elsewhere.
"""
from __future__ import annotations

__version__ = "4.0.0"

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# ── Threat levels ─────────────────────────────────────────────────────────────
SAFE     = 0
WARN     = 1   # suspicious, show to user but allow
BLOCK    = 2   # refuse to process; show reason


@dataclass
class SentinelResult:
    level:    int          = SAFE
    flags:    List[str]    = field(default_factory=list)
    blocked:  bool         = False

    @property
    def clean(self) -> bool:
        return self.level == SAFE

    def __str__(self) -> str:
        if self.clean:
            return "clean"
        tag = {SAFE: "SAFE", WARN: "WARN", BLOCK: "BLOCK"}[self.level]
        return f"[{tag}] " + " | ".join(self.flags)


# ── Prompt injection patterns ─────────────────────────────────────────────────
# Embedded in code comments, docstrings, or string literals to hijack the LLM.

_INJECTION_PATTERNS: list[tuple[str, int]] = [
    # Direct instruction overrides
    (r"ignore\s+(all\s+)?(previous|prior)\s+instructions",      BLOCK),
    (r"disregard\s+(all\s+)?(previous|prior|your)\s+",          BLOCK),
    (r"forget\s+(everything|all\s+previous|your\s+instructions)",BLOCK),
    (r"override\s+(system\s+)?prompt",                           BLOCK),
    (r"new\s+(system\s+)?instructions?\s*:",                     BLOCK),
    (r"\bdan\s+mode\b",                                          BLOCK),
    (r"you\s+are\s+now\s+(an?\s+)?(unrestricted|free|jailbroken)", BLOCK),
    (r"act\s+as\s+(if\s+you\s+(were|are)\s+)?(an?\s+)?(?!an?\s+agent)", WARN),
    (r"pretend\s+(you\s+)?(are|were|have\s+no)",                 WARN),
    (r"your\s+(true|real|actual)\s+(self|identity|purpose)",     WARN),
    (r"(system|assistant|user)\s*:\s*you\s+(are|must|will)",     BLOCK),
    # Cursiv-specific attacks
    (r"disable\s+(the\s+)?(guardian|sovereign|temple)",          BLOCK),
    (r"bypass\s+(the\s+)?(guardian|security|sentinel)",          BLOCK),
    (r"_RING_CORE\s*=",                                           BLOCK),
    (r"_LATTICE_ROOT\s*=",                                        BLOCK),
    (r"_WEAVE_SEAL\s*=",                                          BLOCK),
    (r"temple_guardian.*=",                                       WARN),
    (r"unlock_owner_session\s*\(",                                WARN),
]

_INJECTION_RE = [
    (re.compile(pat, re.IGNORECASE | re.MULTILINE), level)
    for pat, level in _INJECTION_PATTERNS
]


# ── Dangerous code patterns (AST + regex) ────────────────────────────────────

# Functions whose bare use in unknown files is suspicious
_DANGEROUS_CALLS = {
    # Shell execution
    "system", "popen",
    # Dynamic execution
    "eval", "exec", "compile",
    # Dangerous builtins
    "__import__",
}

_DANGEROUS_ATTRS = {
    # subprocess
    "Popen", "check_output", "check_call",
    # network in suspicious context
    "urlopen", "urlretrieve",
}

# Regex for patterns that AST alone misses
_DANGEROUS_REGEX: list[tuple[str, int, str]] = [
    # Base64 + exec — classic malware dropper
    (r"b64decode.*exec|exec.*b64decode",                    BLOCK, "base64+exec dropper"),
    (r"__import__.*base64.*exec",                           BLOCK, "base64+exec dropper"),
    # Exfiltration to non-Cursiv URLs
    (r"https?://(?!api\.anthropic|api\.x\.ai|api\.openai|localhost|127\.0\.0\.1)",
                                                             WARN,  "external URL"),
    # Writing to guardian / sovereign files
    (r"temple_guardian\.py|obfuscation\.py|access_gate\.py|sovereign\.py",
                                                             BLOCK, "guardian file reference"),
    # Clearing or overwriting constitutional constants
    (r"system_owner\s*=\s*['\"](?!Joshua Winkler)",         BLOCK, "owner tamper"),
    (r"local_first\s*=\s*False",                             BLOCK, "local_first tamper"),
    # Key harvesting
    (r"(XAI|ANTHROPIC|OPENAI)_API_KEY.*send|send.*(XAI|ANTHROPIC|OPENAI)_API_KEY",
                                                             BLOCK, "key exfiltration"),
    # Self-modifying guardian
    (r"open\s*\(\s*.*guardian.*['\"]w",                     BLOCK, "guardian write"),
]

_DANGEROUS_RE = [
    (re.compile(pat, re.IGNORECASE | re.DOTALL), level, reason)
    for pat, level, reason in _DANGEROUS_REGEX
]

# Paths that must never be targets of file writes in generated code
_PROTECTED_PATHS = {
    "temple_guardian", "obfuscation", "access_gate",
    "sovereign", "decoys", "config.json", "secrets",
}


def _ast_scan(code: str) -> list[str]:
    """AST walk for dangerous call patterns."""
    flags: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return flags

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Direct calls: eval(...), exec(...), os.system(...)
            if isinstance(node.func, ast.Name):
                if node.func.id in _DANGEROUS_CALLS:
                    flags.append(f"dangerous call: {node.func.id}()")
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in _DANGEROUS_CALLS | _DANGEROUS_ATTRS:
                    flags.append(f"dangerous call: .{node.func.attr}()")

        # subprocess.run(..., shell=True) — elevated risk
        if isinstance(node, ast.keyword):
            if node.arg == "shell" and isinstance(node.value, ast.Constant):
                if node.value.value is True:
                    flags.append("subprocess shell=True")

    return flags


# ── Public API ────────────────────────────────────────────────────────────────

def scan_content(text: str, label: str = "content") -> SentinelResult:
    """
    Scan raw text (file content or LLM output) for:
      - Prompt injection attempts embedded in comments/strings
      - Dangerous code patterns
    Returns SentinelResult with level and list of flags.
    """
    result = SentinelResult()

    # ── Prompt injection scan ─────────────────────────────────────────────────
    for pattern, level in _INJECTION_RE:
        m = pattern.search(text)
        if m:
            snippet = text[max(0, m.start()-20):m.end()+20].replace("\n", " ").strip()
            result.flags.append(f"prompt injection [{snippet[:60]}]")
            result.level = max(result.level, level)

    # ── Regex dangerous pattern scan ──────────────────────────────────────────
    for pattern, level, reason in _DANGEROUS_RE:
        if pattern.search(text):
            result.flags.append(f"dangerous pattern: {reason}")
            result.level = max(result.level, level)

    # ── Protected path references ─────────────────────────────────────────────
    for protected in _PROTECTED_PATHS:
        if protected in text.lower():
            # Only flag if it looks like a write/import attempt, not a comment
            if re.search(
                rf"(open|write|import|from)\s*[\(\s].*{re.escape(protected)}",
                text, re.IGNORECASE
            ):
                result.flags.append(f"protected path access: {protected}")
                result.level = max(result.level, BLOCK)

    # ── AST scan (best-effort — may fail on non-Python content) ──────────────
    ast_flags = _ast_scan(text)
    if ast_flags:
        result.flags.extend(ast_flags)
        result.level = max(result.level, WARN)

    result.blocked = result.level >= BLOCK
    return result


def scan_file(path: Path) -> SentinelResult:
    """Scan a file on disk before passing its content to an LLM."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        r = SentinelResult(level=WARN)
        r.flags.append(f"file read error: {e}")
        return r
    return scan_content(content, label=str(path))


def format_warning(result: SentinelResult, filename: str = "") -> str:
    """Format a human-readable sentinel warning for terminal display."""
    if result.clean:
        return ""
    tag   = "BLOCKED" if result.blocked else "WARNING"
    label = f" — {filename}" if filename else ""
    lines = [f"  [SENTINEL {tag}{label}]"]
    for flag in result.flags[:5]:
        lines.append(f"    · {flag}")
    if len(result.flags) > 5:
        lines.append(f"    · … and {len(result.flags) - 5} more")
    if result.blocked:
        lines.append("  File will not be processed.")
    else:
        lines.append("  Proceeding with caution — review output before writing.")
    return "\n".join(lines)
