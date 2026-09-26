"""
MessageLine widget for displaying single-line status messages with generic styling,
an expandable details button, and auto-hide timeout functionality.
"""

import sys as _sys
import traceback as _traceback
import typing as _typing

import qt_gateway.QtCore as _QtCore
import qt_gateway.QtGui as _QtGui
import qt_gateway.QtWidgets as _QtWidgets


class MessageType:
    """Supported message severity types for MessageLine."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


# Standard pixmap mappings for status severity icons
_ICON_MAP = {
    MessageType.INFO: _QtWidgets.QStyle.SP_MessageBoxInformation,
    MessageType.SUCCESS: _QtWidgets.QStyle.SP_DialogApplyButton,
    MessageType.WARNING: _QtWidgets.QStyle.SP_MessageBoxWarning,
    MessageType.ERROR: _QtWidgets.QStyle.SP_MessageBoxCritical,
}

_TITLE_MAP = {
    MessageType.INFO: "Information",
    MessageType.SUCCESS: "Success",
    MessageType.WARNING: "Warning",
    MessageType.ERROR: "Error",
}

# Default timeout in seconds based on message type relevance (0 = no auto-hide / sticky)
_DEFAULT_TIMEOUTS = {
    MessageType.SUCCESS: 4,  # Transient confirmation
    MessageType.INFO: 7,  # Informational update
    MessageType.WARNING: 12,  # Warning requiring attention
    MessageType.ERROR: 0,  # Error/Exception requires manual view/dismissal
}


class _MessageDetailsDialog(_QtWidgets.QDialog):
    """
    Internal dialog for displaying detailed information or exception tracebacks
    associated with a MessageLine entry.
    """

    def __init__(
        self,
        parent: _typing.Optional[_QtWidgets.QWidget] = None,
        title: str = "Details",
        message: str = "",
        details: str = "",
        message_type: str = MessageType.INFO,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"{title} - Details")
        self.resize(650, 420)
        self.setMinimumSize(450, 250)

        layout = _QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header layout
        header_layout = _QtWidgets.QHBoxLayout()
        header_layout.setSpacing(10)

        # Header Icon
        pixmap_enum = _ICON_MAP.get(
            message_type, _QtWidgets.QStyle.SP_MessageBoxInformation
        )
        icon_pixmap = self.style().standardPixmap(pixmap_enum)

        self._icon_label = _QtWidgets.QLabel(self)
        self._icon_label.setPixmap(
            icon_pixmap.scaled(
                28, 28, _QtCore.Qt.KeepAspectRatio, _QtCore.Qt.SmoothTransformation
            )
        )
        header_layout.addWidget(self._icon_label)

        # Header Message
        self._header_msg_label = _QtWidgets.QLabel(message, self)
        self._header_msg_label.setWordWrap(True)
        header_font = _QtGui.QFont()
        header_font.setBold(True)
        self._header_msg_label.setFont(header_font)
        header_layout.addWidget(self._header_msg_label, 1)

        layout.addLayout(header_layout)

        # Details Text Edit
        self._details_edit = _QtWidgets.QTextEdit(self)
        self._details_edit.setReadOnly(True)
        self._details_edit.setPlainText(details)

        mono_font = _QtGui.QFont("Consolas", 9)
        mono_font.setStyleHint(_QtGui.QFont.Monospace)
        self._details_edit.setFont(mono_font)
        layout.addWidget(self._details_edit, 1)

        # Button box
        btn_layout = _QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(8)

        self._copy_btn = _QtWidgets.QPushButton("Copy to Clipboard", self)
        self._copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(self._copy_btn)

        btn_layout.addStretch()

        self._close_btn = _QtWidgets.QPushButton("Close", self)
        self._close_btn.setDefault(True)
        self._close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self._close_btn)

        layout.addLayout(btn_layout)

    def _copy_to_clipboard(self):
        clipboard = _QtWidgets.QApplication.clipboard()
        if clipboard:
            clipboard.setText(self._details_edit.toPlainText())
            self._copy_btn.setText("Copied!")
            _QtWidgets.QApplication.processEvents()
            _QtCore.QTimer.singleShot(
                2000, lambda: self._copy_btn.setText("Copy to Clipboard")
            )


class MessageLine(_QtWidgets.QFrame):
    """
    A single-line status message widget with generic styling, a prominent details button,
    and automatic timeout auto-hiding.

    Signals:
        details_opened: Emitted when details dialog is displayed.
        dismissed: Emitted when close button is clicked.
        timed_out: Emitted when message auto-hides due to timeout expiry.
    """

    details_opened = _QtCore.Signal()
    dismissed = _QtCore.Signal()
    timed_out = _QtCore.Signal()

    def __init__(
        self,
        parent: _typing.Optional[_QtWidgets.QWidget] = None,
        message: str = "",
        message_type: str = MessageType.INFO,
        details: _typing.Optional[str] = None,
        timeout: _typing.Optional[int] = None,
        dismissable: bool = False,
    ):
        super().__init__(parent)
        self.setObjectName("MessageLine")
        self._message_type = message_type
        self._message_text = message
        self._details_text = details or ""
        self._active_timeout = 0

        # Auto-hide Timer setup
        self._timer = _QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._handle_timeout)

        self._init_ui(dismissable)
        if message:
            self.set_message(message, message_type, details, timeout)
        else:
            self.hide()

        if parent:
            self.setContentsMargins(0, 0, 0, 0)

    def _init_ui(self, dismissable: bool):
        self.setSizePolicy(
            _QtWidgets.QSizePolicy.Expanding, _QtWidgets.QSizePolicy.Fixed
        )

        layout = _QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Left status icon
        self._icon_label = _QtWidgets.QLabel(self)
        self._icon_label.setFixedSize(18, 18)
        layout.addWidget(self._icon_label)

        # Message text label
        self._message_label = _QtWidgets.QLabel(self)
        self._message_label.setSizePolicy(
            _QtWidgets.QSizePolicy.Expanding, _QtWidgets.QSizePolicy.Fixed
        )
        layout.addWidget(self._message_label, 1)

        # Right side prominent details button
        self._details_btn = _QtWidgets.QPushButton("Details...", self)
        self._details_btn.setToolTip("Click to view full details or error traceback...")
        self._details_btn.setCursor(_QtCore.Qt.PointingHandCursor)
        self._details_btn.clicked.connect(self._show_details_dialog)
        layout.addWidget(self._details_btn)

        # Right side dismiss button
        self._dismiss_btn = _QtWidgets.QToolButton(self)
        self._dismiss_btn.setToolTip("Dismiss message")
        self._dismiss_btn.setFixedSize(20, 20)
        close_icon = self.style().standardIcon(_QtWidgets.QStyle.SP_TitleBarCloseButton)
        self._dismiss_btn.setIcon(close_icon)
        self._dismiss_btn.setIconSize(_QtCore.QSize(10, 10))
        self._dismiss_btn.clicked.connect(self.dismiss)
        self._dismiss_btn.setVisible(dismissable)
        layout.addWidget(self._dismiss_btn)

    def set_message(
        self,
        message: str,
        message_type: str = MessageType.INFO,
        details: _typing.Optional[str] = None,
        timeout: _typing.Optional[int] = None,
    ):
        """
        Set the message text, severity type, optional details, and optional timeout in seconds.

        Args:
            message: Status message text.
            message_type: Message severity (info, success, warning, error).
            details: Extended details string or exception traceback.
            timeout: Timeout duration in seconds. If None, uses default timeout for message_type.
                     Set to 0 to disable auto-hide (sticky).
        """
        self._message_text = message
        self._message_type = message_type
        self._details_text = details or ""

        # Update text & tooltip
        self._message_label.setText(message)
        self._message_label.setToolTip(message)

        # Update status icon and dynamic Qt property
        self._apply_type_property(message_type)

        # Toggle details button visibility
        self._details_btn.setVisible(bool(self._details_text))

        # Handle Timeout configuration
        self._timer.stop()
        if timeout is None:
            effective_timeout = _DEFAULT_TIMEOUTS.get(message_type, 0)
        else:
            effective_timeout = max(0, int(timeout))

        self._active_timeout = effective_timeout
        if effective_timeout > 0:
            self._timer.start(effective_timeout * 1000)

        self.show()

    def set_info(
        self,
        message: str,
        details: _typing.Optional[str] = None,
        timeout: _typing.Optional[int] = None,
    ):
        """Display an informational message (default timeout: 7s)."""
        self.set_message(message, MessageType.INFO, details, timeout)

    def set_success(
        self,
        message: str,
        details: _typing.Optional[str] = None,
        timeout: _typing.Optional[int] = None,
    ):
        """Display a success message (default timeout: 4s)."""
        self.set_message(message, MessageType.SUCCESS, details, timeout)

    def set_warning(
        self,
        message: str,
        details: _typing.Optional[str] = None,
        timeout: _typing.Optional[int] = None,
    ):
        """Display a warning message (default timeout: 12s)."""
        self.set_message(message, MessageType.WARNING, details, timeout)

    def set_error(
        self,
        message: str,
        details: _typing.Optional[str] = None,
        timeout: _typing.Optional[int] = None,
    ):
        """Display an error message (default timeout: 0s / sticky)."""
        self.set_message(message, MessageType.ERROR, details, timeout)

    def set_exception(
        self,
        exception: _typing.Union[Exception, str],
        message: _typing.Optional[str] = None,
        timeout: _typing.Optional[int] = None,
    ):
        """
        Display an exception error message with auto-formatted traceback details (default timeout: 0s / sticky).
        """
        if isinstance(exception, Exception):
            exc_msg = message or f"{type(exception).__name__}: {str(exception)}"
            tb_str = "".join(
                _traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
            )
            if not tb_str.strip():
                tb_str = _traceback.format_exc()
        else:
            exc_msg = message or str(exception)
            tb_str = str(exception)

        self.set_error(exc_msg, details=tb_str, timeout=timeout)

    def clear(self):
        """Clear message content, stop active timer, and hide the line."""
        self._timer.stop()
        self._message_text = ""
        self._details_text = ""
        self._message_label.setText("")
        self._details_btn.setVisible(False)
        self.hide()

    def dismiss(self):
        """Hide the message line and emit dismissed signal."""
        self.clear()
        self.dismissed.emit()

    def _show_details_dialog(self):
        """Open the details dialog showing full message and trace/details."""
        if not self._details_text:
            return

        # Pause auto-hide timer while user is viewing details
        if self._timer.isActive():
            self._timer.stop()

        dialog_title = _TITLE_MAP.get(self._message_type, "Information")
        dlg = _MessageDetailsDialog(
            parent=self,
            title=dialog_title,
            message=self._message_text,
            details=self._details_text,
            message_type=self._message_type,
        )
        self.details_opened.emit()
        dlg.exec_()

    def enterEvent(self, event):
        """Pause auto-hide timer when user hovers over the message line."""
        if self._timer.isActive():
            self._timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Resume auto-hide timer when user stops hovering over the message line."""
        if self.isVisible() and self._active_timeout > 0:
            self._timer.start(self._active_timeout * 1000)
        super().leaveEvent(event)

    def _handle_timeout(self):
        self.clear()
        self.timed_out.emit()

    def _apply_type_property(self, message_type: str):
        pixmap_enum = _ICON_MAP.get(
            message_type, _QtWidgets.QStyle.SP_MessageBoxInformation
        )
        pixmap = self.style().standardPixmap(pixmap_enum)
        self._icon_label.setPixmap(
            pixmap.scaled(
                16, 16, _QtCore.Qt.KeepAspectRatio, _QtCore.Qt.SmoothTransformation
            )
        )

        self.setProperty("messageType", message_type)
        self.style().unpolish(self)
        self.style().polish(self)


