"""
Cursiv — chat panel command router.

The terminal CLI (cursiv_v215/ui/chat_cli.py) has ~40 built-in commands
(key management, council deliberation, Babel translation, strand memory,
Codex/Hermes agents, blast-to-board, Obsidian sync, substrate, etc.) all
built directly against terminal I/O -- print() with ANSI codes, input()
for prompts. This module ports the ROUTING + the calls to the same
underlying functions (babel_agent, codex_agent, async_council, strand
store, postal, etc.) to a UI-agnostic form the GUI chat panel can render,
without touching or duplicating the terminal CLI itself.

Not ported here (need a genuinely different widget, not a text command):
  - voice / listen        -- needs a microphone record/stop control
  - image / paste         -- need an image-display widget
  - write to / letters /
    postal *              -- multi-line compose + PIN-entry dialogs
  - legacy *               -- same, family-letter vault has its own PIN flow
These still work from the terminal (Open in Terminal button).

Everything else -- key/openai/anthropic, files, workspace, mode, tier,
offline, governor, status, codex, hermes, council/full/deliberate,
anchor this, strands/remember, grow, ref, search, pull, rate, funforge
(start/done/extend), babel, blast, substrate, obsidian, grok/claude
direct retry, overseer, "hey <provider>" routing -- is handled here,
calling the exact same lower-level functions the CLI calls.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Generator, Optional

_HERE = Path(__file__).parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from cursiv_v215.ui.chat_app import (
    chat as _chat,
    ROOT as _CHAT_ROOT,
    RATE_SENTINEL,
    _call_ollama,
    _call_xai_stream,
    _call_claude_direct,
    _call_openai_direct,
    _call_provider_council,
    _web_search,
)

try:
    from cursiv_v215.ui.chat_cli import _save_key, _probe_xai, _probe_openai, _probe_claude
except Exception:
    def _save_key(field, value): pass
    def _probe_xai(key): return None
    def _probe_openai(key): return None
    def _probe_claude(key): return None

try:
    from cursiv_v215.agents.babel_agent import is_babel_command as _babel_detect, extract_babel_input as _babel_input
    _BABEL_OK = True
except Exception:
    _BABEL_OK = False
    def _babel_detect(t): return False
    def _babel_input(t): return ""

try:
    from cursiv_v215.agents.codex_agent import generate as _codex_gen, is_available as _codex_avail
    _CODEX_OK = True
except Exception:
    _CODEX_OK = False
    def _codex_gen(p): return ""
    def _codex_avail(): return False

try:
    from cursiv_v215.agents.hermes_agent import run as _hermes_run, is_available as _hermes_avail
    _HERMES_OK = True
except Exception:
    _HERMES_OK = False
    def _hermes_run(p): return ""
    def _hermes_avail(): return False

try:
    from cursiv_v215.agents.reference_brain import answer as _ref_answer, is_available as _ref_avail
    _REF_OK = True
except Exception:
    _REF_OK = False
    def _ref_answer(q): return ""
    def _ref_avail(): return False

try:
    from cursiv_v215.council.async_council import run_council as _async_council_run, council_available as _async_council_ok
    _ASYNC_COUNCIL_OK = True
except Exception:
    _ASYNC_COUNCIL_OK = False
    def _async_council_run(q, cfg, **kw): return None
    def _async_council_ok(cfg): return False

try:
    from cursiv_v215.core.strand_store import (
        save_strand as _strand_save,
        list_strands as _strand_list,
        search_strands as _strand_search,
        format_strand_list as _strand_fmt,
        strand_count as _strand_count,
        territory_counts as _strand_terr_counts,
        load_territories as _strand_territories,
    )
    _STRAND_OK = True
except Exception:
    _STRAND_OK = False
    def _strand_save(*a, **kw): return ""
    def _strand_list(**kw): return []
    def _strand_search(q, **kw): return []
    def _strand_fmt(s): return ""
    def _strand_count(): return 0
    def _strand_terr_counts(): return {}
    def _strand_territories(): return {}

try:
    from cursiv_v215.web.board_client import (
        board_login as _board_login,
        board_register as _board_register,
        board_logout as _board_logout,
        board_whoami as _board_whoami,
        board_blast as _board_blast,
    )
    _BOARD_OK = True
except Exception:
    _BOARD_OK = False
    def _board_login(u, p): return (False, "board client unavailable")
    def _board_register(u, p): return (False, "board client unavailable")
    def _board_logout(): pass
    def _board_whoami(): return None
    def _board_blast(t, s): return (False, "board client unavailable")

try:
    from cursiv_v215.obsidian.exporter import (
        load_config as _obs_load_config,
        save_config as _obs_save_config,
        export_today as _obs_export,
    )
    _OBS_OK = True
except Exception:
    _OBS_OK = False
    def _obs_load_config(): return {"enabled": False, "vault_path": ""}
    def _obs_save_config(e, p): pass
    def _obs_export(vp, d=None): return (False, "Obsidian module unavailable.")

try:
    from cursiv_v215.substrate.activator import get_activator as _get_activator
    _SUBSTRATE_OK = True
except Exception:
    _SUBSTRATE_OK = False
    def _get_activator(): return None

try:
    from cursiv_v215.memory.session_log import append_exchange as _session_append
except Exception:
    def _session_append(u, a, m="unknown"): pass

try:
    from cursiv_v215.postal.sealed_store import (
        seal_letter as _postal_seal,
        open_letter as _postal_open,
        get_sealed_entry as _postal_entry,
        get_sig_status as _postal_sig_status,
        letters_for as _postal_for,
        letters_from as _postal_from,
        all_letters as _postal_all,
        export_sealpack as _postal_export,
        import_sealpack as _postal_import,
    )
    from cursiv_v215.postal.council_reader import council_walkthrough as _postal_council
    from cursiv_v215.postal.user_registry import (
        setup_identity as _postal_setup,
        my_identity as _postal_my_id,
        add_contact as _postal_add_contact,
        remove_contact as _postal_rm_contact,
        list_contacts as _postal_contacts,
        resolve_recipient as _postal_resolve,
        rotate_identity as _postal_rotate,
        key_rotation_history as _postal_key_history,
    )
    _POSTAL_OK = True
except Exception:
    _POSTAL_OK = False
    def _postal_seal(**kw): return ""
    def _postal_open(i): return None
    def _postal_entry(i): return None
    def _postal_sig_status(i): return "unknown"
    def _postal_for(k): return []
    def _postal_from(k): return []
    def _postal_all(): return []
    def _postal_export(i): return None
    def _postal_import(f, p): return None
    def _postal_council(i, u, c, **kw): return "[Postal module unavailable]"
    def _postal_setup(n): return {}
    def _postal_my_id(): return None
    def _postal_add_contact(n, k): return {}
    def _postal_rm_contact(n): return False
    def _postal_contacts(): return []
    def _postal_resolve(n): return None
    def _postal_rotate(reason="", **kw): return {}
    def _postal_key_history(): return []

try:
    from cursiv_v215.family.family_profiles import detect_family_member as _fam_detect
    from cursiv_v215.family.legacy_store import (
        letters_waiting_for as _legacy_letters_for,
        letters_written_by as _legacy_letters_by,
        get_letter_content as _legacy_get_content,
        save_letter as _legacy_save,
        rewrite_letter as _legacy_rewrite,
        delete_letter as _legacy_delete,
        name_to_key as _legacy_name_to_key,
        export_pack as _legacy_export_pack,
        import_pack as _legacy_import_pack,
        open_folder as _legacy_open_folder,
    )
    from cursiv_v215.family.family_profiles import (
        pin_is_set as _fam_pin_is_set,
        verify_pin as _fam_verify_pin,
    )
    _LEGACY_OK = True
except Exception:
    _LEGACY_OK = False
    def _fam_detect(n, d): return None
    def _fam_pin_is_set(k): return False
    def _fam_verify_pin(k, p): return False
    def _legacy_letters_for(k): return []
    def _legacy_letters_by(k): return []
    def _legacy_get_content(i): return None
    def _legacy_save(**kw): return ""
    def _legacy_rewrite(i, c): return False
    def _legacy_delete(i): return False
    def _legacy_name_to_key(n): return n.lower().split()[0] if n.split() else ""
    def _legacy_export_pack(k, d): return (Path("."), 0)
    def _legacy_import_pack(f): return (0, [])
    def _legacy_open_folder(p): pass

try:
    from cursiv_v215.agents.voice_agent import (
        record as _voice_record,
        transcribe_raw as _voice_transcribe,
        is_available as _voice_avail,
        stt_backend as _voice_stt_backend,
        capture_backend as _voice_cap_backend,
        VOICE_CLEAN_SYSTEM as _VOICE_CLEAN_SYS,
    )
    _VOICE_OK = True
except Exception:
    _VOICE_OK = False
    def _voice_record(duration_s=5.0, status_cb=None): return b"", None
    def _voice_transcribe(pcm, float32_arr=None, status_cb=None): return ""
    def _voice_avail(): return False
    def _voice_stt_backend(): return "none"
    def _voice_cap_backend(): return "none"
    _VOICE_CLEAN_SYS = ""

try:
    from cursiv_v215.agents.babel_agent import (
        encode_to_binary as _babel_encode,
        decode_from_binary as _babel_decode,
    )
except Exception:
    def _babel_encode(t): return b""
    def _babel_decode(b): return ""


# ── Result types ─────────────────────────────────────────────────────────

class TextResult:
    """A complete, ready-to-show result -- no streaming."""
    def __init__(self, text: str, image_path: str = ""):
        self.text = text
        self.image_path = image_path   # set for image-generation/paste results


class StreamResult:
    """An intro line shown immediately, then a generator streamed in."""
    def __init__(
        self,
        intro: str,
        generator: Generator[str, None, None],
        on_complete: Optional[Callable[[str], None]] = None,
    ):
        self.intro = intro
        self.generator = generator
        self.on_complete = on_complete


def _default_cfg() -> dict:
    """Same shape as chat_cli.py's cfg dict, minus the terminal-only fields."""
    return {
        "file_access":      False,
        "confirm_mode":     "auto",   # GUI has no write-confirm prompt loop (yet) -- default to auto
        "funforge_session": None,
        "workspace":        str(_CHAT_ROOT),
        "obsidian_enabled": False,
        "obsidian_path":    "",
        "overseer_mode":    False,
        "trust_tier":       3,
        "offline_mode":     False,
        "cursiv_mode":      "personal",
        "last_user_msg":    "",
        "_last_council_synthesis": "",
        "_last_council_query":     "",
    }


