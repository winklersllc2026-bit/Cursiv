"""
Cursiv — in-app chat panel (Eye of Horus, native edition).

Replaces the old terminal-spawned CLI with a real chat view living inside
the main Cursiv window, using the exact same core chat() call the terminal
CLI and the web demo both already go through (cursiv_v215/ui/chat_app.py).
No subprocess, no console window -- streaming happens on a background
thread and reaches the UI through Qt signals, which is the only
thread-safe way to touch widgets from outside the main thread.

This is a first pass: it covers the core "talk to Cursiv" experience with
real streaming and API-key status, not the terminal CLI's full command set
(babel, voice, council, strands, postal letters, etc.) -- porting all of
that is a much larger follow-up, not a one-shot change.
"""
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QTextCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QPlainTextEdit,
    QPushButton, QLabel, QSizePolicy,
)

_HERE = Path(__file__).parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from cursiv_v215.ui.chat_app import chat as _cursiv_chat, ROOT as _CHAT_ROOT
    _CHAT_OK = True
    _CHAT_IMPORT_ERROR = ""
except Exception as _e:  # pragma: no cover - surfaced in the UI instead
    _CHAT_OK = False
    _CHAT_IMPORT_ERROR = str(_e)
    _CHAT_ROOT = _ROOT

# Same config file the terminal CLI reads/writes (cursiv_v215/ui/chat_cli.py
# _KEYS_FILE) -- reusing chat_app's own ROOT means keys saved from the
# terminal already show up here with no migration step.
_KEYS_FILE = Path(_CHAT_ROOT) / ".cursiv" / "config.json"


def _load_saved_keys() -> dict:
    try:
        data = json.loads(_KEYS_FILE.read_text(encoding="utf-8"))
        return {k: v for k, v in data.items() if isinstance(v, str)}
    except Exception:
        return {}


# ── Palette (matches cursiv_launcher.py exactly) ────────────────────────────
BG     = "#0b0b12"
BG2    = "#13131e"
BORDER = "#2a2a3f"
GOLD   = "#FFD700"
LGOLD  = "#9B7B20"
SILVER = "#C8C8D4"
SILV2  = "#666680"


class _ChatSignals(QObject):
    chunk   = pyqtSignal(str)   # one streamed text fragment, append to the reply in progress
    done    = pyqtSignal()      # generation finished cleanly
    error   = pyqtSignal(str)   # generation raised an exception


