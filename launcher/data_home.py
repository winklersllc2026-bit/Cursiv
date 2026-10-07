"""
One home for Cursiv's data in the installed app: %USERPROFILE%\\.cursiv

Modules work out their data folder three different ways -- next to the code
({app}\\_internal\\.cursiv), relative to the working directory ({app}\\.cursiv),
or the user's home (%USERPROFILE%\\.cursiv). In the installed app the first two
live inside the program folder, where reinstalls and updates can wipe them.

link_data_folders() runs once at startup of the frozen app:
  1. copies anything from the program-folder .cursiv folders into the home one
     that isn't already there (home is never overwritten -- e.g. the login files
     in runtime\\ are read from home, so home's copies are the real ones),
  2. renames each old folder to .cursiv.moved-<date> (a backup, never deleted),
  3. replaces it with a directory junction to the home folder,
so every module reads and writes %USERPROFILE%\\.cursiv no matter how it finds it.
Source checkouts are left alone (their repo .cursiv is the developer's data).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME_DATA = Path(os.environ.get("CURSIV_DATA_DIR") or (Path.home() / ".cursiv"))


def _is_link(p: Path) -> bool:
    try:
        return p.is_symlink() or p.is_junction()
    except Exception:
        return False


def _points_home(p: Path) -> bool:
    try:
        return _is_link(p) and Path(os.path.realpath(p)).resolve() == HOME_DATA.resolve()
    except Exception:
        return False


def merge_missing(src: Path, dest: Path) -> int:
    """Copy files from src into dest that dest doesn't have yet. Returns the count."""
    copied = 0
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        target = dest / f.relative_to(src)
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        copied += 1
    return copied


def _make_junction(link: Path, target: Path) -> bool:
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       capture_output=True, creationflags=flags)
    return r.returncode == 0 and _is_link(link)


def link_one(old: Path, log: list[str]) -> None:
    """Merge one program-folder .cursiv into home and replace it with a junction."""
    if _points_home(old):
        return
    if _is_link(old):                 # a link somewhere else -- leave it alone
        log.append(f"skip {old}: already a link elsewhere")
        return
    if old.exists():
        n = merge_missing(old, HOME_DATA)
        backup = old.with_name(f".cursiv.moved-{datetime.now():%Y%m%d-%H%M%S}")
        old.rename(backup)
        if not _make_junction(old, HOME_DATA):
            backup.rename(old)        # put it back exactly as it was
            log.append(f"could not link {old}; left in place")
            return
        log.append(f"moved {n} file(s) from {old} -> {HOME_DATA} (backup: {backup.name})")
    else:
        old.parent.mkdir(parents=True, exist_ok=True)
        if _make_junction(old, HOME_DATA):
            log.append(f"linked {old} -> {HOME_DATA}")


def link_data_folders() -> list[str]:
    """Frozen (installed) app only. Safe to call on every startup."""
    log: list[str] = []
    if not getattr(sys, "frozen", False) or sys.platform != "win32":
        return log
    try:
        HOME_DATA.mkdir(parents=True, exist_ok=True)
        app_dir = Path(sys.executable).resolve().parent
        internal = Path(getattr(sys, "_MEIPASS", app_dir / "_internal"))
        for old in (internal / ".cursiv", app_dir / ".cursiv"):
            try:
                link_one(old, log)
            except Exception as exc:
                log.append(f"error for {old}: {exc}")
    except Exception as exc:
        log.append(f"error: {exc}")
    if log:
        try:
            (HOME_DATA / "logs").mkdir(parents=True, exist_ok=True)
            with open(HOME_DATA / "logs" / "data_home.log", "a", encoding="utf-8") as fh:
                for line in log:
                    fh.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {line}\n")
        except Exception:
            pass
    return log