def _auto_territory(q: str) -> str:
    ql = q.lower()
    if any(w in ql for w in ["code", "function", "python", "debug", "build", "error", "syntax", "class", "codex"]):
        return "coding"
    if any(w in ql for w in ["health", "recovery", "feel", "mental", "grounding", "medication", "episode"]):
        return "recovery"
    if any(w in ql for w in ["design", "system", "architecture", "cursiv", "agent", "strand", "council", "guardian"]):
        return "architecture"
    if any(w in ql for w in ["music", "creative", "story", "forge", "art", "write", "poem", "song"]):
        return "creative"
    if any(w in ql for w in ["research", "history", "world", "science", "civilization"]):
        return "worldmodel"
    return "general"


_LANG_NAMES = {
    "mandarin": "Mandarin Chinese", "chinese": "Mandarin Chinese", "korean": "Korean",
    "russian": "Russian", "spanish": "Spanish", "french": "French", "german": "German",
    "japanese": "Japanese", "arabic": "Arabic", "hindi": "Hindi", "portuguese": "Portuguese",
    "italian": "Italian", "turkish": "Turkish", "dutch": "Dutch", "polish": "Polish",
    "vietnamese": "Vietnamese", "thai": "Thai", "hebrew": "Hebrew", "greek": "Greek",
    "swedish": "Swedish", "ukrainian": "Ukrainian", "farsi": "Persian (Farsi)",
    "persian": "Persian (Farsi)", "tagalog": "Tagalog",
}


def _cascade_gen(cfg: dict, messages: list[dict], max_tokens: int = 900):
    """Same provider-preference order the CLI's grow/babel-outbound commands use."""
    ant, xai, oai = cfg.get("anthropic_key", ""), cfg.get("api_key", ""), cfg.get("openai_key", "")
    if ant:
        return _call_claude_direct(messages, ant), "Claude"
    if xai:
        return _call_xai_stream(messages, xai, False), "xAI"
    if oai:
        return _call_openai_direct(messages, oai), "OpenAI"
    return _call_ollama(messages, max_tokens=max_tokens), "Ollama"


