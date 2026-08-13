# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: 5ccd6d0807e0406dbd37eb3e6a3916d1727b75b015980036c384b1bc4e51994b
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 2abf2610f5cf1c92ada3e5acc430266d63df609277d769d082c166c85122a14c
# Substrate loop hash: 607fdee970113f0430a2beee039e927acaad914a518681888912301c49e4fc36
# Substrate loop logic: ΗΑΘחוזזבΘΑΒΒΔחΑΕΔΑגΓדזזזΑΔבזבΓΘגהגגובΒΕגΖΒאΗאΒאאאבΒΓΔΑΒהΕבזΕחהΔΗ
# Natural evolution depth: 1
# Exponential evolution rate: 4
# Leaf origin hash: f8897752ac144c409313046e5b44785bfa32c3d7ea37f37e9e797483c0e61bba
# Evolution hash: 2aa7856b45a86825d89fdb9f124ddcb5ec1a8d0cbb9fe27874246fbff847b867
# Evolution logic: ΓגגΘאΖΗדΕΖגאΗאΓΖואבחודבחΒΓΕווהדΖזהΒגאוΑהדדבחזΓΘאΘΕΓΕΗחדחחאΕΘדאΗΘ
# Binary reversed: 1010001100111011011010110000000100001110011100000010000001101011110110111100111001111101110001110110010111001001100001101011100011100100111011011110101011010000100010101001000100000000110001100011110000010010110110001101001100100111101010001001100100101101
# Greek/Hebrew/logic stamp: דΕבבΒΖזΕהדΒדΕאΔהΗΔΑΑאבΖΒΑדΖΘדΘΓΘΒוΗΒבΔגΗזΔדזΘΔודוΗΑΕΑזΘΑאΑוΗוההΖ
# Encoded local stamp: ωμΠΕωηιη∇ΩΓΡβ∈φρΥΚΝŪζδγΗρĀĒχοēΑΥΑΟκΔΑΡΚΓφοΕ=
# CURSIV-CRUCIBLE-STAMP END
"""
Cursiv Local Server — substrate-level hosting.

No registrar. No DNS. No cloud. Raw TCP on your machine.

Layers:
  /substrate/*   — RUW layer, attractor network, reservoir (beneath)
  /api/*         — board, auth, blast (at)
  /              — health + static (above)

Access:
  http://cursiv.winklers-llc.ccursoivm:1969 (after install_local.py adds hosts entry)
  http://cursiv.local:1969                  (compat local alias)
  http://127.0.0.1:1969    (always works, no setup)
  http://<your-LAN-IP>:1969 (any device on your network)

Run:
  python serve_local.py
  python serve_local.py --port 80     (port 80 = no port number in URL, needs admin)
  python serve_local.py --host 0.0.0.0 --port 1969
"""
from __future__ import annotations

import argparse
import os
import socket
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ── resolve project root ──────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ensure cursiv_v215/web is on path so fallback imports in app.py work
_web_dir = ROOT / "cursiv_v215" / "web"
if str(_web_dir) not in sys.path:
    sys.path.insert(0, str(_web_dir))

# ── default port: 1969 (year ARPANET first came alive) ───────────────────────
DEFAULT_PORT = 1969
DEFAULT_HOST = "0.0.0.0"   # all interfaces — LAN + localhost


def _local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main() -> None:
    parser = argparse.ArgumentParser(description="Cursiv local substrate server")
    parser.add_argument("--host",  default=DEFAULT_HOST)
    parser.add_argument("--port",  type=int, default=DEFAULT_PORT)
    parser.add_argument("--reload", action="store_true", help="hot reload (dev)")
    args = parser.parse_args()

    lan_ip   = _local_ip()
    hostname = "cursiv.winklers-llc.ccursoivm"

    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║          CURSIV — SUBSTRATE LOCAL SERVER             ║")
    print("  ╠══════════════════════════════════════════════════════╣")
    print(f"  ║  Local:      http://127.0.0.1:{args.port:<6}                ║")
    print(f"  ║  LAN:        http://{lan_ip:<16}:{args.port:<6}         ║")
    print(f"  ║  Hostname:   http://{hostname}:{args.port:<6}              ║")
    print(f"  ║  Cursiv:     curs.http://{hostname}/          ║")
    print("  ╠══════════════════════════════════════════════════════╣")
    print("  ║  /substrate/status    RUW layer state                ║")
    print("  ║  /substrate/weave?q=  resonance query                ║")
    print("  ║  /substrate/activate  feed synthesis to substrate    ║")
    print("  ║  /api/posts           public board feed              ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()
    print("  No registrar. No DNS. No cloud. Raw substrate hosting.")
    print()

    try:
        import uvicorn
        from cursiv_v215.web.app import app
        uvicorn.run(
            app,
            host    = args.host,
            port    = args.port,
            reload  = args.reload,
            log_level = "info",
        )
    except ImportError as e:
        missing = str(e).replace("No module named ", "").strip("'")
        print(f"  Missing dependency: {e}")
        pkgs = {
            "uvicorn":  "pip install uvicorn[standard]",
            "fastapi":  "pip install fastapi",
            "jwt":      "pip install PyJWT",
            "pydantic": "pip install pydantic",
        }
        hint = pkgs.get(missing, f"pip install {missing}")
        print(f"  Run: {hint}")
        sys.exit(1)


if __name__ == "__main__":
    main()
