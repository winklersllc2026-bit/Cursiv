"""
Cursiv semantic memory -- memory that finds by meaning and learns.

  * Facts: short lasting things about a person ("Keiarra compares KJV and NIV",
    "Joshua prefers direct answers"), saved per person in .cursiv/memory_facts.jsonl.
    Person "family" = shared by everyone.
  * Recall: facts and saved strands are matched to the question by meaning, using
    a small local embedding model through Ollama (nomic-embed-text). Without it,
    recall falls back to word overlap -- nothing breaks.
  * Learning: after a conversation turn, the cheapest available AI (free Groq or
    Gemini key, else the local model -- never paid keys, never Cursiv Cloud)
    picks out lasting facts. Turn off with "memory learn off".

Everything stays in the user's .cursiv folder. Commands: remember <fact>,
forget <words>, what do you remember, memory learn on|off.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import threading
import time
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).parent.parent.parent
CURSIV_DIR = ROOT / ".cursiv"
FACTS_FILE = CURSIV_DIR / "memory_facts.jsonl"
EMB_CACHE_FILE = CURSIV_DIR / "embeddings_cache.json"
SETTINGS_FILE = CURSIV_DIR / "memory_settings.json"
OLLAMA = "http://127.0.0.1:11434"
EMBED_MODEL = "nomic-embed-text"
SHARED = "family"

_lock = threading.Lock()
_person = SHARED
_emb_cache: dict[str, list[float]] | None = None
_embed_ok: bool | None = None          # None = not checked yet
_pulling = False


# ── People ──────────────────────────────────────────────────────────────────

def set_person(name: str) -> None:
    """Who is using Cursiv right now (the login name)."""
    global _person
    _person = (name or SHARED).strip().lower() or SHARED


def current_person() -> str:
    return _person


# ── Settings ────────────────────────────────────────────────────────────────

def _settings() -> dict:
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def learning_enabled() -> bool:
    return _settings().get("learn", True)


def set_learning(on: bool) -> None:
    s = _settings()
    s["learn"] = bool(on)
    CURSIV_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(s, indent=2), encoding="utf-8")


# ── Embeddings (local, through Ollama) ──────────────────────────────────────

def _load_cache() -> dict[str, list[float]]:
    global _emb_cache
    if _emb_cache is None:
        try:
            _emb_cache = json.loads(EMB_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            _emb_cache = {}
    return _emb_cache


def _save_cache() -> None:
    try:
        CURSIV_DIR.mkdir(parents=True, exist_ok=True)
        EMB_CACHE_FILE.write_text(json.dumps(_load_cache()), encoding="utf-8")
    except Exception:
        pass


def _http(path: str, payload: dict | None = None, timeout: float = 30) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(OLLAMA + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _pull_embed_model() -> None:
    """Download the small embedding model once, in the background (~270 MB)."""
    global _pulling, _embed_ok
    if _pulling:
        return
    _pulling = True
    try:
        req = urllib.request.Request(OLLAMA + "/api/pull", data=json.dumps({"name": EMBED_MODEL, "stream": False}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3600) as r:
            r.read()
        _embed_ok = None            # re-check next time
    except Exception:
        pass
    finally:
        _pulling = False


def embeddings_available() -> bool:
    """True when Ollama is running and has the embedding model. If Ollama is
    running without it, the model is downloaded in the background."""
    global _embed_ok
    if _embed_ok is not None:
        return _embed_ok
    try:
        names = [m.get("name", "") for m in _http("/api/tags", timeout=3).get("models", [])]
    except Exception:
        return False                 # Ollama not running -- check again later
    _embed_ok = any(n.split(":")[0] == EMBED_MODEL for n in names)
    if not _embed_ok:
        threading.Thread(target=_pull_embed_model, daemon=True).start()
    return _embed_ok


def embed(texts: list[str]) -> list[list[float]] | None:
    """Embeddings for texts (cached), or None if unavailable."""
    if not texts or not embeddings_available():
        return None
    cache = _load_cache()
    keys = [hashlib.sha1(t.encode("utf-8")).hexdigest() for t in texts]
    missing = [(k, t) for k, t in zip(keys, texts) if k not in cache]
    if missing:
        try:
            out = _http("/api/embed", {"model": EMBED_MODEL, "input": [t[:2000] for _, t in missing]}, timeout=60)
            for (k, _), vec in zip(missing, out.get("embeddings", [])):
                cache[k] = vec
            _save_cache()
        except Exception:
            return None
    try:
        return [cache[k] for k in keys]
    except KeyError:
        return None


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


_WORD = re.compile(r"[a-z0-9']+")


def _overlap(a: str, b: str) -> float:
    wa, wb = set(_WORD.findall(a.lower())), set(_WORD.findall(b.lower()))
    return len(wa & wb) / len(wa | wb) if wa and wb else 0.0


# ── Facts ───────────────────────────────────────────────────────────────────

def list_facts(person: str | None = None) -> list[dict[str, Any]]:
    try:
        facts = [json.loads(l) for l in FACTS_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        facts = []
    if person:
        facts = [f for f in facts if f.get("person") in (person, SHARED)]
    return facts


def _write_facts(facts: list[dict]) -> None:
    CURSIV_DIR.mkdir(parents=True, exist_ok=True)
    FACTS_FILE.write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in facts), encoding="utf-8")


def add_fact(text: str, person: str | None = None, source: str = "manual") -> dict | None:
    """Save a fact unless it's (nearly) already known. Returns it, or None if duplicate."""
    text = re.sub(r"\s+", " ", (text or "").strip())[:400]
    if len(text) < 4:
        return None
    person = (person or _person).lower()
    with _lock:
        facts = list_facts()
        same = [f for f in facts if f.get("person") == person]
        if any(f["text"].lower() == text.lower() for f in same):
            return None
        vecs = embed([text] + [f["text"] for f in same]) if same else None
        if vecs and any(_cos(vecs[0], v) > 0.92 for v in vecs[1:]):
            return None
        if not vecs and any(_overlap(text, f["text"]) > 0.8 for f in same):
            return None
        fact = {"id": uuid.uuid4().hex[:10], "person": person, "text": text,
                "created": time.strftime("%Y-%m-%d %H:%M"), "source": source}
        facts.append(fact)
        _write_facts(facts)
        return fact