def handle_command(raw: str, cfg: dict, history: list[dict]) -> Optional[TextResult | StreamResult]:
    """
    Returns None if `raw` isn't a recognized built-in command -- caller
    should fall through to a plain chat() call in that case.
    """
    text = raw.strip()
    if not text:
        return None
    cmd = text.lower()

    # ── Simple state toggles ────────────────────────────────────────────
    if cmd == "status":
        lines = [
            f"xAI key:       {'set' if cfg.get('api_key') else 'not set'}",
            f"OpenAI key:    {'set' if cfg.get('openai_key') else 'not set'}",
            f"Anthropic key: {'set' if cfg.get('anthropic_key') else 'not set'}",
            f"File access:   {'ON' if cfg.get('file_access') else 'OFF'}",
            f"Trust tier:    {cfg.get('trust_tier', 3)}",
            f"Offline mode:  {'ON' if cfg.get('offline_mode') else 'OFF'}",
            f"Cursiv mode:   {cfg.get('cursiv_mode', 'personal')}",
            f"Overseer:      {'ON' if cfg.get('overseer_mode') else 'OFF'}",
            f"Workspace:     {cfg.get('workspace', '')}",
        ]
        return TextResult("\n".join(lines))

    if cmd in ("tier 1", "tier 2", "tier 3"):
        cfg["trust_tier"] = int(cmd[-1])
        labels = {1: "SOVEREIGN OFFLINE (Ollama only)", 2: "LOCAL + LIMITED", 3: "FULL COUNCIL"}
        return TextResult(f"Trust tier → {cfg['trust_tier']} — {labels[cfg['trust_tier']]}")

    if cmd in ("offline on", "offline off"):
        cfg["offline_mode"] = cmd == "offline on"
        if cfg["offline_mode"]:
            cfg["trust_tier"] = 1
            return TextResult("Offline sovereign mode ON — all external APIs blocked, tier forced to 1.")
        return TextResult("Offline mode OFF — external routing restored.")

    if cmd in ("governor on", "governor off", "governor"):
        if cmd == "governor off":
            cfg["cursiv_mode"] = "personal"
            return TextResult("Governor mode OFF → Personal mode.")
        cfg["cursiv_mode"] = "governor"
        return TextResult(
            "GOVERNOR MODE ENGAGED — constitutional enforcement elevated. "
            "Responses will be formal and constitutionally grounded. "
            "Type 'governor off' to return to personal mode."
        )

    if cmd in ("files on", "files off"):
        cfg["file_access"] = cmd == "files on"
        return TextResult(f"File access → {'ON' if cfg['file_access'] else 'OFF'}")

    if cmd in ("overseer on", "overseer off"):
        if cmd == "overseer on":
            if not cfg.get("anthropic_key"):
                return TextResult("Overseer needs an Anthropic key for Claude. Type: anthropic sk-ant-xxxxx")
            if not (cfg.get("api_key") or cfg.get("openai_key")):
                return TextResult("Overseer needs a Grok/OpenAI key as the primary model. Type: key xai-xxxxx")
            cfg["overseer_mode"] = True
            return TextResult("Overseer mode → ON. Grok generates, Claude reviews every response.")
        cfg["overseer_mode"] = False
        return TextResult("Overseer mode → OFF. Normal routing restored.")

    if cmd.startswith("workspace"):
        new_ws = text[9:].strip()
        if not new_ws:
            return TextResult(f"Workspace: {cfg.get('workspace', '')}")
        ws_path = Path(new_ws).expanduser().resolve()
        if not ws_path.exists() or not ws_path.is_dir():
            return TextResult(f"Not a valid directory: {new_ws}")
        cfg["workspace"] = str(ws_path)
        return TextResult(f"Workspace → {ws_path}")

    # ── API keys ─────────────────────────────────────────────────────────
    if cmd.startswith("key "):
        new_key = text[4:].strip()
        if new_key.startswith(("sk-", "sk_")):
            cfg["openai_key"] = new_key
            _save_key("openai_key", new_key)
            live = _probe_openai(new_key)
            return TextResult(
                "That's an OpenAI key — routed to the OpenAI slot.\n"
                f"OpenAI: {'connected' if live else 'unreachable'}"
            )
        cfg["api_key"] = new_key
        _save_key("api_key", new_key)
        live = _probe_xai(new_key)
        return TextResult(f"xAI: {'connected' if live else 'unreachable'}")

    if cmd.startswith("openai "):
        new_key = text[7:].strip()
        if new_key.startswith("xai-"):
            cfg["api_key"] = new_key
            _save_key("api_key", new_key)
            return TextResult(f"That's an xAI key — routed to the xAI slot. {'connected' if _probe_xai(new_key) else 'unreachable'}")
        if new_key.startswith("sk-ant-"):
            cfg["anthropic_key"] = new_key
            _save_key("anthropic_key", new_key)
            return TextResult(f"That's an Anthropic key — routed to the Anthropic slot. {'connected' if _probe_claude(new_key) else 'unreachable'}")
        cfg["openai_key"] = new_key
        _save_key("openai_key", new_key)
        return TextResult(f"OpenAI: {'connected' if _probe_openai(new_key) else 'unreachable'}")

    if cmd.startswith("anthropic "):
        new_key = text[10:].strip()
        if new_key.startswith("xai-"):
            cfg["api_key"] = new_key
            _save_key("api_key", new_key)
            return TextResult(f"That's an xAI key — routed to the xAI slot. {'connected' if _probe_xai(new_key) else 'unreachable'}")
        if new_key.startswith("sk-") and not new_key.startswith("sk-ant-"):
            cfg["openai_key"] = new_key
            _save_key("openai_key", new_key)
            return TextResult(f"That's an OpenAI key — routed to the OpenAI slot. {'connected' if _probe_openai(new_key) else 'unreachable'}")
        cfg["anthropic_key"] = new_key
        _save_key("anthropic_key", new_key)
        return TextResult(f"Claude: {'connected' if _probe_claude(new_key) else 'unreachable'}")

    # ── Codex / Hermes / Reference Brain ────────────────────────────────
    if cmd == "codex" or cmd.startswith("codex "):
        if not _CODEX_OK or not _codex_avail():
            return TextResult("Codex Agent not available — set CURSIV_CODEX_PATH or place Winkler_Codex_AI as a sibling to Cursiv-v3.")
        prompt = text[6:].strip()
        if not prompt:
            return TextResult("Usage: codex <what to build>")
        result = _codex_gen(prompt)
        _session_append(prompt, result, "codex_agent")
        return TextResult(result)

    if cmd == "hermes" or cmd.startswith("hermes "):
        if not _HERMES_OK or not _hermes_avail():
            return TextResult("Hermes Agent not available — needs Ollama running.")
        prompt = text[7:].strip()
        if not prompt:
            return TextResult("Usage: hermes <task to run>")
        result = _hermes_run(prompt)
        _session_append(prompt, result, "hermes_agent")
        return TextResult(result)

    if cmd == "ref" or cmd.startswith("ref "):
        if not _REF_OK or not _ref_avail():
            return TextResult("Reference Brain not available.")
        query = text[4:].strip()
        if not query:
            return TextResult("Usage: ref <question>")
        return TextResult(_ref_answer(query))

    # ── Council ──────────────────────────────────────────────────────────
    if (cmd == "council" or cmd.startswith("council ")
            or cmd == "/full" or cmd.startswith("/full ")
            or cmd == "/deliberate" or cmd.startswith("/deliberate ")):
        force_full = cmd.startswith(("/full", "/deliberate"))
        for prefix in ("council ", "/full ", "/deliberate "):
            if cmd.startswith(prefix):
                question = text[len(prefix):].strip()
                break
        else:
            question = ""
        if not question:
            return TextResult("Usage: council <question>  ·  /full <question> for complete deliberation")
        if _ASYNC_COUNCIL_OK:
            def _run():
                result = _async_council_run(question, cfg, force_full=True if force_full else None)
                if result is not None:
                    yield result.synthesis
                    cfg["_last_council_synthesis"] = result.synthesis
                    cfg["_last_council_query"] = question
            def _finish(full: str):
                _session_append(question, full, "async_council")
                if _STRAND_OK and full and len(full) > 100:
                    _strand_save(question, full, tags=["council", "async"], score=0.80,
                                 territory_tag="worldmodel", source="async_council", model="council_synthesis")
            return StreamResult(f"⬡ Council deliberating — {question[:60]}", _run(), _finish)
        if not (cfg.get("api_key") or cfg.get("openai_key") or cfg.get("anthropic_key")):
            return TextResult("Council requires at least one API key.")
        def _finish2(full: str):
            cfg["_last_council_synthesis"] = full
            _session_append(question, full, "group_discovery")
        return StreamResult(
            f"⬡ Group discovery — {question[:60]}",
            _call_provider_council(question, cfg.get("api_key", ""), cfg.get("openai_key", ""), cfg.get("anthropic_key", "")),
            _finish2,
        )

    # ── Strand memory ────────────────────────────────────────────────────
    if cmd == "anchor this" or cmd.startswith("anchor this "):
        if not _STRAND_OK:
            return TextResult("Strand store unavailable.")
        parts = cmd.split()
        territory = parts[2] if len(parts) >= 3 else "general"
        if territory != "general" and territory not in _strand_territories():
            territory = "general"
        if not history:
            return TextResult("No session history to anchor.")
        last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        last_ai = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), "")
        if not (last_user or last_ai):
            return TextResult("Nothing to anchor yet — send a message first.")
        sid = _strand_save(last_user, last_ai, tags=["anchor"], score=0.85,
                            territory_tag=territory, source="anchor", model="gui")
        return TextResult(f"⬡ Anchored → Strand {sid}" + (f"  [{territory}]" if territory != "general" else ""))

    if cmd == "strands" or cmd.startswith("strands "):
        if not _STRAND_OK:
            return TextResult("Strand store unavailable.")
        sub = text[8:].strip() if cmd.startswith("strands ") else ""
        if sub.startswith("search "):
            q = sub[7:].strip()
            if not q:
                return TextResult("Usage: strands search <query>")
            return TextResult(f"⬡ Strand search — {q}\n\n" + (_strand_fmt(_strand_search(q)) or "No matches."))
        if sub and sub in _strand_territories():
            results = _strand_list(territory=sub, limit=20)
            return TextResult(f"⬡ Strands [{sub}] ({len(results)} found)\n\n" + (_strand_fmt(results) or "None yet."))
        total = _strand_count()
        counts = _strand_terr_counts()
        recent = _strand_list(limit=8)
        counts_line = "  ".join(f"{t}:{n}" for t, n in counts.items()) if counts else "none yet"
        out = f"⬡ Strand Archive — {total} total\n{counts_line}"
        if recent:
            out += "\n\n" + _strand_fmt(recent)
        return TextResult(out)

    if cmd.startswith("remember ") or cmd == "remember":
        if not _STRAND_OK:
            return TextResult("Strand store unavailable.")
        q = text[9:].strip()
        if not q:
            return TextResult("Usage: remember <query>")
        results = _strand_search(q, top_k=5, min_score=0.08)
        if not results:
            return TextResult("No matching strands found. Anchor exchanges with: anchor this")
        return TextResult(f"⬡ Local memory — {q}\n\n" + _strand_fmt(results))

    if cmd.startswith("rate"):
        parts = cmd.split()
        score = None
        if len(parts) >= 2:
            tok = parts[1]
            if tok == "good":
                score = 5
            elif tok == "bad":
                score = 1
            elif tok.isdigit() and 1 <= int(tok) <= 5:
                score = int(tok)
        if score is None:
            return TextResult("Usage: rate good  ·  rate bad  ·  rate 1-5")
        if not history:
            return TextResult("No exchange to rate yet.")
        return TextResult(f"Rated {'★' * score}{'☆' * (5 - score)}  ({score}/5)")

    # ── Grow (self-referential code evolution) ─────────────────────────
    if cmd == "grow" or cmd.startswith("grow "):
        sub = text[5:].strip()
        if not sub:
            return TextResult("Usage: grow <filepath>  ·  grow system")
        if sub.lower() == "system":
            gen, label = _cascade_gen(cfg, [
                {"role": "system", "content": (
                    "You are a systems architect reviewing the Cursiv AI OS. "
                    "Identify the single most valuable capability that is clearly "
                    "missing or half-built and write a Python module stub for it "
                    "(filename, docstring, key functions with signatures). No filler."
                )},
                {"role": "user", "content": "Suggest the next capability for this system."},
            ], max_tokens=1200)
            def _finish(full):
                if _STRAND_OK and full:
                    _strand_save("grow system", full, tags=["grow", "system"], score=0.80,
                                 territory_tag="architecture", source="grow", model=label)
            return StreamResult(f"⬡ Grow — system level (via {label})", gen, _finish)
        gpath = Path(sub)
        if not gpath.is_absolute():
            gpath = Path(cfg.get("workspace", str(_CHAT_ROOT))) / sub
        if not gpath.exists():
            return TextResult(f"File not found: {sub}")
        try:
            code = gpath.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return TextResult(f"Read error: {e}")
        gen, label = _cascade_gen(cfg, [
            {"role": "system", "content": (
                "You are a code evolution engine. Study this file's style and "
                "patterns, then write the next logical addition -- same voice, "
                "same conventions. Output only the new code, no explanation."
            )},
            {"role": "user", "content": code},
        ], max_tokens=1200)
        return StreamResult(f"⬡ Grow — {sub} (via {label})", gen)

    # ── Babel translation ────────────────────────────────────────────────
    if _BABEL_OK and (cmd == "babel" or (cmd.startswith("babel") and len(cmd) > 5 and cmd[5] in (" ", ":"))):
        raw_input = _babel_input(text)
        if not raw_input:
            return TextResult("Usage: babel <text in any language>  ·  babel <text> into <language(s)>")
        into_match = re.search(r"\s+into\s+(.+)$", raw_input, re.IGNORECASE)
        if into_match and not re.match(r"^i\s+am\b", raw_input, re.IGNORECASE):
            src = raw_input[:into_match.start()].strip()
            langs = [l.strip().rstrip(",;") for l in re.split(r"[\s,]+", into_match.group(1).strip()) if l.strip()]
            if src and langs:
                targets = [_LANG_NAMES.get(l.lower(), l.title()) for l in langs]
                gen, label = _cascade_gen(cfg, [
                    {"role": "system", "content": (
                        "You are a precise translation engine. Translate the user's text "
                        "into each requested language. For each, output a header line "
                        "exactly like:\n  ── [Language Name] ──\nfollowed by the translation. "
                        "Return translations only, no explanations."
                    )},
                    {"role": "user", "content": f"Text to translate:\n{src}\n\nTranslate into: {', '.join(targets)}"},
                ], max_tokens=800)
                return StreamResult(f"⬡ Babel — English → {', '.join(targets)} (via {label})", gen)
        gen, label = _cascade_gen(cfg, [
            {"role": "system", "content": "Translate the following text to English. Return only the translation, nothing else."},
            {"role": "user", "content": raw_input},
        ], max_tokens=500)
        return StreamResult(f"⬡ Babel → English (via {label})", gen)

    # ── Web search + synthesis ───────────────────────────────────────────
    if cmd.startswith("search:") or cmd.startswith("search "):
        query = text[7:].strip()
        if not query:
            return TextResult("Usage: search <query>")
        results = _web_search(query)
        if not results:
            return TextResult("No web results found. Check internet connection or try a different query.")
        gen = _chat(
            f"search: {query}", history,
            cfg.get("api_key", ""), None, cfg.get("file_access", False),
            cfg.get("workspace", str(_CHAT_ROOT)), cfg.get("openai_key", ""),
            False, cfg.get("anthropic_key", ""),
        )
        return StreamResult(f"⊕ Web search — {query}\n\n{results}\n", gen)

    # ── Page pull ────────────────────────────────────────────────────────
    if cmd.startswith("pull "):
        url = text[5:].strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            import urllib.request as _pur
            req = _pur.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Cursiv/3.14)"})
            with _pur.urlopen(req, timeout=12) as resp:
                raw_html = resp.read(65_536).decode("utf-8", errors="replace")
            body = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", raw_html, flags=re.IGNORECASE)
            body = re.sub(r"<[^>]+>", " ", body)
            body = re.sub(r"&[a-zA-Z]{2,6};", " ", body)
            body = re.sub(r"\s+", " ", body).strip()[:4000]
        except Exception as e:
            return TextResult(f"Fetch failed: {e}")
        if len(body) < 80:
            return TextResult("Page returned too little text — may require JavaScript.")
        gen, label = _cascade_gen(cfg, [
            {"role": "user", "content": (
                f"URL: {url}\n\nContent:\n{body}\n\n"
                "Analyze this page. Give: 1) core thesis, 2) key facts worth remembering, "
                "3) any connection to current work. Be precise, no filler."
            )},
        ], max_tokens=800)
        def _finish(full):
            if _STRAND_OK and full:
                _strand_save(f"pull: {url}", full, tags=["pull", "web"], score=0.72,
                             territory_tag="worldmodel", source="pull", model=label)
        return StreamResult(f"⬡ Page pull — {url[:70]} (via {label})", gen, _finish)

    # ── FunForge ─────────────────────────────────────────────────────────
    if cmd in ("forge done", "forge close"):
        ff = cfg.get("funforge_session")
        if not ff:
            return TextResult("No active FunForge session.")
        gen = _chat(
            "Let's close this creative spike. Synthesize what we made into a final artifact.",
            history, cfg.get("api_key", ""), None, False, cfg.get("workspace", str(_CHAT_ROOT)),
            cfg.get("openai_key", ""), False, cfg.get("anthropic_key", ""),
        )
        cfg["funforge_session"] = None
        return StreamResult("⬡ FunForge closing — producing artifact", gen)

    if cmd.startswith("funforge") or cmd.startswith("spike "):
        topic = text[len("funforge"):].strip() if cmd.startswith("funforge") else text[6:].strip()
        topic = topic or "open-ended creative spike"
        cfg["funforge_session"] = {"topic": topic, "started": datetime.now()}
        gen = _chat(
            f"[FUNFORGE] Playful 45-minute creative spike. Topic: {topic}. "
            "Respond playfully and start the creative spike.",
            history, cfg.get("api_key", ""), None, False, cfg.get("workspace", str(_CHAT_ROOT)),
            cfg.get("openai_key", ""), False, cfg.get("anthropic_key", ""),
        )
        return StreamResult(f"⬡ FunForge active — {topic}  (type 'forge done' when finished)", gen)

    # ── Blast (public board) ────────────────────────────────────────────
    if cmd == "blast" or cmd.startswith("blast "):
        if not _BOARD_OK:
            return TextResult("Board client unavailable.")
        sub = text[6:].strip() if cmd.startswith("blast ") else ""
        if sub == "who":
            who = _board_whoami()
            return TextResult(f"Board: logged in as {who}" if who else "Not logged in. Use: blast login <username>")
        if sub == "logout":
            _board_logout()
            return TextResult("Board session cleared.")
        if sub.startswith(("login ", "register ")):
            return TextResult(
                "Board login/register needs a password prompt — use the terminal "
                "(Open in Terminal) for this one, or ask me to add a login dialog here."
            )
        synth = cfg.get("_last_council_synthesis", "")
        if not synth:
            return TextResult("No council synthesis yet — run a council deliberation first, then blast.")
        who = _board_whoami()
        if not who:
            return TextResult("Not logged in to the board. Use the terminal to log in first.")
        ok, msg = _board_blast(synth, source="council")
        return TextResult(f"✓ Blasted. Post ID: {msg}" if ok else f"✗ {msg}")

    # ── Substrate ────────────────────────────────────────────────────────
    if cmd == "substrate" or cmd.startswith("substrate "):
        if not _SUBSTRATE_OK:
            return TextResult("Substrate module unavailable.")
        act = _get_activator()
        sub = text[10:].strip() if cmd.startswith("substrate ") else ""
        if sub == "status":
            st = act.status()
            ly = st["layer"]
            return TextResult(
                f"⬡ Substrate — RUW layer\nNodes: {ly['nodes']}  Edges: {ly['edges']}  "
                f"Activations: {st['activations']}\nAddress: {ly['address']}"
            )
        if sub.startswith("weave "):
            q = sub[6:].strip()
            hits = act.weave(q, top_k=5) if q else []
            if not hits:
                return TextResult("No nodes in layer yet. Run a council deliberation first.")
            return TextResult("⬡ Substrate weave — resonant nodes\n" + "\n".join(f"{score:.3f}  {nid}" for nid, score in hits))
        synth = cfg.get("_last_council_synthesis", "")
        query = cfg.get("_last_council_query", "")
        if not synth:
            return TextResult("No council synthesis yet. Run a council deliberation first.")
        result = act.activate(synth, query=query, session_id="gui")
        return TextResult(
            f"⬡ Substrate activated\nRUW address: {result['ruw_address']}\n"
            f"Resonance: {result['resonance']:.4f}  Nodes: {result['layer_state']['nodes']}"
        )

    # ── Obsidian ─────────────────────────────────────────────────────────
    if cmd in ("obsidian on", "obsidian off"):
        cfg["obsidian_enabled"] = cmd == "obsidian on"
        _obs_save_config(cfg["obsidian_enabled"], cfg.get("obsidian_path", ""))
        msg = f"Obsidian sync → {'ON' if cfg['obsidian_enabled'] else 'OFF'}"
        if cfg["obsidian_enabled"] and not cfg.get("obsidian_path"):
            msg += "\nSet vault path with: obsidian path <path>"
        return TextResult(msg)

    if cmd.startswith("obsidian path "):
        cfg["obsidian_path"] = text[14:].strip()
        _obs_save_config(cfg.get("obsidian_enabled", False), cfg["obsidian_path"])
        return TextResult(f"Obsidian vault → {cfg['obsidian_path']}")

    if cmd == "obsidian export":
        if not cfg.get("obsidian_path"):
            return TextResult("Set vault path first: obsidian path <path>")
        ok, msg = _obs_export(cfg["obsidian_path"])
        return TextResult(msg)

    if cmd == "obsidian status":
        return TextResult(
            f"Obsidian sync: {'ON' if cfg.get('obsidian_enabled') else 'OFF'}\n"
            f"Vault path: {cfg.get('obsidian_path') or '(not set)'}"
        )

    # ── Direct provider retry ───────────────────────────────────────────
    if cmd in ("grok", "use grok", "try grok"):
        last = cfg.get("last_user_msg", "")
        if not last:
            return TextResult("No previous message to retry with Grok.")
        if not cfg.get("api_key"):
            return TextResult("No xAI key set. Type: key xai-xxxxx")
        gen = _chat(last, history[:-1] if history else [], cfg["api_key"], None, False,
                    cfg.get("workspace", str(_CHAT_ROOT)), cfg.get("openai_key", ""), False, "",
                    force_provider="grok")
        return StreamResult("⟳ Grok re-run", gen)

    if cmd in ("claude", "use claude", "try claude"):
        last = cfg.get("last_user_msg", "")
        if not last:
            return TextResult("No previous message to retry with Claude.")
        if not cfg.get("anthropic_key"):
            return TextResult("No Anthropic key set. Type: anthropic sk-ant-xxxxx")
        gen = _chat(last, history[:-1] if history else [], "", None, False,
                    cfg.get("workspace", str(_CHAT_ROOT)), "", False, cfg["anthropic_key"],
                    force_provider="claude")
        return StreamResult("⟳ Claude re-run", gen)

    # ── Postal — sealed encrypted letters (read/manage side; composing a
    # new letter needs a multi-line dialog, handled by chat_panel.py) ──────
    if cmd == "letters" or cmd in ("letters for me", "letters from me"):
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        postal_user = cfg.get("postal_user", "joshua")
        if cmd == "letters for me":
            llist, heading = _postal_for(postal_user), f"LETTERS FOR {postal_user.upper()}"
        elif cmd == "letters from me":
            llist, heading = _postal_from(postal_user), f"LETTERS FROM {postal_user.upper()}"
        else:
            llist, heading = _postal_all(), "ALL SEALED LETTERS"
        if not llist:
            return TextResult(f"⬡ {heading}\n\nNo sealed letters found.")
        lines = [f"⬡ {heading}"]
        for e in llist:
            badge = "read" if e.get("read") else "unread"
            hint = f"  ({e['hint']})" if e.get("hint") else ""
            lines.append(
                f"{e['id']}  {e.get('from_display', '?')} → {e.get('for_display', '?')}  "
                f"{e.get('sealed', '')[:10]}  {badge}{hint}"
            )
        return TextResult("\n".join(lines))

    if cmd.startswith("open letter ") or cmd.startswith("letter "):
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        lid = (text[12:] if cmd.startswith("open letter ") else text[7:]).strip()
        if not lid:
            return TextResult("Usage: open letter <id>")
        entry = _postal_entry(lid)
        if not entry:
            return TextResult(f"Letter {lid} not found.")
        body = _postal_open(lid)
        if body is None:
            return TextResult("Decryption failed. This seal cannot be opened on this machine.")
        sig = {
            "verified": "✓ VERIFIED", "verified_rotated": "✓ VERIFIED (signed with sender's prior key)",
            "verified_compromised": "⟳ COHERENCE DEGRADED (signed with a compromised key)",
            "unverified": "~ unverified (sender not in contacts)",
            "unsigned": "unsigned (pre-identity letter)", "INVALID": "✗ SIGNATURE INVALID",
        }.get(_postal_sig_status(lid), _postal_sig_status(lid))
        header = f"from: {entry.get('from_display', '?')}  to: {entry.get('for_display', '?')}  {entry.get('sealed', '')[:10]}\n{sig}"
        if entry.get("hint"):
            header += f"\nhint: {entry['hint']}"
        return TextResult(f"{header}\n\n{body}")

    if cmd.startswith("council letter "):
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        lid = text[15:].strip()
        if not lid:
            return TextResult("Usage: council letter <id>")
        postal_user = cfg.get("postal_user", "joshua")
        reading = _postal_council(lid, postal_user, cfg)
        return TextResult(reading)

    if cmd.startswith("seal export "):
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        lid = text[12:].strip()
        result = _postal_export(lid)
        if result is None:
            return TextResult("Export failed — letter not found or cannot decrypt.")
        pack_path, passphrase = result
        return TextResult(
            f"⬡ Sealpack exported\nfile: {pack_path}\npassphrase: {passphrase}\n\n"
            "Share this passphrase with the recipient out-of-band. It is shown once and never stored."
        )

    if cmd.startswith("seal import "):
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        rest = text[12:].strip()
        # Last whitespace-separated token is the passphrase; everything
        # before it is the (possibly space-containing) file path.
        parts = rest.rsplit(None, 1)
        if len(parts) != 2:
            return TextResult("Usage: seal import <filepath> <passphrase>")
        pack_file, passphrase = parts
        new_id = _postal_import(pack_file.strip('"').strip("'"), passphrase)
        if new_id is None:
            return TextResult("Import failed — wrong passphrase or corrupted pack.")
        return TextResult(f"⬡ Sealed locally as: {new_id}")

    if cmd == "postal user" or cmd.startswith("postal user "):
        new_user = text[12:].strip().lower() if cmd.startswith("postal user ") else ""
        if not new_user:
            return TextResult(f"Current postal identity: {cfg.get('postal_user', 'joshua')}")
        cfg["postal_user"] = new_user
        return TextResult(f"Postal identity set to: {new_user}")

    if cmd.startswith("postal setup ") or cmd == "postal setup":
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        name = text[13:].strip() if cmd.startswith("postal setup ") else ""
        if not name:
            return TextResult("Usage: postal setup <your name>")
        try:
            meta = _postal_setup(name)
        except Exception as e:
            return TextResult(f"Setup failed: {e}")
        cfg["postal_user"] = meta.get("name", name).lower()
        return TextResult(
            f"⬡ Identity created\nName: {meta.get('name', name)}\nKey ID: {meta.get('key_id', '?')[:8]}\n"
            f"Public: {meta.get('pubkey', '?')}\n\n"
            f"Share this public key with anyone you want to receive letters from. "
            f"They add you with: postal add user {name} <your key>"
        )

    if cmd == "postal my key":
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        my_id = _postal_my_id()
        if not my_id:
            return TextResult("No identity set up yet. Run: postal setup <your name>")
        return TextResult(
            f"⬡ Your Cursiv identity\nName: {my_id.get('name', '?')}\n"
            f"Key ID: {my_id.get('key_id', '?')[:8]}\nPublic: {my_id.get('pubkey', '?')}"
        )

    if cmd.startswith("postal add user ") or cmd == "postal add user":
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        parts = text[16:].strip().split() if cmd.startswith("postal add user ") else []
        if len(parts) < 2:
            return TextResult("Usage: postal add user <name> <pubkey>")
        try:
            entry = _postal_add_contact(parts[0], parts[1])
        except ValueError as e:
            return TextResult(f"Invalid public key: {e}")
        return TextResult(f"⬡ Contact added: {parts[0]}  (key-id: {entry.get('key_id', '?')[:8]})")

    if cmd.startswith("postal remove user "):
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        name = text[19:].strip()
        ok = _postal_rm_contact(name)
        return TextResult(f"Contact removed: {name}" if ok else f"Contact not found: {name}")

    if cmd.startswith("postal rotate") or cmd == "postal rotate key":
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        compromised = "compromised" in cmd or "leaked" in cmd
        reason = "key compromised — attacker may have private key" if compromised else "manual rotation"
        try:
            rot = _postal_rotate(reason=reason, compromised=compromised)
        except Exception as e:
            return TextResult(f"Rotation failed: {e}")
        if not rot:
            return TextResult("Rotation failed — no identity set up. Run: postal setup <name>")
        note = (
            "\n\nCoherence degradation will activate on the retired key — any letter later "
            "read through it returns shifted content. The attacker sees output, not truth."
            if compromised else ""
        )
        return TextResult(
            f"⬡ Key rotation\nOld key ID: {rot.get('old_key_id', '?')[:8]} (archived locally)\n"
            f"New key ID: {rot.get('new_key_id', '?')[:8]}\nNew public: {rot.get('new_pubkey', '?')}\n\n"
            f"Update your contacts: postal add user <your name> <new key>{note}"
        )

    if cmd == "postal key history":
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        hist = _postal_key_history()
        if not hist:
            return TextResult("⬡ Key history\n\nNo retired keys.")
        lines = ["⬡ Key history"]
        for hk in hist:
            flag = "  COMPROMISED — coherence degradation active" if hk.get("compromised") else ""
            lines.append(f"{hk.get('key_id', '?')[:8]}  retired:{hk.get('retired_at', '?')[:10]}  {hk.get('reason', '?')[:40]}{flag}")
        return TextResult("\n".join(lines))

    if cmd == "postal contacts":
        if not _POSTAL_OK:
            return TextResult("Postal module unavailable.")
        clist = _postal_contacts()
        if not clist:
            return TextResult("⬡ Contacts\n\nNo contacts yet. Use: postal add user <name> <pubkey>")
        lines = [f"⬡ Contacts ({len(clist)})"]
        for c in clist:
            lines.append(f"{c['name']:<16}  id:{c.get('key_id', '?')[:8]}  added:{c.get('added', '?')[:10]}")
        return TextResult("\n".join(lines))

    if cmd.startswith("legacy import "):
        imp_path = text[14:].strip().strip('"').strip("'")
        if not imp_path:
            return TextResult("Usage: legacy import <path to .legacypack file>")
        try:
            count, skipped = _legacy_import_pack(imp_path)
        except (FileNotFoundError, ValueError) as e:
            return TextResult(str(e))
        except Exception as e:
            return TextResult(f"Import failed: {e}")
        if count == 0 and not skipped:
            return TextResult("No letters found in pack.")
        out = []
        if count:
            out.append(f"Imported {count} letter(s).")
        if skipped:
            out.append(f"Skipped {len(skipped)} duplicate(s): " + ", ".join(skipped))
        out.append("Letters are now in the vault.")
        return TextResult("\n".join(out))

    # ── Image generation (DALL-E 3) ─────────────────────────────────────
    if cmd.startswith("image ") or cmd == "image":
        prompt = text[6:].strip()
        if not prompt:
            return TextResult("Usage: image <description>")
        if not cfg.get("openai_key"):
            return TextResult("No OpenAI key — image generation requires DALL-E 3. Set key: openai sk-...")
        try:
            import openai as _oai_img
            import urllib.request as _img_req
            from datetime import datetime as _ImgDt
            img_client = _oai_img.OpenAI(api_key=cfg["openai_key"])
            resp = img_client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1)
            img_url = resp.data[0].url
            revised = getattr(resp.data[0], "revised_prompt", prompt)
            img_dir = Path(cfg.get("workspace", str(_CHAT_ROOT))) / ".cursiv" / "images"
            img_dir.mkdir(parents=True, exist_ok=True)
            img_path = img_dir / f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            _img_req.urlretrieve(img_url, str(img_path))
        except Exception as e:
            return TextResult(f"Image generation failed: {e}")
        if _STRAND_OK:
            _strand_save(f"image: {prompt[:200]}", f"Generated: {img_path}\nRevised prompt: {revised[:300]}",
                         tags=["image", "dalle3"], score=0.70, territory_tag="creative", source="image", model="dall-e-3")
        note = f"\n\nDALL-E revised the prompt to:\n{revised[:300]}" if revised != prompt else ""
        return TextResult(f"⬡ Image generated  ({img_path.name}){note}", image_path=str(img_path))

    return None