def run_demo():
    """
    Launch an interactive demo window showcasing MessageLine features including auto-hide timeouts.
    """
    app = _QtWidgets.QApplication.instance() or _QtWidgets.QApplication(_sys.argv)

    window = _QtWidgets.QWidget()
    window.setWindowTitle("MessageLine Widget Demo")
    window.resize(650, 320)

    layout = _QtWidgets.QVBoxLayout(window)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(16)

    # Title label
    title_label = _QtWidgets.QLabel(
        "MessageLine Generic GUI Demo (with Auto-Hide Timeout)", window
    )
    title_font = _QtGui.QFont()
    title_font.setPointSize(11)
    title_font.setBold(True)
    title_label.setFont(title_font)
    layout.addWidget(title_label)

    # MessageLine Instance
    msg_line = MessageLine(window, dismissable=True)
    msg_line.set_info(
        "Welcome to MessageLine! Hover over me to pause auto-hide timer.",
        details="Default timeouts: Success (4s), Info (7s), Warning (12s), Error (0s / Sticky).",
    )
    layout.addWidget(msg_line)

    layout.addStretch()

    # Control buttons container
    controls_layout = _QtWidgets.QHBoxLayout()
    controls_layout.setSpacing(8)

    btn_info = _QtWidgets.QPushButton("Show Info (7s)")
    btn_info.clicked.connect(
        lambda: msg_line.set_info(
            "Project configuration loaded successfully.",
            details="Loaded config from '/pipeline/projects/demo_config.json'.\nFound 12 asset overrides.",
        )
    )
    controls_layout.addWidget(btn_info)

    btn_success = _QtWidgets.QPushButton("Show Success (4s)")
    btn_success.clicked.connect(
        lambda: msg_line.set_success(
            "Render task completed successfully in 00:04:12.",
            details="Output saved to: /renders/shot_010/final_v003.exr (3840x2160)",
        )
    )
    controls_layout.addWidget(btn_success)

    btn_warning = _QtWidgets.QPushButton("Show Warning (12s)")
    btn_warning.clicked.connect(
        lambda: msg_line.set_warning(
            "Asset texture resolution exceeds memory budget.",
            details="Asset 'hero_skin' texture size is 8192x8192 (128 MB RAM). Recommended maximum is 4096x4096.",
        )
    )
    controls_layout.addWidget(btn_warning)

    def trigger_exception():
        try:
            data = {}
            _ = data["missing_key"]
        except Exception as err:
            msg_line.set_exception(
                err, message="Pipeline data processing error! (Sticky)"
            )

    btn_error = _QtWidgets.QPushButton("Trigger Exception (Sticky)")
    btn_error.clicked.connect(trigger_exception)
    controls_layout.addWidget(btn_error)

    btn_clear = _QtWidgets.QPushButton("Clear")
    btn_clear.clicked.connect(msg_line.clear)
    controls_layout.addWidget(btn_clear)

    layout.addLayout(controls_layout)

    window.show()
    return app.exec_()


if __name__ == "__main__":
    _sys.exit(run_demo())