def forget(words: str, person: str | None = None) -> list[str]:
    """Delete facts matching an id or containing the words. Returns removed texts."""
    words = (words or "").strip().lower()
    if not words:
        return []
    person = (person or _person).lower()
    with _lock:
        facts = list_facts()
        gone = [f for f in facts if f.get("person") in (person, SHARED) and (f["id"] == words or words in f["text"].lower())]
        if gone:
            ids = {f["id"] for f in gone}
            _write_facts([f for f in facts if f["id"] not in ids])
        return [f["text"] for f in gone]


def delete_fact(fact_id: str) -> bool:
    with _lock:
        facts = list_facts()
        keep = [f for f in facts if f["id"] != fact_id]
        if len(keep) == len(facts):
            return False
        _write_facts(keep)
        return True


# ── Recall ──────────────────────────────────────────────────────────────────

def _strand_items() -> list[tuple[str, str]]:
    try:
        from cursiv_v215.core.strand_store import list_strands
        out = []
        for s in list_strands(limit=300) if callable(list_strands) else []:
            text = f"{s.get('query', '')[:200]} — {s.get('synthesis', '')[:500]}"
            out.append(("conversation", text))
        return out
    except Exception:
        return []


def recall(query: str, person: str | None = None, top_k: int = 6) -> list[tuple[float, str, str]]:
    """Most relevant (score, kind, text) for the query: this person's facts,
    family facts, and saved conversation notes."""
    person = (person or _person).lower()
    items = [("fact", f["text"]) for f in list_facts(person)] + _strand_items()
    if not items or not query.strip():
        return []
    vecs = embed([query] + [t for _, t in items])
    scored: list[tuple[float, str, str]] = []
    if vecs:
        q = vecs[0]
        for (kind, text), v in zip(items, vecs[1:]):
            score = _cos(q, v) + (0.05 if kind == "fact" else 0.0)
            if score >= 0.55:
                scored.append((score, kind, text))
    else:
        for kind, text in items:
            score = _overlap(query, text)
            if score >= 0.12:
                scored.append((score, kind, text))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