def hey_prefix(raw: str) -> tuple[str, str]:
    """Detect a 'hey <provider> ...' routing prefix. Returns (force_provider, stripped_text)."""
    lower = raw.lower()
    for prefix, fp in (
        ("hey council ", "council"), ("hey grok ", "grok"), ("hey claude ", "claude"),
        ("hey chat ", "openai"), ("hey openai ", "openai"), ("hey gpt ", "openai"),
        ("hey ollama ", "ollama"),
    ):
        if lower.startswith(prefix):
            return fp, raw[len(prefix):].strip()
    return "", raw


# ── Blast (board) login/register — password collected by the caller via a
# Qt dialog, since this module stays UI-agnostic; the actual HTTP call
# lives here so it's identical to what the terminal CLI does. ─────────────

def blast_login(username: str, password: str) -> TextResult:
    if not _BOARD_OK:
        return TextResult("Board client unavailable.")
    ok, msg = _board_login(username, password)
    return TextResult(f"✓ Logged in as {msg}" if ok else f"✗ {msg}")


def blast_register(username: str, password: str) -> TextResult:
    if not _BOARD_OK:
        return TextResult("Board client unavailable.")
    ok, msg = _board_register(username, password)
    return TextResult(f"✓ Account created. Logged in as {msg}" if ok else f"✗ {msg}")


