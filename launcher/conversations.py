"""
Saved conversations -- kept per person in %USERPROFILE%\\.cursiv\\conversations\\.

Each file holds the messages (so Cursiv can continue with full context) and the
transcript as shown on screen (so council output, translations etc. reappear
exactly). Nothing is saved unless the user chooses to.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

DIR = Path.home() / ".cursiv" / "conversations"


def _person() -> str:
    try:
        from cursiv_v215.memory import semantic
        return semantic.current_person()
    except Exception:
        return "family"


def title_from(messages: list[dict]) -> str:
    first = next((m.get("content", "") for m in messages if m.get("role") == "user" and m.get("content")), "")
    first = " ".join(str(first).split())
    return (first[:48] + "…") if len(first) > 48 else (first or "New conversation")


def save(conv_id: str | None, messages: list[dict], html: str, title: str | None = None) -> str:
    DIR.mkdir(parents=True, exist_ok=True)
    conv_id = conv_id or uuid.uuid4().hex[:12]
    path = DIR / f"{conv_id}.json"
    existing = load(conv_id) or {}
    data = {
        "id": conv_id,
        "person": existing.get("person") or _person(),
        "title": title or existing.get("title") or title_from(messages),
        "created": existing.get("created") or time.time(),
        "updated": time.time(),
        "messages": messages,
        "html": html,
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
    return conv_id


def load(conv_id: str) -> dict | None:
    try:
        return json.loads((DIR / f"{conv_id}.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def list_all() -> list[dict]:
    """This person's conversations, newest first (without the bulky fields)."""
    person = _person()
    out = []
    for f in DIR.glob("*.json") if DIR.exists() else []:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("person", person) != person:
            continue
        out.append({"id": d["id"], "title": d.get("title", "Conversation"), "updated": d.get("updated", 0)})
    return sorted(out, key=lambda c: c["updated"], reverse=True)


def rename(conv_id: str, title: str) -> None:
    d = load(conv_id)
    if d and title.strip():
        d["title"] = title.strip()[:80]
        (DIR / f"{conv_id}.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def delete(conv_id: str) -> None:
    (DIR / f"{conv_id}.json").unlink(missing_ok=True)
