"""
Cursiv Guardian — Windows Service wrapper.

Install:   python services/guardian_service.py install
Start:     python services/guardian_service.py start
Stop:      python services/guardian_service.py stop
Remove:    python services/guardian_service.py remove
Debug run: python services/guardian_service.py debug
"""

import sys
import time
import threading
import logging
from pathlib import Path

# ── Ensure repo root is importable ──────────────────────────────────────────
_HERE = Path(__file__).parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── Logging ──────────────────────────────────────────────────────────────────
_LOG_DIR = Path.home() / ".cursiv" / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(_LOG_DIR / "guardian_service.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("CursivGuardian")


try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    _WIN32_OK = True
except ImportError:
    _WIN32_OK = False


# ── Service workers ───────────────────────────────────────────────────────────

def _run_guardian(stop_evt: threading.Event):
    """Run Temple Guardian in a loop until stop_evt is set."""
    try:
        from cursiv_v215.guardian.temple_guardian import TempleGuardian
        guardian = TempleGuardian()
        log.info("Guardian started.")
        while not stop_evt.is_set():
            try:
                guardian.tick()
            except Exception as exc:
                log.warning("Guardian tick error: %s", exc)
            stop_evt.wait(timeout=5)
        log.info("Guardian stopped.")
    except ImportError as exc:
        log.error("Could not import TempleGuardian: %s", exc)


def _run_tracker(stop_evt: threading.Event):
    """Run Memory Tracker in a loop until stop_evt is set."""
    try:
        from cursiv_v215.memory.tracker import MemoryTracker
        tracker = MemoryTracker()
        log.info("Tracker started.")
        while not stop_evt.is_set():
            try:
                tracker.tick()
            except Exception as exc:
                log.warning("Tracker tick error: %s", exc)
            stop_evt.wait(timeout=10)
        log.info("Tracker stopped.")
    except ImportError as exc:
        log.error("Could not import MemoryTracker: %s", exc)


# ── Windows Service class ─────────────────────────────────────────────────────

if _WIN32_OK:
    class CursivGuardianService(win32serviceutil.ServiceFramework):
        _svc_name_         = "CursivGuardian"
        _svc_display_name_ = "Cursiv Guardian Service"
        _svc_description_  = (
            "Runs the Cursiv Guardian Firewall and Memory Tracker silently in "
            "the background. Required for Cursiv AI system integrity monitoring."
        )

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self._stop_evt  = threading.Event()
            self._hWaitStop = win32event.CreateEvent(None, 0, 0, None)

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self._stop_evt.set()
            win32event.SetEvent(self._hWaitStop)

        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            log.info("Service starting...")
            self._run()

        def _run(self):
            threads = [
                threading.Thread(target=_run_guardian, args=(self._stop_evt,), daemon=True),
                threading.Thread(target=_run_tracker,  args=(self._stop_evt,), daemon=True),
            ]
            for t in threads:
                t.start()

            # Wait for stop signal
            win32event.WaitForSingleObject(self._hWaitStop, win32event.INFINITE)

            self._stop_evt.set()
            for t in threads:
                t.join(timeout=15)
            log.info("Service stopped.")


# ── Standalone debug runner (no Windows Service infrastructure needed) ────────

def _debug_run():
    """Run guardian + tracker in-process for testing."""
    print("Running in debug mode — Ctrl-C to stop.")
    stop_evt = threading.Event()
    threads = [
        threading.Thread(target=_run_guardian, args=(stop_evt,), daemon=True, name="Guardian"),
        threading.Thread(target=_run_tracker,  args=(stop_evt,), daemon=True, name="Tracker"),
    ]
    for t in threads:
        t.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_evt.set()
    for t in threads:
        t.join(timeout=15)
    print("Done.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        _debug_run()
    elif _WIN32_OK:
        win32serviceutil.HandleCommandLine(CursivGuardianService)
    else:
        print(
            "pywin32 is not installed — cannot manage Windows Service.\n"
            "Run:  pip install pywin32\n"
            "Or use 'debug' mode:  python services/guardian_service.py debug"
        )
        sys.exit(1)