# ── Voice — caller (chat_panel.py) owns the mic-record UI affordance
# (start/stop button); this function does the actual capture, STT, and
# Babel-clean pass, identical to the terminal CLI's "voice"/"listen". ─────

def voice_turn(cfg: dict, duration_s: float = 5.0, raw_mode: bool = False,
                status_cb: Optional[Callable[[str], None]] = None) -> TextResult:
    if not _VOICE_OK or not _voice_avail():
        return TextResult("Voice agent unavailable — needs: pip install faster-whisper sounddevice")
    cb = status_cb or (lambda m: None)
    try:
        pcm, arr = _voice_record(duration_s=duration_s, status_cb=cb)
        raw_text = _voice_transcribe(pcm, float32_arr=arr, status_cb=cb)
    except RuntimeError as e:
        return TextResult(str(e))
    except Exception as e:
        return TextResult(f"Voice capture error: {e}")

    if not raw_text:
        return TextResult("Nothing heard — adjust mic or try again.")

    if raw_mode:
        return TextResult(raw_text)

    # Stage 2: Babel binary clean pass -- fixes filler words/errors and
    # translates non-English speech, same pipeline the CLI uses.
    try:
        decoded = _babel_decode(_babel_encode(raw_text))
        gen, _label = _cascade_gen(cfg, [
            {"role": "system", "content": _VOICE_CLEAN_SYS},
            {"role": "user", "content": decoded},
        ], max_tokens=300)
        cleaned = "".join(c for c in gen if c != RATE_SENTINEL)
        return TextResult((cleaned.strip() or raw_text))
    except Exception:
        return TextResult(raw_text)


