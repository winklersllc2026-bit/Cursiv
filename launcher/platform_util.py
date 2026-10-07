"""
Everything that differs between Windows, Linux and macOS, in one place.

Callers ask for what they want ("open this folder", "where is Ollama", "start
with the computer") and get the right thing for the system they run on.
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")
OS_NAME = "Windows" if IS_WIN else "macOS" if IS_MAC else "Linux"

# Popen flag that hides console windows on Windows (0 = no-op elsewhere).
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def hidden_startupinfo():
    """STARTUPINFO that hides the window on Windows; None elsewhere."""
    if not IS_WIN:
        return None
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return si


def open_path(path: str | Path) -> None:
    """Open a folder or file in the system's file manager / default app."""
    p = str(path)
    if IS_WIN:
        os.startfile(p)  # type: ignore[attr-defined]
    elif IS_MAC:
        subprocess.Popen(["open", p])
    else:
        subprocess.Popen(["xdg-open", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ensure_emoji_font() -> None:
    """Linux: if the system has no emoji font (Raspberry Pi OS, WSL), load the bundled
    Noto Color Emoji so buttons like 📱 and 💾 don't show as empty boxes."""
    if not IS_LINUX:
        return
    from PyQt6.QtGui import QFontDatabase
    if any("emoji" in f.lower() for f in QFontDatabase.families()):
        return
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))
    for cand in (base / "launcher" / "resources" / "fonts" / "NotoColorEmoji.ttf",
                 Path(__file__).parent / "resources" / "fonts" / "NotoColorEmoji.ttf"):
        if cand.exists():
            QFontDatabase.addApplicationFont(str(cand))
            return


# ── Ollama ──────────────────────────────────────────────────────────────────