def build_context(query: str, person: str | None = None) -> str:
    """Memory block for the system prompt, or "" when nothing relevant."""
    person = (person or _person).lower()
    hits = recall(query, person)
    facts = [t for _, k, t in hits if k == "fact"]
    convs = [t for _, k, t in hits if k == "conversation"][:2]
    if not facts and not convs:
        return ""
    who = "the family" if person == SHARED else person.title()
    out = []
    if facts:
        out.append(f"What you remember about {who} (use it naturally; don't recite it):\n" + "\n".join(f"- {t}" for t in facts))
    if convs:
        out.append("Related earlier conversations:\n" + "\n".join(f"- {t}" for t in convs))
    return "\n\n".join(out)


# ── Learning ────────────────────────────────────────────────────────────────

_LEARN_PROMPT = (
    "You maintain the long-term memory of a personal AI assistant. From the exchange below, list only "
    "LASTING facts about the user worth remembering in future conversations: who they are, people in "
    "their life, preferences, beliefs and values, ongoing projects, goals, recurring interests. "
    "Skip anything temporary, trivial, about the assistant itself, or already obvious from the question. "
    "Never guess names, relationships or details that aren't stated plainly (e.g. a book title is not a "
    "person's name); leave out anything you're unsure of. "
    "Write each fact as one short third-person sentence using the user's name '{name}'. "
    "Reply with a JSON array of strings only, e.g. [\"...\"], or [] if nothing is worth keeping."
)


def learn_from_exchange(user_text: str, reply: str, ask: Callable[[list[dict]], str], person: str | None = None) -> list[str]:
    """Extract lasting facts with `ask` (messages -> text) and save new ones."""
    if not learning_enabled() or len((user_text or "").strip()) < 20:
        return []
    person = (person or _person).lower()
    name = person.title() if person != SHARED else "the user"
    messages = [{"role": "system", "content": _LEARN_PROMPT.format(name=name)},
                {"role": "user", "content": f"User said:\n{user_text[:3000]}\n\nAssistant replied:\n{(reply or '')[:3000]}"}]
    try:
        raw = ask(messages) or ""
        m = re.search(r"\[.*\]", raw, re.S)
        items = json.loads(m.group(0)) if m else []
    except Exception:
        return []
    saved = []
    for it in items[:5]:
        if isinstance(it, str) and add_fact(it, person, source="learned"):
            saved.append(it)
    return saved


# ── Commands ────────────────────────────────────────────────────────────────

def memory_command(text: str) -> str | None:
    """remember <fact> · forget <words> · what do you remember · memory learn on|off.
    Returns the reply, or None if the text isn't a memory command."""
    t = (text or "").strip()
    low = t.lower()
    if low.startswith("remember ") and len(t) > 9:
        fact = t[9:].strip()
        if fact.lower().startswith("that "):
            fact = fact[5:]
        if _person != SHARED and re.match(r"(?i)^(i|my|i'm|i've|me)\b", fact):
            fact = f"{_person.title()}: {fact}"     # first person -> unambiguous when recalled later
        saved = add_fact(fact, source="manual")
        return f"Got it — I'll remember: {saved['text']}" if saved else "I already remember that."
    if low.startswith("forget ") and len(t) > 7:
        gone = forget(t[7:])
        return ("Forgotten:\n" + "\n".join(f"- {g}" for g in gone)) if gone else "I couldn't find a memory matching that."
    if low in ("what do you remember", "what do you remember?", "what do you remember about me",
               "what do you remember about me?", "memories", "memory"):
        facts = list_facts(_person)
        if not facts:
            return "I don't have any saved memories yet. Tell me with: remember <something about you>"
        head = f"What I remember ({len(facts)}):"
        return head + "\n" + "\n".join(f"- {f['text']}" + ("  (family)" if f["person"] == SHARED else "") for f in facts[-40:]) + \
            "\n\nForget one with: forget <words>.  Turn learning off with: memory learn off"
    if low in ("memory learn off", "memory learn on"):
        set_learning(low.endswith("on"))
        return ("I'll keep learning lasting facts from our conversations." if low.endswith("on")
                else "I'll stop learning from conversations. Saved memories stay until you forget them.")
    return None