# ── Paste image from clipboard → vision analysis → strand. Caller passes
# already-extracted PNG bytes (from Qt's clipboard); the vision-API calls
# and strand save live here so they match the terminal CLI's "paste". ────

def analyze_pasted_image(png_bytes: bytes, cfg: dict, width: int, height: int) -> TextResult:
    import base64 as _b64img

    img_dir = Path(cfg.get("workspace", str(_CHAT_ROOT))) / ".cursiv" / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    img_path = img_dir / f"paste_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img_path.write_bytes(png_bytes)

    vision_result, vision_provider = "", ""
    img_b64 = _b64img.b64encode(png_bytes).decode()
    ant_key, oai_key = cfg.get("anthropic_key", ""), cfg.get("openai_key", "")

    if ant_key:
        try:
            import anthropic as _anth_v
            resp = _anth_v.Anthropic(api_key=ant_key).messages.create(
                model="claude-sonnet-4-6", max_tokens=600,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}},
                    {"type": "text", "text": "Describe what you see in this image. Be specific and useful. "
                                              "Flag anything relevant to code, design, architecture, or ongoing work."},
                ]}],
            )
            vision_result, vision_provider = resp.content[0].text, "Claude"
        except Exception:
            pass

    if not vision_result and oai_key:
        try:
            import openai as _oai_v
            resp2 = _oai_v.OpenAI(api_key=oai_key).chat.completions.create(
                model="gpt-4o", max_tokens=600,
                messages=[{"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                    {"type": "text", "text": "Describe what you see in this image. Be specific and useful. "
                                              "Flag anything relevant to code, design, architecture, or ongoing work."},
                ]}],
            )
            vision_result, vision_provider = resp2.choices[0].message.content, "GPT-4o"
        except Exception:
            pass

    if _STRAND_OK:
        body = vision_result or f"Image pasted: {img_path} ({width}x{height}px)"
        _strand_save(f"paste: image {img_path.stem}", body, tags=["image", "paste", "vision"],
                     score=0.72, territory_tag="worldmodel", source="paste", model=vision_provider or "none")

    header = f"⬡ Image pasted — {width}×{height}px\n\n"
    if vision_result:
        return TextResult(f"{header}Vision analysis (via {vision_provider}):\n\n{vision_result}", image_path=str(img_path))
    return TextResult(f"{header}No vision model available — image saved, no analysis. "
                       f"Set an Anthropic or OpenAI key to enable analysis.", image_path=str(img_path))


