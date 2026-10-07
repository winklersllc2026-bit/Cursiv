"""
Tools for any AI (Groq, Gemini, local): Cursiv can look things up on this
computer before answering -- "how much space is on my C drive?", "what's in my
Downloads folder?", "read notes.txt and summarize it".

Works the same with every engine: a short routing step picks tool calls as
JSON, Cursiv runs them, and the results are given to the answering model.

Built-in tools are READ-ONLY. Plugins (core/plugins.py) can add more tools.
Sensitive places are never read: Cursiv's own data/keys, SSH/GPG keys, browser
password stores, .env/key/pem files.
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import time
from pathlib import Path
from typing import Callable

MAX_READ = 12000

_DENY = re.compile(
    r"(^|[\\/])(\.cursiv|\.ssh|\.gnupg|\.aws|\.azure|\.kube|\.docker)([\\/]|$)|"
    r"(^|[\\/])(id_rsa|id_ed25519|.*\.pem|.*\.key|.*\.pfx|.*\.p12|\.env(\..*)?|.*secrets?.*|.*password.*|.*credential.*)$|"
    r"Login Data|Cookies|Web Data|Local State|Microsoft[\\/]Credentials|Microsoft[\\/]Protect|"
    r"[\\/]Cursiv[\\/]_internal[\\/]\.cursiv",
    re.I)


def _resolve(path: str) -> Path:
    p = (path or "").strip().strip('"').strip("'")
    aliases = {"downloads": "Downloads", "desktop": "Desktop", "documents": "Documents", "pictures": "Pictures",
               "music": "Music", "videos": "Videos", "home": ""}
    if p.lower() in aliases:
        base = Path.home() / aliases[p.lower()]
        od = Path.home() / "OneDrive" / aliases[p.lower()]
        return od if aliases[p.lower()] and not base.exists() and od.exists() else base
    if re.match(r"^/mnt/([a-z])/", p):                      # WSL path -> Windows
        p = re.sub(r"^/mnt/([a-z])/", lambda m: m.group(1).upper() + ":/", p)
    return Path(os.path.expandvars(p)).expanduser()


def _check(path: Path) -> str | None:
    s = str(path)
    if _DENY.search(s):
        return "That location is private (keys, passwords or Cursiv's own data) — I don't read it."
    return None


def system_info() -> str:
    lines = [f"OS: {platform.system()} {platform.release()} ({platform.version()})",
             f"CPU: {platform.processor() or platform.machine()}, {os.cpu_count()} threads"]
    try:
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MS(); m.dwLength = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        lines.append(f"RAM: {m.ullTotalPhys / 2**30:.1f} GB total, {m.ullAvailPhys / 2**30:.1f} GB free ({m.dwMemoryLoad}% in use)")
    except Exception:
        pass
    if os.name != "nt":
        try:
            if os.path.exists("/proc/meminfo"):
                mi = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo") if l.split()[1:2]}
                lines.append(f"RAM: {mi['MemTotal'] / 2**20:.1f} GB total, {mi.get('MemAvailable', 0) / 2**20:.1f} GB free")
            else:
                import subprocess
                total = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout.strip())
                lines.append(f"RAM: {total / 2**30:.1f} GB total")
            u = shutil.disk_usage(str(Path.home()))
            lines.append(f"Disk (home): {u.free / 2**30:.0f} GB free of {u.total / 2**30:.0f} GB")
        except Exception:
            pass
    for letter in ("CDEFGH" if os.name == "nt" else ""):
        root = f"{letter}:\\"
        if os.path.exists(root):
            try:
                u = shutil.disk_usage(root)
                lines.append(f"Drive {letter}: {u.free / 2**30:.0f} GB free of {u.total / 2**30:.0f} GB")
            except Exception:
                pass
    try:
        from cursiv_v215.core import speed
        lines.append(f"Graphics card memory: {speed.gpu_vram_mb()} MB")
    except Exception:
        pass
    return "\n".join(lines)


def list_folder(path: str = "home") -> str:
    p = _resolve(path)
    if (msg := _check(p)):
        return msg
    if not p.is_dir():
        return f"No folder at {p}"
    items = []
    try:
        entries = sorted(p.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        return f"Windows doesn't allow reading {p}"
    for e in entries[:120]:
        try:
            if e.is_dir():
                items.append(f"[folder] {e.name}")
            else:
                st = e.stat()
                items.append(f"{e.name}  ({st.st_size / 1024:.0f} KB, modified {time.strftime('%Y-%m-%d', time.localtime(st.st_mtime))})")
        except Exception:
            items.append(e.name)
    more = f"\n... and {len(entries) - 120} more" if len(entries) > 120 else ""
    return f"{p} ({len(entries)} items):\n" + "\n".join(items) + more


def read_file(path: str) -> str:
    p = _resolve(path)
    if (msg := _check(p)):
        return msg
    if not p.is_file():
        return f"No file at {p}"
    if p.stat().st_size > 2_000_000:
        return f"{p.name} is too big to read here ({p.stat().st_size / 2**20:.1f} MB)."
    try:
        raw = p.read_bytes()
        if b"\x00" in raw[:4000]:
            return f"{p.name} isn't a text file."
        text = raw.decode("utf-8", errors="replace")
    except Exception as e:
        return f"Couldn't read {p}: {e}"
    cut = f"\n[... {len(text) - MAX_READ} more characters not shown]" if len(text) > MAX_READ else ""
    return f"--- {p} ---\n{text[:MAX_READ]}{cut}"


def find_files(name: str, folder: str = "home") -> str:
    root = _resolve(folder)
    if (msg := _check(root)):
        return msg
    if not root.is_dir():
        return f"No folder at {root}"
    pat = name if any(c in name for c in "*?") else f"*{name}*"
    found, t0 = [], time.time()
    skip = {"node_modules", ".git", "AppData", "$Recycle.Bin", "Windows", "__pycache__", ".venv", "venv"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for f in filenames:
            if Path(f).match(pat):
                full = Path(dirpath) / f
                if not _check(full):
                    found.append(str(full))
        if len(found) >= 40 or time.time() - t0 > 8:
            break
    return ("Found:\n" + "\n".join(found[:40])) if found else f"No files matching {name!r} under {root}"


BUILTIN: dict[str, dict] = {
    "system_info": {"fn": system_info, "description": "This computer's OS, CPU, RAM, free disk space per drive, GPU memory. args: {}"},
    "list_folder": {"fn": list_folder, "description": "List a folder's contents. args: {\"path\": \"C:/Users/...\" or downloads/desktop/documents/home}"},
    "read_file": {"fn": read_file, "description": "Read a text file (first 12,000 characters). args: {\"path\": \"...\"}"},
    "find_files": {"fn": find_files, "description": "Find files by name or pattern. args: {\"name\": \"notes\" or \"*.py\", \"folder\": \"home\"}"},
}

_TRIGGER = re.compile(
    r"\b(file|files|folder|folders|directory|path|drive|disk|storage|space left|free space|ram|memory usage|"
    r"my (computer|pc|laptop|system|desktop|downloads|documents)|downloads|desktop|documents|"
    r"read (this|my|the)|open (my|the)|look (at|in) (my|the)|what'?s in|how much (space|room|ram)|specs?)\b|"
    r"[A-Za-z]:[\\/]|/mnt/[a-z]/|~/|\.(txt|md|py|json|csv|log|ini|ya?ml|html?|js|ts|docx?|xlsx?)\b", re.I)


def all_tools() -> dict[str, dict]:
    out = dict(BUILTIN)
    try:
        from cursiv_v215.core import plugins
        for name, t in plugins.tools().items():
            out.setdefault(name, t)
    except Exception:
        pass
    return out


def might_need_tools(text: str) -> bool:
    if _TRIGGER.search(text or ""):
        return True
    try:
        from cursiv_v215.core import plugins
        low = (text or "").lower()
        return any(name.replace("_", " ") in low or name in low for name in plugins.tools())
    except Exception:
        return False


_ROUTER = """You decide whether answering the user's message needs information from their computer.
Available tools:
{tools}