def ollama_exe() -> Path | None:
    """Path to the ollama program, or None if it isn't installed."""
    found = shutil.which("ollama")
    if found:
        return Path(found)
    candidates = []
    if IS_WIN:
        candidates.append(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe")
    elif IS_MAC:
        candidates += [Path("/Applications/Ollama.app/Contents/Resources/ollama"),
                       Path("/usr/local/bin/ollama"), Path("/opt/homebrew/bin/ollama")]
    else:
        candidates += [Path("/usr/local/bin/ollama"), Path("/usr/bin/ollama"), Path.home() / ".local/bin/ollama"]
    return next((c for c in candidates if c.exists()), None)


OLLAMA_DOWNLOAD = {
    "Windows": "https://ollama.com/download/OllamaSetup.exe",
    "macOS": "https://ollama.com/download/Ollama.dmg",
    "Linux": "https://ollama.com/install.sh",
}[OS_NAME]


def ollama_install_steps() -> str:
    """Plain-language install instructions for this system (shown if automatic install isn't possible)."""
    if IS_WIN:
        return "Download and run the installer from https://ollama.com/download"
    if IS_MAC:
        return ("Download Ollama for Mac from https://ollama.com/download, open the .dmg, drag Ollama to "
                "Applications, then open it once.")
    return "In a terminal, run:  curl -fsSL https://ollama.com/install.sh | sh"


def linux_install_ollama_command() -> list[str] | None:
    """A command that installs Ollama on Linux with a graphical password prompt (pkexec),
    or None if there's no graphical way to ask for the password."""
    if not IS_LINUX:
        return None
    script = "curl -fsSL https://ollama.com/install.sh | sh"
    if shutil.which("pkexec") and shutil.which("curl"):
        return ["pkexec", "sh", "-c", script]
    return None


def start_ollama_app() -> bool:
    """Start Ollama the way a person would (tray app on Windows/Mac, server on Linux)."""
    try:
        if IS_MAC and Path("/Applications/Ollama.app").exists():
            subprocess.Popen(["open", "-a", "Ollama"])
            return True
        exe = ollama_exe()
        if not exe:
            return False
        subprocess.Popen([str(exe), "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=NO_WINDOW)
        return True
    except Exception:
        return False


def stop_ollama() -> None:
    """Stop running Ollama processes (used by Restart Ollama)."""
    try:
        if IS_WIN:
            for name in ("ollama app.exe", "ollama.exe"):
                subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True, creationflags=NO_WINDOW)
        elif IS_MAC:
            subprocess.run(["osascript", "-e", 'quit app "Ollama"'], capture_output=True)
            subprocess.run(["pkill", "-f", "ollama serve"], capture_output=True)
        else:
            subprocess.run(["pkill", "-f", "ollama serve"], capture_output=True)
    except Exception:
        pass


# ── Start with the computer ────────────────────────────────────────────────

def _launch_command() -> list[str]:
    if getattr(sys, "frozen", False):
        appimage = os.environ.get("APPIMAGE")          # Linux AppImage: the outer file, not the temp mount
        return [appimage or sys.executable]
    return [sys.executable, str(Path(__file__).with_name("main.py"))]


def _linux_autostart_file() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "autostart" / "cursiv.desktop"


def _mac_agent_file() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / "com.winklersllc.cursiv.plist"


def set_autostart(on: bool) -> bool:
    """Start Cursiv when the person logs in (Linux/macOS; Windows uses tray.py's registry code)."""
    try:
        cmd = _launch_command() + ["--tray"]
        if IS_LINUX:
            f = _linux_autostart_file()
            if on:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text("[Desktop Entry]\nType=Application\nName=Cursiv\n"
                             f"Exec={' '.join(shlex.quote(c) for c in cmd)}\nX-GNOME-Autostart-enabled=true\n",
                             encoding="utf-8")
            else:
                f.unlink(missing_ok=True)
            return True
        if IS_MAC:
            f = _mac_agent_file()
            if on:
                f.parent.mkdir(parents=True, exist_ok=True)
                args = "".join(f"<string>{c}</string>" for c in cmd)
                f.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                             '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0"><dict>'
                             "<key>Label</key><string>com.winklersllc.cursiv</string>"
                             f"<key>ProgramArguments</key><array>{args}</array>"
                             "<key>RunAtLoad</key><true/></dict></plist>\n", encoding="utf-8")
            else:
                f.unlink(missing_ok=True)
            return True
    except Exception:
        return False
    return False


def autostart_enabled() -> bool:
    if IS_LINUX:
        return _linux_autostart_file().exists()
    if IS_MAC:
        return _mac_agent_file().exists()
    return False


# ── Terminals ──────────────────────────────────────────────────────────────

def open_terminal(command: str, title: str = "Cursiv") -> bool:
    """Run a shell command in a new visible terminal window (best effort on Linux/macOS)."""
    try:
        if IS_MAC:
            esc = command.replace("\\", "\\\\").replace('"', '\\"')
            subprocess.Popen(["osascript", "-e", f'tell application "Terminal" to do script "{esc}"'])
            return True
        if IS_LINUX:
            for term, args in (("x-terminal-emulator", ["-e"]), ("gnome-terminal", ["--"]), ("konsole", ["-e"]),
                               ("xfce4-terminal", ["-x"]), ("xterm", ["-e"])):
                if shutil.which(term):
                    subprocess.Popen([term, *args, "bash", "-lc", command + "; exec bash"])
                    return True
            return False
    except Exception:
        return False
    return False


# ── Updates ────────────────────────────────────────────────────────────────

def update_asset_names() -> list[str]:
    """Release asset names this system can install, best first."""
    import platform
    arm = platform.machine().lower() in ("arm64", "aarch64")
    if IS_WIN:
        return ["Cursiv-Setup-latest.exe"]
    if IS_MAC:
        return ["Cursiv-macOS-arm64.zip" if arm else "Cursiv-macOS-x86_64.zip", "Cursiv-macOS-arm64.zip"]
    return ["Cursiv-Linux-aarch64.AppImage" if arm else "Cursiv-Linux-x86_64.AppImage"]
