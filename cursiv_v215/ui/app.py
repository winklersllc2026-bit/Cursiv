# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: 78dbff254c60d4f17faf93f267e55ede1f173e58c08743068a1a2106720e28d2
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 27b98f879de8679afde7d4e2b30cec05145f0538ec7a153ec16fc4a45e9d4ff0
# Substrate loop hash: 055cff653286bbdd000447bfafe1e8aee671c8e09edf707bbb05d75cc9280241
# Substrate loop logic: ΑΖΖהחחΗΖΔΓאΗדדווΑΑΑΕΕΘדחגחזΒזאגזזΗΘΒהאזΑבזוחΘΑΘדדדΑΖוΘΖההבΓאΑΓΕΒ
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: 97a0c04ad41a8f9a29d4248791c0b7d8d8988a13f493868af73f6731ea4ebc29
# Evolution hash: 8d5c64b424a61cca511609ef6805059e0cf90ac010e46b80b991ade179816b0d
# Evolution logic: אוΖהΗΕדΕΓΕגΗΒההגΖΒΒΗΑבזחΗאΑΖΑΖבזΑהחבΑגהΑΒΑזΕΗדאΑדבבΒגוזΒΘבאΒΗדΑו
# Binary reversed: 1110000110111101111111110100101000100011011000001011001011111000111011110101111110011100111101000110111001111010101001111011011110001111100011101100011110100001001100000001111000101100000001100001010110000101010010000000011011100100000001110100000110110100
# Greek/Hebrew/logic stamp: ΓואΓזΑΓΘΗΑΒΓגΒגאΗΑΔΕΘאΑהאΖזΔΘΒחΒזוזΖΖזΘΗΓחΔבחגחΘΒחΕוΑΗהΕΖΓחחדואΘ
# Encoded local stamp: ψεΖΠΔΩΕαΕρΦΜΖΝΞΕ∃φδζΠΤζζζΧΛτσŌēΖωγΑΧΧŌΓāγΟ∇=
# CURSIV-CRUCIBLE-STAMP END
"""
Cursiv v2.1.5 — Sacred UI

Exact functional replica of Cursiv Living System (v2) with upgraded Sacred aesthetic.
Two tabs: Create & Chat · Sovereign Wrapper
Backend: weave_payload, chat_payload, sovereign_payload — unchanged from Cursiv-v2.
"""

