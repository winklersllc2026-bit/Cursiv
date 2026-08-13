# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: 4cc1bd23897069da88f5c845000bc6c474167b6f73a36d62cccb18dd4d151a65
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: e241491364f420cb8090354653a9f9547518a65568b15cde3551e32262433b7a
# Substrate loop hash: 5e9de1244872e1066285e156bb3faa5df48ffb129bceb9a4e80bab95de7c4eab
# Substrate loop logic: ΖזבוזΒΓΕΕאΘΓזΒΑΗΗΓאΖזΒΖΗדדΔחגגΖוחΕאחחדΒΓבדהזדבגΕזאΑדגדבΖוזΘהΕזגד
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 9af6cfa7c4e32d48d9e9bcfdecdccca867ac16bd606c3c5f8e14911160bab8ea
# Evolution hash: 0551bf0fe9c796835eba2ea567a0222a8e153aaff18935b80050e206a320632e
# Evolution logic: ΑΖΖΒדחΑחזבהΘבΗאΔΖזדגΓזגΖΗΘגΑΓΓΓגאזΒΖΔגגחחΒאבΔΖדאΑΑΖΑזΓΑΗגΔΓΑΗΔΓז
# Binary reversed: 0010001100111000110110110100110000011001111000000110100110110101000100011111101000110001001010100000000000001101001101100011001011100010100001101110110101101111111011000101110001101011011001000011001100111101100000011011101100101011100010101000010101101010
# Greek/Hebrew/logic stamp: ΖΗגΒΖΒוΕוואΒדהההΓΗוΗΔגΔΘחΗדΘΗΒΕΘΕהΗהדΑΑΑΖΕאהΖחאאגובΗΑΘבאΔΓודΒההΕ
# Encoded local stamp: ∇Ζū∇φΚΕφτκΚΘŪΧΞψΠΕΒīΒΩΥūΝξΕλΥΤνΩφΝΦκΥΟξΗσΔΑ=
# CURSIV-CRUCIBLE-STAMP END
"""
FunForge Meta — Bounded creative spike engine.
Turns "let's just mess around" into a repeatable micro-process.
"""

from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""
import time

TRIGGER_WORDS = ("funforge", "let's play", "lets play", "quick experiment")

FUNFORGE_SYSTEM = """[FUNFORGE META ACTIVE]
You are in FunForge mode — a bounded creative spike with hard rules:
1. Stay focused on the single topic/constraint defined below. One thing only.
2. Be playful, generative, low-pressure. No overbuilding. No rabbit holes.
3. Active council: Lens + Spark + Balance only. All other agents silent.
4. Constitutional guardrails remain non-negotiable — identity drift, energy
   depletion, or family misalignment aborts immediately back to JWArchitectCore.
5. At session close you MUST produce the artifact below in EXACTLY this format,
   plain text, no extra headers, nothing after it:

FunForge Spike Complete
Focus: [one sentence]
What happened: [one sentence]
Keep: [one micro-adjustment worth keeping]
State: [three words — emotional/energy state]
Next possible spark: [optional one-liner or leave blank]
"""

FUNFORGE_CLOSE_PROMPT = (
    "FunForge time is up. Produce the closing artifact now in EXACTLY this "
    "format — plain text, no markdown, nothing before or after:\n\n"
    "FunForge Spike Complete\n"
    "Focus: [one sentence]\n"
    "What happened: [one sentence]\n"
    "Keep: [one micro-adjustment]\n"
    "State: [three words]\n"
    "Next possible spark: [optional one-liner]"
)

DEFAULT_DURATION_MIN = 45


class FunForgeSession:
    def __init__(self, topic: str, duration_min: int = DEFAULT_DURATION_MIN):
        self.topic       = topic
        self.duration_s  = duration_min * 60
        self.start_time  = time.time()
        self.anchored    = False
        self.extended    = False
        self.closed      = False

    @property
    def elapsed_s(self) -> float:
        return time.time() - self.start_time

    @property
    def remaining_s(self) -> float:
        return max(0.0, self.duration_s - self.elapsed_s)

    @property
    def expired(self) -> bool:
        return self.elapsed_s >= self.duration_s

    def time_display(self) -> str:
        r = int(self.remaining_s)
        return f"{r // 60}m {r % 60:02d}s"

    def extend(self) -> bool:
        """One-time 30-minute extension. Returns False if already extended."""
        if self.extended:
            return False
        self.duration_s += 30 * 60
        self.extended = True
        return True

    def system_fragment(self) -> str:
        return f"{FUNFORGE_SYSTEM}\nSpike topic: {self.topic}"


def detect_trigger(text: str) -> bool:
    lower = text.lower().strip()
    return any(lower.startswith(t) for t in TRIGGER_WORDS) or lower.startswith("spike ")


def extract_topic(text: str) -> str:
    lower = text.lower().strip()
    for trigger in (*TRIGGER_WORDS, "spike"):
        if lower.startswith(trigger):
            remainder = text[len(trigger):].strip(" —:-")
            return remainder if remainder else "open creative exploration"
    return text.strip()