class _ChatInput(QPlainTextEdit):
    """Enter sends, Shift+Enter inserts a newline -- standard chat-app behavior."""

    def __init__(self, on_send, parent=None):
        super().__init__(parent)
        self._on_send = on_send
        self.setFixedHeight(64)
        self.setPlaceholderText("Message Cursiv…")
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {BG2}; color: {SILVER};
                border: 1px solid {BORDER}; border-radius: 8px;
                padding: 8px 10px; font-size: 13px;
            }}
            QPlainTextEdit:focus {{ border-color: {LGOLD}; }}
        """)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
            e.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self._on_send()
            return
        super().keyPressEvent(e)


class ChatPanel(QWidget):
    """
    Self-contained chat view: transcript + input box, wired to the real
    chat() streaming core. Owns its own conversation history for the life
    of the window (not persisted across restarts in this first pass).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history: list[dict] = []          # [{"role": "user"|"assistant", "content": str}]
        self._streaming = False
        self._signals = _ChatSignals()
        self._signals.chunk.connect(self._on_chunk)
        self._signals.done.connect(self._on_done)
        self._signals.error.connect(self._on_error)

        self._build_ui()

        if not _CHAT_OK:
            self._append_system(
                f"Chat core failed to load: {_CHAT_IMPORT_ERROR}\n"
                "This usually means a required package didn't install correctly."
            )
        else:
            keys = _load_saved_keys()
            has_key = any(keys.get(k) for k in ("api_key", "openai_key", "anthropic_key"))
            self._append_system(
                "Talk to Cursiv here — no terminal needed. Runs through Ollama "
                "locally when no cloud key is set, or cascades through your "
                "configured providers otherwise."
                if has_key else
                "Talk to Cursiv here — no terminal needed. No cloud API key is "
                "configured yet, so this runs on your local Ollama model. Set "
                "one from the terminal CLI (key / openai / anthropic <key>) if "
                "you want cloud routing too."
            )

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        header = QLabel("𓂀  Eye of Horus")
        header.setStyleSheet(
            f'color: {GOLD}; font-size: 15px; font-weight: 700;'
            f' font-family: "Segoe UI", "Segoe UI Historic";'
        )
        lay.addWidget(header)

        self._transcript = QTextBrowser()
        self._transcript.setOpenExternalLinks(True)
        self._transcript.setStyleSheet(f"""
            QTextBrowser {{
                background: {BG2}; color: {SILVER};
                border: 1px solid {BORDER}; border-radius: 8px;
                padding: 10px; font-size: 13px;
            }}
        """)
        self._transcript.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        lay.addWidget(self._transcript, 1)

        row = QHBoxLayout()
        row.setSpacing(8)

        self._input = _ChatInput(self._send)
        row.addWidget(self._input, 1)

        self._send_btn = QPushButton("Send")
        self._send_btn.setFixedSize(72, 64)
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background: #2255DD; color: #ffffff;
                font-size: 13px; font-weight: 600;
                border-radius: 8px; border: none;
            }}
            QPushButton:hover    {{ background: #3366EE; }}
            QPushButton:pressed  {{ background: #1144CC; }}
            QPushButton:disabled {{ background: #1a1a2e; color: {SILV2}; }}
        """)
        self._send_btn.clicked.connect(self._send)
        row.addWidget(self._send_btn)

        lay.addLayout(row)

        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {SILV2}; font-size: 10px;")
        lay.addWidget(self._status)

    # ── Transcript rendering ─────────────────────────────────────────────

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )

    def _append_html_block(self, html: str) -> None:
        self._transcript.moveCursor(QTextCursor.MoveOperation.End)
        self._transcript.insertHtml(html)
        self._transcript.moveCursor(QTextCursor.MoveOperation.End)

    def _append_system(self, text: str) -> None:
        self._append_html_block(
            f'<p style="color:{SILV2}; font-size:12px; margin:4px 0 12px 0;">{self._escape(text)}</p>'
        )

    def _append_user(self, text: str) -> None:
        self._append_html_block(
            f'<p style="margin:10px 0 4px 0;">'
            f'<span style="color:{LGOLD}; font-weight:600;">You</span><br>'
            f'<span style="color:{SILVER};">{self._escape(text)}</span></p>'
        )

    def _begin_ai_reply(self) -> None:
        # Opens a paragraph the streamed chunks get appended into; closed in _on_done.
        self._append_html_block(
            f'<p style="margin:4px 0 4px 0;">'
            f'<span style="color:{GOLD}; font-weight:700;">✦ Cursiv</span><br>'
            f'<span style="color:#F0E9D8;">'
        )

    def _append_reply_chunk(self, chunk: str) -> None:
        # Streamed chunks come from the model, not markup -- insert as plain
        # text so partial HTML never lands mid-tag, then keep the cursor at
        # the end so later chunks land in the right place.
        self._transcript.moveCursor(QTextCursor.MoveOperation.End)
        self._transcript.insertPlainText(chunk)
        self._transcript.moveCursor(QTextCursor.MoveOperation.End)

    def _end_ai_reply(self) -> None:
        self._append_html_block("</span></p>")

    # ── Sending ───────────────────────────────────────────────────────────

    def _send(self) -> None:
        if self._streaming:
            return
        text = self._input.toPlainText().strip()
        if not text:
            return
        if not _CHAT_OK:
            self._append_system("Chat core isn't available -- see the message above.")
            return

        self._input.clear()
        self._append_user(text)
        self._history.append({"role": "user", "content": text})

        self._streaming = True
        self._send_btn.setEnabled(False)
        self._status.setText("Cursiv is thinking…")
        self._reply_text = ""
        self._begin_ai_reply()

        keys = _load_saved_keys()
        history_snapshot = list(self._history)  # chat() doesn't need the reply-in-progress

        thread = threading.Thread(
            target=self._run_chat,
            args=(text, history_snapshot, keys),
            daemon=True,
        )
        thread.start()

    def _run_chat(self, text: str, history: list[dict], keys: dict) -> None:
        try:
            gen = _cursiv_chat(
                text,
                history[:-1],   # chat() appends the current user turn itself
                api_key=keys.get("api_key", ""),
                files=None,
                file_access=False,
                root_path=str(_CHAT_ROOT),
                openai_key=keys.get("openai_key", ""),
                confirm_writes=False,
                anthropic_key=keys.get("anthropic_key", ""),
            )
            for chunk in gen:
                if chunk:
                    self._signals.chunk.emit(chunk)
            self._signals.done.emit()
        except Exception as e:
            self._signals.error.emit(str(e))

    # ── Signal handlers (run on the GUI thread) ─────────────────────────

    def _on_chunk(self, chunk: str) -> None:
        self._reply_text += chunk
        self._append_reply_chunk(chunk)

    def _on_done(self) -> None:
        self._end_ai_reply()
        self._history.append({"role": "assistant", "content": self._reply_text})
        self._streaming = False
        self._send_btn.setEnabled(True)
        self._status.setText("")
        self._input.setFocus()

    def _on_error(self, message: str) -> None:
        self._append_html_block(
            f'<span style="color:#ff6666;">[Error: {self._escape(message)}]</span></p>'
        )
        if self._reply_text:
            self._history.append({"role": "assistant", "content": self._reply_text})
        self._streaming = False
        self._send_btn.setEnabled(True)
        self._status.setText("")