Reply with JSON only: {{"calls": [{{"tool": "<name>", "args": {{...}}}}]}} with at most 3 calls, or {{"calls": []}} if no tool is needed.
Use Windows paths. Home folder: {home}. Don't guess file names you weren't told -- list or search first."""


_SYS_Q = re.compile(r"\b(disk|drive|storage|space|ram|memory usage|how much memory|specs?|cpu|processor|gpu|"
                    r"graphics card|vram|system info|my (computer|pc|laptop)'?s? (specs|info))\b", re.I)
_FOLDER_Q = re.compile(r"\b(what'?s|what is|list|show)\b.{0,20}\b(in )?(my )?(downloads|desktop|documents|pictures)\b", re.I)


def quick_plan(text: str) -> list[dict]:
    """Obvious questions get their tool directly -- no AI needed to decide."""
    calls = []
    m = _FOLDER_Q.search(text or "")
    if m:
        calls.append({"tool": "list_folder", "args": {"path": m.group(3).lower()}})
    if _SYS_Q.search(text or "") and not re.search(r"\b(remember|memories)\b", text or "", re.I):
        calls.append({"tool": "system_info", "args": {}})
    return calls


def plan(text: str, ask: Callable[[list[dict]], str]) -> list[dict]:
    quick = quick_plan(text)
    if quick and not re.search(r"\b(read|open|file|find|search for)\b|[A-Za-z]:[\\/]|\.\w{2,4}\b", text or "", re.I):
        return quick
    tools = all_tools()
    desc = "\n".join(f"- {n}: {t['description']}" for n, t in tools.items())
    try:
        raw = ask([{"role": "system", "content": _ROUTER.format(tools=desc, home=str(Path.home()))},
                   {"role": "user", "content": text[:2000]}]) or ""
        m = re.search(r"\{.*\}", raw, re.S)
        calls = json.loads(m.group(0)).get("calls", []) if m else []
    except Exception:
        return quick
    calls = [c for c in calls[:3] if isinstance(c, dict) and c.get("tool") in tools]
    return calls or quick


def run(calls: list[dict]) -> list[tuple[str, str]]:
    tools = all_tools()
    out = []
    for c in calls:
        t = tools[c["tool"]]
        args = c.get("args") or {}
        try:
            res = t["fn"](**args) if isinstance(args, dict) else t["fn"](args)
        except TypeError:
            try:
                res = t["fn"](*args.values()) if isinstance(args, dict) else t["fn"]()
            except Exception as e:
                res = f"Tool error: {e}"
        except Exception as e:
            res = f"Tool error: {type(e).__name__}: {e}"
        label = c["tool"] + (" " + ", ".join(str(v) for v in args.values())[:80] if isinstance(args, dict) and args else "")
        out.append((label, str(res)[:MAX_READ + 500]))
    return out


def context_for(results: list[tuple[str, str]]) -> str:
    return "## Tool results (read from this computer just now — use them, quote real names and numbers)\n" + \
           "\n\n".join(f"### {label}\n{res}" for label, res in results)