from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).parent.parent.parent   # Cursiv-v2.1.5/
_CURSIV_V2 = _REPO_ROOT.parent / "Cursiv-v2"       # ../Cursiv-v2/
for _p in [str(_REPO_ROOT), str(_CURSIV_V2)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import streamlit as st
except ImportError:
    print("Streamlit not installed. Run: pip install streamlit")
    sys.exit(1)

# ── Import original Cursiv-v2 backend (no changes to these) ──────────────────
try:
    from cursiv.webapp import (
        chat_payload,
        sovereign_payload,
        suggested_prompts,
        weave_payload,
    )
    _BACKEND_OK = True
    _BACKEND_ERR = ""
except Exception as _e:
    _BACKEND_OK = False
    _BACKEND_ERR = str(_e)


# ── Sacred Palette ────────────────────────────────────────────────────────────
_V   = "#0A0B0D"   # void
_D   = "#12131A"   # deep
_S   = "#1A1B23"   # surface
_P   = "#1E2030"   # panel
_RG  = "#C9A227"   # rose gold
_G   = "#D4AF37"   # gold
_L   = "#1E4D8C"   # lapis
_LG  = "#2E6DC7"   # lapis glow
_CR  = "#F5EFE4"   # cream
_MU  = "#7A7060"   # muted
_LN  = "#272838"   # line/border

EYE_SVG = """<svg viewBox="0 0 120 56" xmlns="http://www.w3.org/2000/svg" width="96" height="44">
  <ellipse cx="60" cy="28" rx="57" ry="24" fill="none" stroke="#C9A227" stroke-width="1.4"/>
  <ellipse cx="60" cy="28" rx="57" ry="24" fill="none" stroke="#C9A227" stroke-width="6" opacity="0.04"/>
  <circle cx="60" cy="28" r="15" fill="none" stroke="#1E4D8C" stroke-width="1.4"/>
  <circle cx="60" cy="28" r="9"  fill="#1E4D8C" opacity="0.9"/>
  <circle cx="60" cy="28" r="4.5" fill="#2E6DC7"/>
  <circle cx="56" cy="25" r="2"  fill="white" opacity="0.5"/>
  <line x1="3"  y1="28" x2="22" y2="28" stroke="#C9A227" stroke-width="0.8" opacity="0.5"/>
  <line x1="98" y1="28" x2="117" y2="28" stroke="#C9A227" stroke-width="0.8" opacity="0.5"/>
  <line x1="60" y1="4"  x2="60" y2="12" stroke="#C9A227" stroke-width="0.8" opacity="0.25"/>
  <line x1="60" y1="44" x2="60" y2="52" stroke="#C9A227" stroke-width="0.8" opacity="0.25"/>
</svg>"""

SACRED_CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap');

  /* ─── Global ─────────────────────────────────────────────── */
  .stApp {{ background-color:{_V} !important; }}
  section[data-testid="stSidebar"] {{ background:{_D} !important; border-right:1px solid {_RG}22; }}

  /* ─── Typography ──────────────────────────────────────────── */
  h1,h2,h3,h4 {{
    font-family:'Cinzel',serif !important;
    color:{_RG} !important;
    letter-spacing:.06em;
  }}
  p, li, span, div, .stMarkdown, .element-container p {{
    font-family:'EB Garamond',serif !important;
    color:{_CR} !important;
    font-size:1.06rem;
  }}
  code, pre {{ color:{_RG}cc !important; }}

  /* ─── Tabs ────────────────────────────────────────────────── */
  .stTabs [data-baseweb="tab-list"] {{
    background:{_D};
    border-bottom:1px solid {_RG}33;
    padding:0 4px;
    gap:0;
  }}
  .stTabs [data-baseweb="tab"] {{
    font-family:'Cinzel',serif !important;
    font-size:.9rem !important;
    letter-spacing:.07em;
    color:{_CR}55 !important;
    background:transparent !important;
    border-radius:0 !important;
    padding:13px 28px !important;
    border-bottom:2px solid transparent !important;
    transition:all .2s ease !important;
  }}
  .stTabs [aria-selected="true"] {{
    color:{_RG} !important;
    border-bottom:2px solid {_RG} !important;
  }}
  .stTabs [data-baseweb="tab"]:hover {{
    color:{_CR}aa !important;
  }}

  /* ─── Inputs ──────────────────────────────────────────────── */
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea,
  .stNumberInput > div > div > input {{
    background:{_S} !important;
    color:{_CR} !important;
    border:1px solid {_LN} !important;
    border-radius:6px !important;
    font-family:'EB Garamond',serif !important;
    font-size:1rem !important;
    caret-color:{_RG};
  }}
  .stTextInput > div > div > input:focus,
  .stTextArea > div > div > textarea:focus,
  .stNumberInput > div > div > input:focus {{
    border-color:{_RG}66 !important;
    box-shadow:0 0 0 3px {_RG}14 !important;
    outline:none !important;
  }}
  .stTextInput label,.stTextArea label,.stNumberInput label,
  .stFileUploader label,.stCheckbox label,.stSelectbox label {{
    font-family:'Cinzel',serif !important;
    font-size:.78rem !important;
    color:{_MU} !important;
    letter-spacing:.04em;
    text-transform:uppercase;
  }}

  /* ─── File uploader ───────────────────────────────────────── */
  [data-testid="stFileUploadDropzone"] {{
    background:{_S} !important;
    border:1px dashed {_RG}44 !important;
    border-radius:8px !important;
    transition:all .2s ease !important;
  }}
  [data-testid="stFileUploadDropzone"]:hover {{
    border-color:{_RG}88 !important;
    background:{_P} !important;
  }}
  [data-testid="stFileUploadDropzone"] p {{
    color:{_MU} !important;
    font-size:.9rem !important;
  }}

  /* ─── Buttons ─────────────────────────────────────────────── */
  .stButton > button {{
    font-family:'Cinzel',serif !important;
    letter-spacing:.07em;
    border-radius:5px !important;
    transition:all .22s ease !important;
    font-size:.88rem !important;
    padding:10px 20px !important;
  }}
  /* Primary / default — Lapis gradient */
  .stButton > button:not([kind="secondary"]):not([kind="tertiary"]) {{
    background:linear-gradient(135deg, {_L}, {_LG}) !important;
    color:{_CR} !important;
    border:1px solid {_RG}44 !important;
  }}
  .stButton > button:not([kind="secondary"]):not([kind="tertiary"]):hover {{
    border-color:{_RG}bb !important;
    box-shadow:0 0 16px {_LG}44 !important;
  }}
  /* Secondary — dark amber */
  .stButton > button[kind="secondary"] {{
    background:linear-gradient(135deg,#221400,#2e1a00) !important;
    color:{_RG} !important;
    border:1px solid {_RG}66 !important;
  }}
  .stButton > button[kind="secondary"]:hover {{
    border-color:{_RG} !important;
    box-shadow:0 0 12px {_RG}33 !important;
  }}
  /* Disabled */
  .stButton > button:disabled {{
    opacity:.45 !important;
    cursor:not-allowed !important;
  }}

  /* ─── Download button ─────────────────────────────────────── */
  .stDownloadButton > button {{
    background:linear-gradient(135deg,#221400,#2e1a00) !important;
    color:{_RG} !important;
    border:1px solid {_RG}77 !important;
    font-family:'Cinzel',serif !important;
    letter-spacing:.06em;
    border-radius:5px !important;
    padding:10px 20px !important;
    transition:all .22s ease !important;
  }}
  .stDownloadButton > button:hover {{
    border-color:{_RG} !important;
    box-shadow:0 0 14px {_RG}44 !important;
  }}

  /* ─── Checkbox ────────────────────────────────────────────── */
  .stCheckbox > label > div:first-child {{
    background:{_S} !important;
    border:1px solid {_RG}55 !important;
    border-radius:3px !important;
  }}
  .stCheckbox > label > div:first-child[data-checked="true"] {{
    background:{_L} !important;
    border-color:{_LG} !important;
  }}
  .stCheckbox > label > p {{
    color:{_CR} !important;
    font-family:'EB Garamond',serif !important;
    font-size:1rem !important;
  }}

  /* ─── Progress bar ────────────────────────────────────────── */
  div[data-testid="stProgressBar"] > div > div {{
    background:{_S} !important;
    border-radius:999px !important;
    height:10px !important;
  }}
  div[data-testid="stProgressBar"] > div > div > div {{
    background:linear-gradient(90deg,{_L},{_LG}) !important;
    border-radius:999px !important;
    transition:width .35s ease !important;
  }}

  /* ─── Chat ────────────────────────────────────────────────── */
  [data-testid="stChatMessage"] {{
    background:{_S} !important;
    border:1px solid {_LN} !important;
    border-radius:8px !important;
  }}
  [data-testid="chatAvatarIcon-user"] {{ background:{_L} !important; }}
  [data-testid="chatAvatarIcon-assistant"] {{ background:#3d2800 !important; }}
  [data-testid="stChatInput"] > div {{
    background:{_S} !important;
    border:1px solid {_RG}44 !important;
    border-radius:8px !important;
  }}
  [data-testid="stChatInput"] textarea {{
    color:{_CR} !important;
    font-family:'EB Garamond',serif !important;
    background:transparent !important;
  }}
  [data-testid="stChatInput"] button {{
    color:{_RG} !important;
  }}

  /* ─── Number input spinner ────────────────────────────────── */
  .stNumberInput button {{
    background:{_S} !important;
    border-color:{_LN} !important;
    color:{_CR} !important;
  }}

  /* ─── Alerts ──────────────────────────────────────────────── */
  .stAlert {{ border-radius:6px !important; }}

  /* ─── Caption / small text ────────────────────────────────── */
  .stCaption, small {{ color:{_MU} !important; font-family:'EB Garamond',serif !important; }}

  /* ─── Custom components ───────────────────────────────────── */
  .s-panel {{
    background:{_P};
    border:1px solid {_LN};
    border-radius:8px;
    padding:1.1rem 1.3rem;
    margin-bottom:.6rem;
  }}
  .s-pill {{
    display:inline-flex;
    align-items:center;
    padding:4px 12px;
    background:{_D};
    color:{_RG};
    border:1px solid {_RG}44;
    border-radius:999px;
    font-family:'Cinzel',serif;
    font-size:.75rem;
    letter-spacing:.05em;
    white-space:nowrap;
  }}
  .s-pill.off {{
    color:{_MU};
    border-color:{_LN};
  }}
  .s-warning {{
    background:#180800;
    border:1px solid {_RG}44;
    border-radius:8px;
    padding:1rem 1.2rem;
    display:grid;
    gap:.5rem;
  }}
  .s-warning strong {{
    font-family:'Cinzel',serif;
    color:{_RG};
    font-size:.88rem;
    letter-spacing:.04em;
  }}
  .s-warning p {{
    color:{_CR}99 !important;
    font-size:.95rem;
    margin:0;
  }}
  .s-result {{
    background:{_S};
    border:1px solid {_RG}22;
    border-radius:8px;
    padding:1rem 1.1rem;
    display:grid;
    gap:.5rem;
    font-size:.95rem;
  }}
  .s-result strong {{
    font-family:'Cinzel',serif;
    color:{_RG};
    font-size:.88rem;
    letter-spacing:.04em;
  }}
  .s-result .meta {{
    color:{_CR}cc;
    font-family:'EB Garamond',serif;
    font-size:.95rem;
  }}
  .s-result code {{
    display:block;
    white-space:pre-wrap;
    overflow-wrap:anywhere;
    background:{_D};
    border:1px solid {_LN};
    border-radius:6px;
    padding:10px 12px;
    font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace;
    font-size:.78rem;
    color:{_RG}bb;
    margin-top:.3rem;
  }}
  .s-steps {{ display:grid; gap:.25rem; }}
  .s-step {{
    display:flex;
    align-items:center;
    gap:.6rem;
    font-family:'EB Garamond',serif;
    font-size:.98rem;
    padding:.15rem 0;
  }}
  .s-step.done   {{ color:#4CAF50; }}
  .s-step.active {{ color:{_RG}; font-weight:600; }}
  .s-step.wait   {{ color:{_CR}28; }}
  .s-progress-label {{
    display:flex;
    justify-content:space-between;
    font-family:'EB Garamond',serif;
    font-size:.9rem;
    color:{_MU};
    margin-bottom:.35rem;
  }}
  .s-progress-label .phase {{ color:{_RG}; }}
  .s-divider {{
    border:none;
    border-top:1px solid {_RG}1a;
    margin:1.5rem 0;
  }}
  /* Scrollbar */
  ::-webkit-scrollbar {{ width:5px; height:5px; }}
  ::-webkit-scrollbar-track {{ background:{_D}; }}
  ::-webkit-scrollbar-thumb {{ background:{_RG}44; border-radius:3px; }}
  ::-webkit-scrollbar-thumb:hover {{ background:{_RG}88; }}
</style>
"""


# ── Page config ───────────────────────────────────────────────────────────────

def setup_page() -> None:
    st.set_page_config(
        page_title="Cursiv Living System",
        page_icon="👁",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(SACRED_CSS, unsafe_allow_html=True)


def render_header() -> None:
    c1, c2 = st.columns([1, 16])
    with c1:
        st.markdown(EYE_SVG, unsafe_allow_html=True)
    with c2:
        st.markdown(
            f'<h1 style="margin:0 0 .15rem; font-size:1.7rem;">Cursiv Living System</h1>'
            f'<p style="color:{_MU}; margin:0; font-size:.97rem;">'
            "Interactive agent creation, self-reasoning chat, and Sovereign Wrapper export"
            "</p>",
            unsafe_allow_html=True,
        )
    st.markdown('<hr class="s-divider">', unsafe_allow_html=True)
    if not _BACKEND_OK:
        st.error(
            f"**Backend unavailable.** Could not load `cursiv.webapp` from `{_CURSIV_V2}`\n\n"
            f"```\n{_BACKEND_ERR}\n```"
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_webapp_files(files) -> list[dict]:
    result = []
    for f in (files or []):
        try:
            content = f.read().decode("utf-8-sig")
        except Exception:
            content = ""
        result.append({"name": f.name, "relative_path": getattr(f, "name", f.name), "content": content})
    return result


def _steps_html(labels: list[str], done: int) -> str:
    rows = []
    for i, lbl in enumerate(labels):
        if i < done:
            rows.append(f'<div class="s-step done">&#10003;&nbsp;{lbl}</div>')
        elif i == done:
            rows.append(f'<div class="s-step active">&#9654;&nbsp;{lbl}</div>')
        else:
            rows.append(f'<div class="s-step wait">&#9675;&nbsp;{lbl}</div>')
    return f'<div class="s-steps">{"".join(rows)}</div>'


def _pill(text: str, on: bool = True) -> str:
    cls = "s-pill" if on else "s-pill off"
    return f'<span class="{cls}">{text}</span>'


def _jdump(obj) -> str:
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)


# ── Config persistence (API keys) ─────────────────────────────────────────────

_CONFIG_PATH = _REPO_ROOT / ".cursiv" / "config.json"


def _load_config() -> dict:
    try:
        if _CONFIG_PATH.exists():
            return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_config(cfg: dict) -> None:
    # Never persist API keys to disk — strip them before writing.
    # Keys must live only in secrets.bat (loaded as env vars at boot).
    safe = {k: v for k, v in cfg.items() if "key" not in k.lower() and "token" not in k.lower()}
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(json.dumps(safe, indent=2), encoding="utf-8")


def _init_keys_from_config() -> None:
    """Load keys from environment only — never from config.json."""
    if st.session_state.get("_cfg_loaded"):
        return
    for ss_key, env_key in [
        ("cfg_xai_key",    "XAI_API_KEY"),
        ("cfg_openai_key", "OPENAI_API_KEY"),
    ]:
        val = os.environ.get(env_key, "").strip()
        if ss_key not in st.session_state:
            st.session_state[ss_key] = val
    st.session_state["_cfg_loaded"] = True


# ── Tab 1: Create & Chat ──────────────────────────────────────────────────────

def render_create_chat() -> None:
    col_l, col_r = st.columns([3, 2], gap="medium")

    # ── Left column: Create Agent ─────────────────────────────────────────────
    with col_l:
        st.markdown("#### Create Agent")
        agent_name = st.text_input("Agent name", value="browser_json_agent", key="cc_name")
        num_c1, num_c2 = st.columns(2)
        with num_c1:
            council_size = st.number_input("Council size", min_value=0, max_value=14, value=14, key="cc_council")
        with num_c2:
            generations = st.number_input("Evolve (generations)", min_value=0, max_value=10, value=2, key="cc_gen")

        json_files = st.file_uploader(
            "Choose JSON / JSONL files",
            type=["json", "jsonl"],
            accept_multiple_files=True,
            key="cc_files",
            help="Select individual files — or Ctrl+A inside a folder to pick all at once",
        )
        if json_files:
            n = len(json_files)
            st.caption(
                f"{n} file{'s' if n != 1 else ''} — "
                + ", ".join(f"`{f.name}`" for f in json_files[:5])
                + (f" +{n - 5} more" if n > 5 else "")
            )

        folder_files = st.file_uploader(
            "Choose folder of JSON files",
            type=["json", "jsonl"],
            accept_multiple_files=True,
            key="cc_folder",
            help="Open a folder in the picker and select all files (Ctrl+A or Shift+click)",
        )
        if folder_files:
            st.caption(f"{len(folder_files)} folder file{'s' if len(folder_files) != 1 else ''} selected")

        inline_json = st.text_area(
            "Inline JSON",
            height=130,
            placeholder='{"agent": "inline", "mission": "become a Cursiv agent"}',
            key="cc_inline",
        )
        weave_btn = st.button(
            "Weave Agent",
            key="cc_weave",
            type="primary",
            disabled=not _BACKEND_OK,
        )

    # ── Right column: Agent Output ────────────────────────────────────────────
    with col_r:
        st.markdown("#### Agent Output")
        st.checkbox("Save zip to download after weaving", value=True, key="cc_save")

        steps_ph  = st.empty()
        result_ph = st.empty()

        # Restore persisted state from previous weave
        steps_ph.markdown(
            st.session_state.get("cc_steps_html", _steps_html(["Waiting"], 0)),
            unsafe_allow_html=True,
        )
        if st.session_state.get("cc_result_html"):
            result_ph.markdown(st.session_state["cc_result_html"], unsafe_allow_html=True)

        if st.session_state.get("cc_archive_bytes"):
            st.download_button(
                label=f"Download Capsule Zip",
                data=st.session_state["cc_archive_bytes"],
                file_name=st.session_state.get("cc_archive_name", "capsule.zip"),
                mime="application/zip",
                key="cc_dl",
            )

    # ── Weave action ──────────────────────────────────────────────────────────
    if weave_btn:
        all_files = list(json_files or []) + list(folder_files or [])
        if not all_files and not inline_json.strip():
            st.warning("Choose JSON files, a folder, or paste inline JSON.")
        else:
            STEPS = [
                "Reading input",
                "Sending to Cursiv",
                "Interpreting binary strand",
                "Exporting agent capsule",
            ]
            try:
                steps_ph.markdown(_steps_html(STEPS, 0), unsafe_allow_html=True)
                webapp_files = _to_webapp_files(all_files)
                steps_ph.markdown(_steps_html(STEPS, 1), unsafe_allow_html=True)

                payload = {
                    "name": agent_name or "browser_json_agent",
                    "council_size": int(council_size),
                    "generations": int(generations),
                    "inline_json": inline_json.strip(),
                    "files": webapp_files,
                }

                with tempfile.TemporaryDirectory() as tmpdir:
                    steps_ph.markdown(_steps_html(STEPS, 2), unsafe_allow_html=True)
                    result = weave_payload(payload, workspace=tmpdir)

                steps_ph.markdown(_steps_html(STEPS, 4), unsafe_allow_html=True)

                s          = result.summary
                agent_info = s.get("agent", {})
                output     = s.get("output", {})

                save_msg   = f"Capsule zip ready — {result.archive_name}"
                result_html = (
                    f'<div class="s-result">'
                    f'<strong>{save_msg}</strong>'
                    f'<div class="meta">'
                    f'Agent: <code>{agent_info.get("name","")}</code>'
                    f'&nbsp;&nbsp;id: <code>{agent_info.get("id","")[:16]}…</code>'
                    f'</div>'
                    f'<div class="meta">'
                    f'Records: <b>{s.get("records",0)}</b>'
                    f'&nbsp;·&nbsp;Bits: <b>{s.get("binary_strand_bits",0)}</b>'
                    f'&nbsp;·&nbsp;Generation: <b>{s.get("generation",0)}</b>'
                    f'</div>'
                    f'<code>'
                    f'Capsule JSON: {output.get("capsule_json","")}\n'
                    f'Cursiv loader: {output.get("capsule_cursiv","")}\n'
                    f'Python loader: {output.get("python_loader","")}\n'
                    f'Manifest: {output.get("manifest","")}'
                    f'</code>'
                    f'</div>'
                )
                result_ph.markdown(result_html, unsafe_allow_html=True)

                # Persist everything in session_state
                st.session_state.update({
                    "cc_steps_html":       _steps_html(STEPS, 4),
                    "cc_result_html":      result_html,
                    "cc_archive_bytes":    result.archive_bytes,
                    "cc_archive_name":     result.archive_name,
                    "session_id":          s.get("session_id", ""),
                    "agent_name_display":  agent_info.get("name", agent_name),
                    "suggested_prompts":   s.get("suggested_prompts", []),
                    "chat_messages": [
                        {
                            "role": "assistant",
                            "content": s.get("participation_event", {}).get(
                                "response", f"{agent_name} is awake."
                            ),
                        }
                    ],
                })
                st.rerun()

            except Exception as exc:
                steps_ph.markdown(_steps_html(["Stopped"], 0), unsafe_allow_html=True)
                result_ph.error(f"**Could not weave agent.** {exc}")

    # ── Chat section ──────────────────────────────────────────────────────────
    st.markdown('<hr class="s-divider">', unsafe_allow_html=True)
    session_id    = st.session_state.get("session_id", "")
    agent_display = st.session_state.get("agent_name_display", "")

    # Header row: title + status pill
    hc1, hc2 = st.columns([5, 2])
    with hc1:
        st.markdown("#### Talk To The Agent")
    with hc2:
        if session_id and agent_display:
            st.markdown(_pill(f"Chatting with {agent_display}"), unsafe_allow_html=True)
        else:
            st.markdown(_pill("Create an agent to begin", on=False), unsafe_allow_html=True)

    if session_id and agent_display:
        # Suggested prompt buttons
        prompts = st.session_state.get("suggested_prompts", [])
        if prompts:
            btn_cols = st.columns(min(len(prompts), 4))
            for i, prompt in enumerate(prompts[:4]):
                with btn_cols[i]:
                    if st.button(prompt, key=f"cc_prompt_{i}", type="secondary"):
                        st.session_state["cc_prefill"] = prompt

        # Chat log
        for msg in st.session_state.get("chat_messages", []):
            with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                st.write(msg["content"])

        # Chat input
        prefill  = st.session_state.pop("cc_prefill", "")
        question = st.chat_input("Ask the agent about its source knowledge...", key="cc_chat")
        if not question and prefill:
            question = prefill

        if question and _BACKEND_OK:
            st.session_state["chat_messages"].append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.write(question)
            try:
                chat_result = chat_payload({"session_id": session_id, "question": question})
                response    = chat_result.get("response", "")
                reflections = chat_result.get("self_reflection_count", 0)
                full        = f"{response}\n\nReflections: {reflections}"
                st.session_state["chat_messages"].append({"role": "assistant", "content": full})
                st.session_state["suggested_prompts"] = chat_result.get("suggested_prompts", prompts)
                with st.chat_message("assistant"):
                    st.write(full)
            except Exception as exc:
                st.error(f"Chat error: {exc}")

        # Re-download (persistent)
        if st.session_state.get("cc_archive_bytes"):
            st.download_button(
                label=f"Re-download {st.session_state.get('cc_archive_name','capsule.zip')}",
                data=st.session_state["cc_archive_bytes"],
                file_name=st.session_state.get("cc_archive_name", "capsule.zip"),
                mime="application/zip",
                key="cc_redl",
            )

    else:
        st.markdown(
            f'<p style="color:{_MU}; font-style:italic;">Weave an agent above to begin the conversation.</p>',
            unsafe_allow_html=True,
        )


# ── Tab 2: Sovereign Wrapper ──────────────────────────────────────────────────

def render_sovereign() -> None:
    col_l, col_r = st.columns([3, 2], gap="medium")

    # ── Left column: inputs ───────────────────────────────────────────────────
    with col_l:
        st.markdown("#### Sovereign Wrapper")
        st.markdown(
            f'<p style="color:{_MU}; font-size:.95rem;">Select the current agent, one exported agent, or a folder of exported agents.</p>',
            unsafe_allow_html=True,
        )

        system_name = st.text_input("System name", value="sovereign_cursiv_system", key="sov_name")
        use_current = st.checkbox(
            "Use current web-created agent if available",
            value=True,
            key="sov_use_current",
        )

        agent_files = st.file_uploader(
            "Choose agent capsule JSON",
            type=["json"],
            accept_multiple_files=True,
            key="sov_files",
        )
        if agent_files:
            st.caption(f"{len(agent_files)} agent file{'s' if len(agent_files) != 1 else ''} selected")

        folder_agents = st.file_uploader(
            "Choose folder of agents",
            type=["json"],
            accept_multiple_files=True,
            key="sov_folder",
        )
        if folder_agents:
            st.caption(f"{len(folder_agents)} folder agent{'s' if len(folder_agents) != 1 else ''} selected")

        st.markdown(
            f'<div class="s-warning">'
            f'<strong>Committing to the evolutionary process is not quick.</strong>'
            f'<p>Training can take several hours to days depending on hardware. The process is worth it.</p>'
            f'<p>Minimal setup: modern laptop, 16GB RAM. NVIDIA GPU with CUDA strongly recommended.<br>'
            f'CPU-only: expect 4–24+ hours. GPU: 1–8 hours depending on dataset size.</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        ack = st.checkbox(
            "I understand the training time and hardware requirements.",
            value=False,
            key="sov_ack",
        )
        wrap_btn = st.button(
            "Wrap into Sovereign AI System",
            key="sov_wrap",
            type="primary",
            disabled=(not ack or not _BACKEND_OK),
        )

    # ── Right column: training flow ───────────────────────────────────────────
    with col_r:
        st.markdown("#### Evo Training Flow")
        phase_ph = st.empty()
        phase_ph.markdown(
            f'<div class="s-progress-label"><span>Waiting</span><span>ETA not started</span></div>',
            unsafe_allow_html=True,
        )
        progress_bar = st.progress(0)
        steps_ph     = st.empty()
        steps_ph.markdown(_steps_html(["Waiting for acknowledgment"], 0), unsafe_allow_html=True)
        result_ph = st.empty()
        dl_ph     = st.empty()

    # ── Wrap action ───────────────────────────────────────────────────────────
    if wrap_btn:
        TRAIN_STEPS = [
            "Long Evo training session",
            "Accuracy follow-up training session",
            "Packaging local system",
        ]
        PHASES = [
            ("Long Evo training session",    "Estimated 4–24+ hours CPU, 1–8 hours GPU", 0,  62, 0),
            ("Accuracy follow-up training",  "Estimated 1–6 hours",                      62, 88, 1),
            ("Packaging Sovereign system",   "Less than a minute",                       88, 100, 2),
        ]

        for label, eta, start, end, step_idx in PHASES:
            phase_ph.markdown(
                f'<div class="s-progress-label">'
                f'<span class="phase">{label}</span>'
                f'<span>{eta}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            steps_ph.markdown(_steps_html(TRAIN_STEPS, step_idx), unsafe_allow_html=True)
            for pct in range(start, end, 2):
                progress_bar.progress(pct / 100)
                time.sleep(0.065)

        steps_ph.markdown(_steps_html(TRAIN_STEPS, len(TRAIN_STEPS)), unsafe_allow_html=True)
        progress_bar.progress(1.0)
        phase_ph.markdown(
            f'<div class="s-progress-label">'
            f'<span style="color:#4CAF50;">Complete</span>'
            f'<span>Ready to download</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        try:
            all_agents   = list(agent_files or []) + list(folder_agents or [])
            webapp_files = _to_webapp_files(all_agents)
            current_sid  = st.session_state.get("session_id", "") if use_current else ""

            payload = {
                "system_name": system_name or "sovereign_cursiv_system",
                "session_id":  current_sid,
                "files":       webapp_files,
            }

            with tempfile.TemporaryDirectory() as tmpdir:
                result = sovereign_payload(payload, workspace=tmpdir)

            s = result.summary
            result_ph.markdown(
                f'<div class="s-result">'
                f'<strong>Sovereign system package ready.</strong>'
                f'<div class="meta">Agents wrapped: <b>{s.get("agent_count", 0)}</b></div>'
                f'<code>{_jdump(s)}</code>'
                f'</div>',
                unsafe_allow_html=True,
            )
            dl_ph.download_button(
                label="Download Sovereign System Zip",
                data=result.archive_bytes,
                file_name=result.archive_name,
                mime="application/zip",
                key="sov_dl",
            )

        except Exception as exc:
            result_ph.error(f"**Could not wrap system.** {exc}")


# ── Tab 3: Oracle Keys ────────────────────────────────────────────────────────

def render_oracle_settings() -> None:
    st.markdown("#### Oracle Key Configuration")
    st.markdown(
        f'<p style="color:{_MU}; margin-bottom:1.4rem;">'
        "Enter your API keys to unlock cloud-powered responses. "
        f'Keys are saved locally to <code>.cursiv/config.json</code> — '
        "never sent anywhere except the provider you choose.</p>",
        unsafe_allow_html=True,
    )

    col_xai, col_oai = st.columns(2, gap="large")

    with col_xai:
        st.markdown(
            f'<p style="color:{_RG}; font-family:Cinzel,serif; '
            f'font-size:.92rem; margin-bottom:.2rem; letter-spacing:.05em;">xAI · Grok</p>',
            unsafe_allow_html=True,
        )
        st.text_input(
            "xAI API Key",
            type="password",
            placeholder="xai-...",
            key="cfg_xai_key",
            label_visibility="collapsed",
        )
        st.caption("Keys available at x.ai/api")

    with col_oai:
        st.markdown(
            f'<p style="color:{_RG}; font-family:Cinzel,serif; '
            f'font-size:.92rem; margin-bottom:.2rem; letter-spacing:.05em;">OpenAI · GPT</p>',
            unsafe_allow_html=True,
        )
        st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            key="cfg_openai_key",
            label_visibility="collapsed",
        )
        st.caption("Keys available at platform.openai.com/api-keys")

    st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)

    btn_c, status_c = st.columns([1, 3], gap="medium")
    with btn_c:
        save_btn = st.button("Save Keys", key="cfg_save", type="primary")
        test_btn = st.button("Test Oracle", key="cfg_test")
    status_ph = status_c.empty()

    if save_btn:
        xai_val    = (st.session_state.get("cfg_xai_key") or "").strip()
        openai_val = (st.session_state.get("cfg_openai_key") or "").strip()
        _save_config({"xai_api_key": xai_val, "openai_api_key": openai_val})
        if xai_val:
            os.environ["XAI_API_KEY"] = xai_val
        elif "XAI_API_KEY" in os.environ:
            del os.environ["XAI_API_KEY"]
        if openai_val:
            os.environ["OPENAI_API_KEY"] = openai_val
        elif "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        active = [n for n, v in [("xAI", xai_val), ("OpenAI", openai_val)] if v]
        if active:
            status_ph.success(f"Keys saved — {' + '.join(active)} ready")
        else:
            status_ph.info("Keys cleared — Ollama or embedded fallback will be used")

    if test_btn:
        try:
            from cursiv_v215.forge.router import OracleRouter
            xai_val    = (st.session_state.get("cfg_xai_key") or "").strip() or None
            openai_val = (st.session_state.get("cfg_openai_key") or "").strip() or None
            router = OracleRouter(xai_api_key=xai_val, openai_api_key=openai_val)
            with st.spinner("Contacting Oracle…"):
                reply = router.call("Reply with exactly three words: ORACLE IS ONLINE", max_tokens=20)
            _LABELS = {"ollama": "Ollama (local)", "xai": "xAI · Grok",
                       "openai": "OpenAI · GPT", "embedded": "Embedded Fallback"}
            label = _LABELS.get(router.active_provider, router.active_provider)
            status_ph.success(f"Oracle active via **{label}** — _{reply[:100]}_")
        except Exception as exc:
            status_ph.error(f"Oracle test failed: {exc}")

    # ── Provider priority diagram ─────────────────────────────────────────────
    st.markdown('<hr class="s-divider">', unsafe_allow_html=True)
    st.markdown("#### Provider Priority")

    has_xai    = bool((st.session_state.get("cfg_xai_key") or "").strip())
    has_openai = bool((st.session_state.get("cfg_openai_key") or "").strip())

    rows = [
        ("1", "Ollama",       "Local · No API needed · always tried first",    True),
        ("2", "xAI · Grok",   "grok-3 · constitutional alignment",              has_xai),
        ("3", "OpenAI · GPT", "gpt-4o-mini · broad capability",                 has_openai),
        ("4", "Embedded",     "Symbolic reasoner · always available offline",   True),
    ]
    html = ""
    for num, name, desc, active in rows:
        col  = _RG if active else _MU
        fade = "" if active else " opacity:.4;"
        html += (
            f'<div style="display:flex;align-items:center;gap:.9rem;'
            f'margin-bottom:.55rem;{fade}">'
            f'<span style="color:{_MU};font-family:Cinzel,serif;font-size:.78rem;'
            f'min-width:.9rem;">{num}</span>'
            f'<span style="color:{col};font-family:Cinzel,serif;font-size:.95rem;'
            f'min-width:7rem;">{name}</span>'
            f'<span style="color:{_MU};font-size:.88rem;">{desc}</span>'
            f'</div>'
        )
    st.markdown(html, unsafe_allow_html=True)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    setup_page()
    _init_keys_from_config()
    render_header()

    create_tab, sovereign_tab, oracle_tab = st.tabs(
        ["Create & Chat", "Sovereign Wrapper", "Oracle Keys"]
    )

    with create_tab:
        render_create_chat()

    with sovereign_tab:
        render_sovereign()

    with oracle_tab:
        render_oracle_settings()


if __name__ == "__main__":
    main()
