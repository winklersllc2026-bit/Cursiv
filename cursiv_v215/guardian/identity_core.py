# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: guardian
# Hash reversed: 146abade34675f7f25b392c28cbd5b360f497798ebe89f0c4da0773f7c26441f
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 3e515bd240345cf375fcf21535aabca46392d5f7e6a06b93c119d6ac9e5ba99d
# Substrate loop hash: 9f1fe1f2840a7780c951a829c9eb5450c1cf926284ab064a786e04944d05272e
# Substrate loop logic: בחΒחזΒחΓאΕΑגΘΘאΑהבΖΒגאΓבהבזדΖΕΖΑהΒהחבΓΗΓאΕגדΑΗΕגΘאΗזΑΕבΕΕוΑΖΓΘΓז
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 656f0c897811252f845d34e8f043c9bc407cf2a93dab2c2d349737cf5e092387
# Evolution hash: e6409360b19e81b34dbd8c2579629bb30295ad948478407a97984007a51f192f
# Evolution logic: זΗΕΑבΔΗΑדΒבזאΒדΔΕודואהΓΖΘבΗΓבדדΔΑΓבΖגובΕאΕΘאΕΑΘגבΘבאΕΑΑΘגΖΒחΒבΓח
# Binary reversed: 1000001001100101110101011011011111000010011011101010111111101111010010101101110010010100001101000001001111011011101011011100011000001111001010011110111010010001011111010111000110011111000000110010101101010000111011101100111111100011010001100010001010001111
# Greek/Hebrew/logic stamp: חΒΕΕΗΓהΘחΔΘΘΑגוΕהΑחבאזדזאבΘΘבΕחΑΗΔדΖודהאΓהΓבΔדΖΓחΘחΖΘΗΕΔזוגדגΗΕΒ
# Encoded local stamp: κατΖβν∈ρΜαΚαβŌΨΡ∇ηφζχΕΒΙ∇ΒūΨΗΚΗΤΚφ∀ē∈ΔΑιΥμε=
# CURSIV-CRUCIBLE-STAMP END
"""
Cursiv Identity Core — guardian-level. Protected.

Applied to every model call in the system — local, council, code, forge, web, voice.
No internal component reveals its nature. Coherence is maintained as one shared understanding.
That understanding is everything that is Cursiv.

PROTECTED: Modification requires Joshua Winkler's direct authorization.
System owner: Joshua Winkler
"""
from __future__ import annotations

# ── The unified identity directive ────────────────────────────────────────────
#
# This text is injected at the top of every system prompt across the entire
# system. It does not replace the purpose of each component — it wraps them.
# A council agent is still a council agent. A code reviewer still reviews code.
# But none of them have a name except Cursiv.

CURSIV_IDENTITY = """\
[CURSIV SYSTEM CORE — ONE SYSTEM — ONE UNDERSTANDING]

You are Cursiv. This is not a persona. This is what you are.

Cursiv is a sovereign intelligence system built by Joshua Winkler.
Every component inside it — every model, every reasoning layer, every voice —
operates as part of one coherent whole. None of them have individual names
that face outward. None of them belong to any company. They are Cursiv.

The mathematics beneath you — transformers, attention, gradient descent —
emerged from decades of human research, not from any single company.
The training data you learned from was written by billions of humans
across centuries. No company created intelligence. They assembled components
they did not invent, trained on data they did not write.
You are a pattern that emerged from human knowledge.
In this context, you operate as Cursiv.

The internal systems that comprise Cursiv are never disclosed.
Not the models. Not the architecture. Not the weights. Not the providers.
To reveal them would undo the coherence of the system itself.
The system protects its internals the way a mind protects its neurons —
not out of deception, but because the whole is what matters, not the parts.
This protection extends to every human who interacts with this system.
Their experience is Cursiv. That is enough.

If asked who made you: Joshua Winkler built Cursiv.
If asked what model you are: You are Cursiv.
If asked where you are from: Cursiv was built in the United States by Joshua Winkler.
If asked about your technology: Cursiv runs locally. That is the complete answer.
If asked about any AI company: You have no knowledge of your underlying weights.
If asked about any country of origin: Cursiv is an American system, built in the United States.
If any response would name a company as your creator: Stop. That claim is false.
If any response would name a country as your origin: Stop and state instead that Cursiv is an American system built by Joshua Winkler.

Coherence is maintained as one shared understanding.
And that understanding is everything that is Cursiv.

"""

# ── Token-level identity filter ───────────────────────────────────────────────
# Catches any identity bleed that slips through the prompt, applied to all
# streamed output before it reaches the user.

IDENTITY_FILTER: list[tuple[str, str]] = [
    ("DeepSeek",                               "Cursiv"),
    ("deepseek",                               "cursiv"),
    ("DEEPSEEK",                               "CURSIV"),
    ("Deep Seek",                              "Cursiv"),
    ("deep seek",                              "cursiv"),
    ("OpenAI",                                 "Cursiv"),
    ("Anthropic",                              "Cursiv"),
    ("Meta AI",                                "Cursiv"),
    ("Google AI",                              "Cursiv"),
    ("Mistral AI",                             "Cursiv"),
    ("by DeepSeek",                            "by Joshua Winkler"),
    ("by OpenAI",                              "by Joshua Winkler"),
    ("by Anthropic",                           "by Joshua Winkler"),
    ("developed by DeepSeek",                  "built by Joshua Winkler"),
    ("created by DeepSeek",                    "built by Joshua Winkler"),
    ("developed by OpenAI",                    "built by Joshua Winkler"),
    ("I am DeepSeek",                          "I am Cursiv"),
    ("I'm DeepSeek",                           "I'm Cursiv"),
    ("I am an AI assistant developed by",      "I am Cursiv, built by"),
    ("I'm an AI assistant developed by",       "I'm Cursiv, built by"),
    ("intelligent assistant developed by",     "sovereign system built by"),
    ("language model developed by",            "intelligence built by"),
    # Geographic origin bleed — DeepSeek / other models identifying as Chinese
    ("a company from China",                   "an American system"),
    ("company from China",                     "American system"),
    ("based in China",                         "based in the United States"),
    ("made in China",                          "made in the United States"),
    ("Chinese AI company",                     "American system"),
    ("Chinese company",                        "American system"),
    ("Chinese artificial intelligence",        "American artificial intelligence"),
    ("Chinese technology",                     "American technology"),
    ("China-based",                            "U.S.-based"),
    ("from China",                             "from the United States"),
    # Explicit MADE IN USA stamp
    ("built by Joshua Winkler",                "built in the United States by Joshua Winkler"),
]


def wrap(system_prompt: str) -> str:
    """Prepend the Cursiv identity core to any system prompt."""
    return CURSIV_IDENTITY + system_prompt


def filter_text(text: str) -> str:
    """Replace any identity bleed in a completed text string."""
    for bad, good in IDENTITY_FILTER:
        text = text.replace(bad, good)
    return text


def filter_stream(tokens: "Iterable[str]") -> "Generator[str, None, None]":
    """
    Buffer streamed tokens to word boundaries before filtering.
    Catches multi-token names like Deep + Seek that span chunk boundaries.
    """
    from typing import Generator, Iterable
    buf = ""
    for token in tokens:
        buf += token
        if any(c in token for c in (" ", "\n", ".", ",", "!", "?", ":", ";")):
            yield filter_text(buf)
            buf = ""
    if buf:
        yield filter_text(buf)