# ── Postal compose — caller (chat_panel.py) collects recipient/hint/body
# via a dialog; the actual sealing call is identical to the terminal CLI's
# "write to" flow. ──────────────────────────────────────────────────────

def postal_compose(sender_user: str, recipient_raw: str, hint: str, content: str) -> TextResult:
    if not _POSTAL_OK:
        return TextResult("Postal module unavailable.")
    if not content.strip():
        return TextResult("Nothing written — letter not sent.")
    resolved = _postal_resolve(recipient_raw)
    recipient_key = resolved[1] if resolved else recipient_raw.lower().replace(" ", "")
    recipient_disp = resolved[0] if resolved else recipient_raw.title()
    my_id = _postal_my_id()
    sender_key = my_id.get("name", sender_user).lower() if my_id else sender_user
    sender_disp = my_id.get("name", sender_user).title() if my_id else sender_user.title()
    lid = _postal_seal(
        sender_key=sender_key, sender_display=sender_disp,
        recipient_key=recipient_key, recipient_display=recipient_disp,
        content=content, hint=hint,
    )
    return TextResult(
        f"⬡ Sealed\nid: {lid}\nfor: {recipient_disp}\n"
        f"signed: {'yes — Ed25519' if my_id else 'no — run postal setup first'}\n"
        f"readable: on this machine only"
    )
