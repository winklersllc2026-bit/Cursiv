"""
Cursiv — in-app chat panel (Eye of Horus, native edition).

Replaces the old terminal-spawned CLI with a real chat view living inside
the main Cursiv window. Plain messages go through the exact same core
chat() call the terminal CLI and web demo already use
(cursiv_v215/ui/chat_app.py); the terminal CLI's ~40 built-in commands
(key management, council, Babel, Codex, strand memory, blast, postal
letters, voice, etc.) are routed through chat_commands.py, which calls the
same underlying functions the CLI does. No subprocess, no console window
-- everything streams on a background thread and reaches the UI through
Qt signals, the only thread-safe way to touch widgets from another thread.

A handful of commands need a real dialog rather than a single line of text
(composing a sealed letter, the family Legacy Vault, board login/register,
voice recording, pasting a clipboard image) -- those are intercepted here,
on the main thread, before anything reaches the command router.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QTextCursor, QGuiApplication
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QPlainTextEdit,
    QPushButton, QLabel, QSizePolicy, QInputDialog, QLineEdit, QMessageBox,
)

_HERE = Path(__file__).parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    import chat_commands as cc
    _CHAT_OK = True
    _CHAT_IMPORT_ERROR = ""
except Exception as _e:  # pragma: no cover - surfaced in the UI instead
    _CHAT_OK = False
    _CHAT_IMPORT_ERROR = str(_e)
    cc = None  # type: ignore

if _CHAT_OK:
    _cursiv_chat = cc._chat
    _CHAT_ROOT = cc._CHAT_ROOT
    _RATE_SENTINEL = cc.RATE_SENTINEL
else:
    _CHAT_ROOT = _ROOT
    _RATE_SENTINEL = object()

# ── Palette (matches cursiv_launcher.py exactly) ────────────────────────────
BG     = "#0b0b12"
BG2    = "#13131e"
BORDER = "#2a2a3f"
GOLD   = "#FFD700"
LGOLD  = "#9B7B20"
SILVER = "#C8C8D4"
SILV2  = "#666680"


def _load_saved_keys() -> dict:
    import json
    keys_file = Path(_CHAT_ROOT) / ".cursiv" / "config.json"
    try:
        data = json.loads(keys_file.read_text(encoding="utf-8"))
        return {k: v for k, v in data.items() if isinstance(v, str)}
    except Exception:
        return {}


class _ChatSignals(QObject):
    chunk = pyqtSignal(str)             # one streamed text fragment
    done  = pyqtSignal()                # generation finished cleanly
    error = pyqtSignal(str)             # generation raised an exception
    image = pyqtSignal(str)             # a local image path to render inline
    voice_result = pyqtSignal(str, bool)   # transcribed text, auto_send


class _ChatInput(QPlainTextEdit):
    """Enter sends, Shift+Enter inserts a newline -- standard chat-app behavior."""

    def __init__(self, on_send, on_paste_image, parent=None):
        super().__init__(parent)
        self._on_send = on_send
        self._on_paste_image = on_paste_image
        self.setFixedHeight(64)
        self.setPlaceholderText("Message Cursiv… (try: council, codex, babel, help)")
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

    def insertFromMimeData(self, source) -> None:
        if source.hasImage() and self._on_paste_image(source.imageData()):
            return
        super().insertFromMimeData(source)


class ChatPanel(QWidget):
    """
    Self-contained chat view: transcript + input box, wired to the real
    chat() streaming core and the full command router. cfg/history persist
    for the life of the window (not saved across restarts in this pass).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history: list[dict] = []          # [{"role": "user"|"assistant", "content": str}]
        self._streaming = False
        self._reply_text = ""
        self._pending_history_append: Optional[list[tuple[str, str]]] = None
        self._signals = _ChatSignals()
        self._signals.chunk.connect(self._on_chunk)
        self._signals.done.connect(self._on_done)
        self._signals.error.connect(self._on_error)
        self._signals.image.connect(self._on_image)
        self._signals.voice_result.connect(self._on_voice_result)

        self._cfg: dict = cc._default_cfg() if _CHAT_OK else {}
        if _CHAT_OK:
            keys = _load_saved_keys()
            self._cfg["api_key"] = keys.get("api_key", "")
            self._cfg["openai_key"] = keys.get("openai_key", "")
            self._cfg["anthropic_key"] = keys.get("anthropic_key", "")
            self._cfg["postal_user"] = "joshua"

        self._build_ui()

        if not _CHAT_OK:
            self._append_system(
                f"Chat core failed to load: {_CHAT_IMPORT_ERROR}\n"
                "This usually means a required package didn't install correctly."
            )
        else:
            has_key = any(self._cfg.get(k) for k in ("api_key", "openai_key", "anthropic_key"))
            self._append_system(
                "Talk to Cursiv here — no terminal needed. Runs through Ollama "
                "locally when no cloud key is set, or cascades through your "
                "configured providers otherwise. Type 'help' for the full command list."
                if has_key else
                "Talk to Cursiv here — no terminal needed. No cloud API key is "
                "configured yet, so this runs on your local Ollama model. Type "
                "'key xai-...', 'openai sk-...', or 'anthropic sk-ant-...' to add one. "
                "Type 'help' for the full command list."
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

        self._input = _ChatInput(self._send, self._handle_pasted_image)
        row.addWidget(self._input, 1)

        self._voice_btn = QPushButton("🎙")
        self._voice_btn.setFixedSize(40, 64)
        self._voice_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._voice_btn.setToolTip("Record 5s of audio and transcribe it into the input box")
        self._voice_btn.setStyleSheet(self._icon_btn_style())
        # clicked emits clicked(bool) -- a bare connect would bind that bool
        # to raw_text (same trap as the Getting Started download buttons),
        # so wrap it to call with no arguments and let the defaults apply.
        self._voice_btn.clicked.connect(lambda: self._start_voice())
        row.addWidget(self._voice_btn)

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

    def _icon_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background: transparent; color: {GOLD}; font-size: 16px;
                border: 1px solid {BORDER}; border-radius: 8px;
            }}
            QPushButton:hover    {{ background: rgba(212,175,55,0.08); border-color: {LGOLD}; }}
            QPushButton:pressed  {{ background: rgba(212,175,55,0.15); }}
            QPushButton:disabled {{ color: {SILV2}; }}
        """

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
            f'<span style="color:#F0E9D8; white-space:pre-wrap;">'
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

    def _append_image(self, path: str) -> None:
        import base64
        try:
            data = Path(path).read_bytes()
        except Exception:
            return
        b64 = base64.b64encode(data).decode()
        ext = Path(path).suffix.lstrip(".").lower() or "png"
        self._append_html_block(
            f'<p style="margin:4px 0 12px 0;">'
            f'<img src="data:image/{ext};base64,{b64}" style="max-width:480px; border-radius:8px;" />'
            f'</p>'
        )

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

        # A handful of commands need a real dialog, not a single line of
        # text -- intercept them here on the main thread before anything
        # reaches the background-thread command router.
        if self._try_dialog_command(text):
            self._input.clear()
            return

        self._input.clear()
        self._append_user(text)
        self._begin_turn()

        # Snapshot deliberately excludes this turn -- built-in commands
        # (anchor this, etc.) inspect history for the *prior* exchange, and
        # the terminal CLI never adds command text to history at all, only
        # real chat turns. Whether/what to append is decided in _run_turn
        # once we know if this resolved to a command or a plain chat call.
        history_snapshot = list(self._history)
        thread = threading.Thread(
            target=self._run_turn, args=(text, history_snapshot), daemon=True,
        )
        thread.start()

    def _begin_turn(self) -> None:
        self._streaming = True
        self._send_btn.setEnabled(False)
        self._voice_btn.setEnabled(False)
        self._status.setText("Cursiv is thinking…")
        self._reply_text = ""
        self._begin_ai_reply()

    def _run_turn(self, text: str, history: list[dict]) -> None:
        try:
            force_provider, stripped = cc.hey_prefix(text)
            result = None
            if not force_provider:
                result = cc.handle_command(text, self._cfg, history)

            if result is not None:
                self._deliver_result(result, history)
                return

            # No built-in command matched (or a "hey <provider>" prefix
            # forced routing) -- fall through to the default streaming chat,
            # the same core the terminal CLI's plain-message path uses.
            # `history` here is the snapshot from *before* this turn, so it
            # goes straight to chat() -- which appends the current user
            # turn itself -- with nothing to trim off the end.
            gen = _cursiv_chat(
                stripped, history,
                api_key=self._cfg.get("api_key", ""), files=None,
                file_access=self._cfg.get("file_access", False),
                root_path=self._cfg.get("workspace", str(_CHAT_ROOT)),
                openai_key=self._cfg.get("openai_key", ""),
                confirm_writes=False,
                anthropic_key=self._cfg.get("anthropic_key", ""),
                force_provider=force_provider,
            )
            self._cfg["last_user_msg"] = stripped
            full = ""
            for chunk in gen:
                if chunk:
                    full += chunk
                    self._signals.chunk.emit(chunk)
            self._signals.done.emit()
            self._pending_history_append = [("user", stripped), ("assistant", full)]
        except Exception as e:
            self._signals.error.emit(str(e))

    def _deliver_result(self, result, history: list[dict]) -> None:
        """Runs on the background thread -- streams a command's TextResult/StreamResult."""
        if isinstance(result, cc.TextResult):
            if result.text:
                self._signals.chunk.emit(result.text)
            if result.image_path:
                self._signals.image.emit(result.image_path)
            self._signals.done.emit()
            self._pending_history_append = None   # commands don't pollute chat history
            return

        # StreamResult
        self._signals.chunk.emit(result.intro + "\n\n")
        full = ""
        try:
            for chunk in result.generator:
                if chunk and chunk != _RATE_SENTINEL:
                    full += chunk
                    self._signals.chunk.emit(chunk)
        except Exception as e:
            self._signals.error.emit(str(e))
            return
        if result.on_complete:
            try:
                result.on_complete(full)
            except Exception:
                pass
        self._signals.done.emit()
        self._pending_history_append = None

    # ── Signal handlers (run on the GUI thread) ─────────────────────────

    def _on_chunk(self, chunk: str) -> None:
        self._reply_text += chunk
        self._append_reply_chunk(chunk)

    def _on_image(self, path: str) -> None:
        self._append_image(path)

    def _on_done(self) -> None:
        self._end_ai_reply()
        for role, content in (getattr(self, "_pending_history_append", None) or []):
            self._history.append({"role": role, "content": content})
        self._pending_history_append = None
        self._streaming = False
        self._send_btn.setEnabled(True)
        self._voice_btn.setEnabled(True)
        self._status.setText("")
        self._input.setFocus()

    def _on_error(self, message: str) -> None:
        self._append_html_block(
            f'<span style="color:#ff6666;">[Error: {self._escape(message)}]</span></p>'
        )
        # _pending_history_append is only ever set right before a clean
        # done.emit() (see _run_turn/_deliver_result), so an error here
        # means it's still None -- a failed generation never produced a
        # complete exchange, so nothing gets added to history.
        self._pending_history_append = None
        self._streaming = False
        self._send_btn.setEnabled(True)
        self._voice_btn.setEnabled(True)
        self._status.setText("")

    # ── Commands that need a real dialog ─────────────────────────────────

    def _try_dialog_command(self, text: str) -> bool:
        """Returns True if `text` was handled here (a dialog was shown)."""
        cmd = text.strip().lower()

        if cmd == "write to" or cmd.startswith("write to "):
            self._open_postal_compose(text[9:].strip())
            return True

        if cmd == "legacy" or cmd.startswith("legacy "):
            # "legacy import <path>" is a plain text command (handled by
            # chat_commands); bare "legacy"/"legacy <anything else>" opens
            # the vault dialog, matching the terminal's natural-language
            # gate but with real structured login fields instead.
            if cmd.startswith("legacy import "):
                return False
            self._open_legacy_vault()
            return True

        if cmd.startswith("blast login") or cmd.startswith("blast register"):
            self._open_blast_auth(is_register=cmd.startswith("blast register"))
            return True

        if cmd in ("voice", "listen") or cmd.startswith("voice ") or cmd.startswith("listen "):
            # Typed as a command (matching the terminal CLI exactly) --
            # auto-send the transcription, same as the CLI falling straight
            # through to model routing with no review step.
            self._start_voice(raw_text=text, auto_send=True)
            return True

        if cmd == "paste":
            self._paste_from_clipboard()
            return True

        return False

    def _open_postal_compose(self, recipient_hint: str) -> None:
        from postal_compose_dialog import PostalComposeDialog
        dlg = PostalComposeDialog(self._cfg.get("postal_user", "joshua"), recipient_hint, self)
        if dlg.exec() and dlg.result_text:
            self._append_user(f"write to {recipient_hint}".strip())
            self._begin_ai_reply()
            self._append_reply_chunk(dlg.result_text)
            self._end_ai_reply()

    def _open_legacy_vault(self) -> None:
        from legacy_vault_dialog import LegacyVaultDialog
        dlg = LegacyVaultDialog(self._cfg, self)
        dlg.exec()

    def _open_blast_auth(self, is_register: bool) -> None:
        username, ok = QInputDialog.getText(self, "Cursiv Board", "Username:")
        if not ok or not username.strip():
            return
        password, ok = QInputDialog.getText(
            self, "Cursiv Board", "Password:", QLineEdit.EchoMode.Password
        )
        if not ok or not password:
            return
        if is_register:
            confirm, ok = QInputDialog.getText(
                self, "Cursiv Board", "Confirm password:", QLineEdit.EchoMode.Password
            )
            if not ok:
                return
            if confirm != password:
                QMessageBox.warning(self, "Cursiv Board", "Passwords do not match.")
                return

        self._append_user(f"blast {'register' if is_register else 'login'} {username.strip()}")
        self._begin_turn()
        threading.Thread(
            target=self._run_blast_auth, args=(is_register, username.strip(), password), daemon=True,
        ).start()

    def _run_blast_auth(self, is_register: bool, username: str, password: str) -> None:
        try:
            result = cc.blast_register(username, password) if is_register else cc.blast_login(username, password)
            self._signals.chunk.emit(result.text)
            self._signals.done.emit()
        except Exception as e:
            self._signals.error.emit(str(e))

    # ── Voice ─────────────────────────────────────────────────────────────

    def _start_voice(self, raw_text: str = "", auto_send: bool = False) -> None:
        if self._streaming:
            return
        low = raw_text.strip().lower()
        raw_mode = low in ("listen",) or low.startswith("listen ")
        duration = 5.0
        sub = ""
        if low.startswith("voice "):
            sub = low[6:].strip()
        elif low.startswith("listen "):
            sub = low[7:].strip()
        if sub == "raw":
            raw_mode = True
        elif sub:
            try:
                duration = max(1.0, min(float(sub), 60.0))
            except ValueError:
                pass

        self._voice_btn.setEnabled(False)
        self._send_btn.setEnabled(False)
        self._streaming = True
        self._status.setText(f"🎙 Listening {duration:.0f}s… speak now")
        threading.Thread(
            target=self._run_voice, args=(duration, raw_mode, auto_send), daemon=True,
        ).start()

    def _run_voice(self, duration: float, raw_mode: bool, auto_send: bool) -> None:
        try:
            result = cc.voice_turn(self._cfg, duration_s=duration, raw_mode=raw_mode)
            self._signals.voice_result.emit(result.text, auto_send)
        except Exception as e:
            self._signals.error.emit(str(e))

    def _on_voice_result(self, text: str, auto_send: bool) -> None:
        self._streaming = False
        self._send_btn.setEnabled(True)
        self._voice_btn.setEnabled(True)
        self._status.setText("")
        if not text:
            return
        self._input.setPlainText(text)
        if auto_send:
            self._send()
        else:
            cursor = self._input.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self._input.setTextCursor(cursor)
            self._input.setFocus()

    # ── Paste image ───────────────────────────────────────────────────────

    def _handle_pasted_image(self, qimage) -> bool:
        if qimage is None or qimage.isNull():
            return False
        self._paste_qimage(qimage)
        return True

    def _paste_from_clipboard(self) -> None:
        qimage = QGuiApplication.clipboard().image()
        if qimage.isNull():
            self._append_system("Clipboard is empty or doesn't contain an image.")
            return
        self._paste_qimage(qimage)

    def _paste_qimage(self, qimage) -> None:
        from PyQt6.QtCore import QBuffer, QByteArray
        buf = QByteArray()
        qbuf = QBuffer(buf)
        qbuf.open(QBuffer.OpenModeFlag.WriteOnly)
        qimage.save(qbuf, "PNG")
        png_bytes = bytes(buf)
        width, height = qimage.width(), qimage.height()

        self._append_user("[pasted image]")
        self._begin_turn()
        threading.Thread(
            target=self._run_paste_analysis, args=(png_bytes, width, height), daemon=True,
        ).start()

    def _run_paste_analysis(self, png_bytes: bytes, width: int, height: int) -> None:
        try:
            result = cc.analyze_pasted_image(png_bytes, self._cfg, width, height)
            self._signals.chunk.emit(result.text)
            if result.image_path:
                self._signals.image.emit(result.image_path)
            self._signals.done.emit()
        except Exception as e:
            self._signals.error.emit(str(e))
