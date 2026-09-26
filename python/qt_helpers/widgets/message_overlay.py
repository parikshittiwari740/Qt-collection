"""
qt_helpers.widgets.message_overlay
==================================

Blocking message overlay widget providing a full-parent semi-transparent scrim
and centered message card to block user input and display progress or status
updates during long-running tasks.
"""

import contextlib as _contextlib
import sys as _sys
import time as _time
import typing as _typing

import qt_gateway.QtCore as _QtCore
import qt_gateway.QtGui as _QtGui
import qt_gateway.QtWidgets as _QtWidgets

import qt_helpers.resources as _resources
import qt_helpers.utils as _utils


class BlockingMessageOverlay(_QtWidgets.QFrame):
    """
    A semi-transparent, input-blocking overlay for showing a centered
    message on top of a parent widget.

    The overlay itself spans the full parent and intercepts all mouse and
    keyboard input while visible (the "scrim"). A smaller, centered card
    inside it holds the actual message and provides a clean popup appearance.

    Automatically recalculates geometry and layout on parent resize events.
    """

    def __init__(self, parent: _QtWidgets.QWidget):
        """
        Initialize the blocking overlay on the specified parent widget.

        Args:
            parent: The parent QWidget over which the overlay will be placed.
        """
        super().__init__(parent=parent)
        self.setObjectName("blocking_message_overlay")

        self._card = _QtWidgets.QFrame(self)
        self._card.setObjectName("blocking_message_card")

        self._setup_card()

        # Watch the parent for resize events to re-lay-out the scrim and card
        parent.installEventFilter(self)
        self.hide()

    def _apply_theme_colors(self) -> None:
        """
        Derive overlay colors from the current QPalette instead of hardcoding them,
        ensuring the overlay follows the active theme (dark, light, or OS-driven) automatically.
        """
        parent = self.parentWidget()
        palette = parent.palette() if parent else self.palette()

        window_color = palette.color(_QtGui.QPalette.ColorRole.Window)
        text_color = palette.color(_QtGui.QPalette.ColorRole.WindowText)
        border_color = palette.color(_QtGui.QPalette.ColorRole.Mid)

        # Scrim: dim toward black if light theme, toward white/black if dark theme
        is_dark_theme = window_color.lightness() < 128
        scrim_alpha = 110 if is_dark_theme else 70
        self.setStyleSheet(
            f"QFrame#blocking_message_overlay {{"
            f" background-color: rgba(0, 0, 0, {scrim_alpha}); }}"
        )

        # Card: translucent version of window/base color with palette text/border
        card_bg = _QtGui.QColor(window_color)
        card_bg.setAlpha(235)
        border = _QtGui.QColor(border_color)
        border.setAlpha(200)

        self._card.setStyleSheet(
            f"""
            QFrame#blocking_message_card {{
                background-color: rgba({card_bg.red()}, {card_bg.green()}, {card_bg.blue()}, {card_bg.alpha()});
                border: 1px solid rgba({border.red()}, {border.green()}, {border.blue()}, {border.alpha()});
                border-radius: 10px;
            }}
            QFrame#blocking_message_card QLabel {{
                background: transparent;
                color: {text_color.name()};
            }}
            """
        )

    def _setup_card(self) -> None:
        """Construct the centered message card and its child labels."""
        card_layout = _QtWidgets.QVBoxLayout(self._card)

        self._icon_label = _QtWidgets.QLabel()
        self._icon_label.setAlignment(_QtCore.Qt.AlignmentFlag.AlignCenter)
        self._icon_label.hide()

        self._message_label = _QtWidgets.QLabel()
        self._message_label.setWordWrap(True)
        self._message_label.setAlignment(_QtCore.Qt.AlignmentFlag.AlignCenter)

        font = self._message_label.font()
        font.setPointSize(font.pointSize() + 4)
        font.setWeight(_QtGui.QFont.Weight.DemiBold)
        self._message_label.setFont(font)

        card_layout.addStretch()
        card_layout.addWidget(self._icon_label)
        card_layout.addWidget(self._message_label)
        card_layout.addStretch()

        # Soft drop shadow to lift the card off the dimmed scrim
        shadow = _QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 4)
        shadow.setColor(_QtGui.QColor(0, 0, 0, 160))
        self._card.setGraphicsEffect(shadow)

    def eventFilter(self, watched: _QtCore.QObject, event: _QtCore.QEvent) -> bool:
        """Filter parent events to adjust geometry on parent resize."""
        if (
            watched is self.parentWidget()
            and event.type() == _QtCore.QEvent.Type.Resize
        ):
            if self.isVisible():
                self._update_geometry()
        return super().eventFilter(watched, event)

    def _update_geometry(self) -> None:
        """Update overlay geometry to match parent widget and center the card."""
        parent = self.parentWidget()
        if not parent:
            return

        self.setGeometry(parent.rect())

        card_width = max(320, min(int(self.width() * 0.5), 520))
        card_height = max(120, min(int(self.height() * 0.3), 220))
        x = (self.width() - card_width) // 2
        y = (self.height() - card_height) // 2
        self._card.setGeometry(x, y, card_width, card_height)

    def show_warning(self, message: str) -> None:
        """
        Display a blocking overlay with a warning icon and the given message.

        Args:
            message: Warning text to display.
        """
        self._show_message(message, icon=_QtWidgets.QStyle.SP_MessageBoxWarning)

    def show_busy(self, message: str) -> None:
        """
        Display a blocking overlay with an hourglass busy icon and the given message.

        Args:
            message: Busy/loading text to display.
        """
        self._show_message(message, icon=_resources.ResourceIcon.HOURGLASS_COLORED)

    def show_message(self, message: str) -> None:
        """
        Display a blocking overlay with the given message (no icon).

        Args:
            message: Status text to display.
        """
        self._show_message(message)

    def _show_message(
        self,
        message: str,
        icon: _typing.Optional[
            _typing.Union[_QtWidgets.QStyle.StandardPixmap, _resources.ResourceIcon]
        ] = None,
    ) -> None:
        """Internal helper to configure and present the overlay card."""
        if icon:
            if isinstance(icon, _resources.ResourceIcon):
                icon_pixmap = icon.get_pixmap(32)
            else:
                icon_pixmap = _utils.get_standard_icon_pixmap(
                    self.style(),
                    icon,
                    widget=self,
                    size=32,
                )
            self._icon_label.setPixmap(icon_pixmap)

        self._message_label.setText(message)
        self._update_geometry()
        self._show_in_center()
        self._icon_label.setVisible(bool(icon))
        self._apply_theme_colors()
        _QtWidgets.QApplication.processEvents()

    def _show_in_center(self) -> None:
        """Show overlay, bring to front, and steal focus to block inputs."""
        self.show()
        self.raise_()
        self.setFocus()

    def hide_message(self) -> None:
        """Hide the overlay and release input blocking."""
        self.hide()

    @_contextlib.contextmanager
    def message(self, text: str) -> _typing.Iterator["BlockingMessageOverlay"]:
        """
        Context manager that displays the overlay with `text` on enter, and hides
        it on exit (even if an unhandled exception occurs).

        Example:
            ```python
            with overlay.message("Saving scene data..."):
                perform_heavy_save()
            ```

        Args:
            text: Message to display during the context duration.

        Yields:
            BlockingMessageOverlay: The overlay instance.
        """
        self.show_message(text)
        try:
            yield self
        finally:
            self.hide_message()


def run_demo() -> int:
    """
    Launch an interactive demo showcasing BlockingMessageOverlay features.
    """
    app = _QtWidgets.QApplication.instance() or _QtWidgets.QApplication(_sys.argv)
    app.setStyle("Fusion")

    main_window = _QtWidgets.QMainWindow()
    main_window.setWindowTitle("BlockingMessageOverlay Demo")
    main_window.resize(600, 450)

    central_widget = _QtWidgets.QWidget(main_window)
    main_window.setCentralWidget(central_widget)

    layout = _QtWidgets.QVBoxLayout(central_widget)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(12)

    title_label = _QtWidgets.QLabel("Interactive Form (Testing Input Block)")
    font = title_label.font()
    font.setBold(True)
    font.setPointSize(12)
    title_label.setFont(font)
    layout.addWidget(title_label)

    # Sample form inputs to test that they are blocked while overlay is visible
    layout.addWidget(_QtWidgets.QLabel("Username:"))
    input_user = _QtWidgets.QLineEdit()
    input_user.setPlaceholderText("Try typing here while overlay is active...")
    layout.addWidget(input_user)

    layout.addWidget(_QtWidgets.QLabel("Project Choice:"))
    combo = _QtWidgets.QComboBox()
    combo.addItems(["Project Alpha", "Project Beta", "Project Gamma"])
    layout.addWidget(combo)

    layout.addStretch()

    # Overlay creation
    overlay = BlockingMessageOverlay(main_window)

    # Action Buttons
    btn_box = _QtWidgets.QHBoxLayout()

    btn_msg = _QtWidgets.QPushButton("Show Message (3s)")

    def _show_temp_msg():
        overlay.show_message("Processing background task...")
        _QtCore.QTimer.singleShot(3000, overlay.hide_message)

    btn_msg.clicked.connect(_show_temp_msg)
    btn_box.addWidget(btn_msg)

    btn_busy = _QtWidgets.QPushButton("Show Busy Icon (3s)")

    def _show_temp_busy():
        overlay.show_busy("Loading heavy pipeline assets...")
        _QtCore.QTimer.singleShot(3000, overlay.hide_message)

    btn_busy.clicked.connect(_show_temp_busy)
    btn_box.addWidget(btn_busy)

    btn_warn = _QtWidgets.QPushButton("Show Warning (3s)")

    def _show_temp_warn():
        overlay.show_warning("Network connectivity degraded.")
        _QtCore.QTimer.singleShot(3000, overlay.hide_message)

    btn_warn.clicked.connect(_show_temp_warn)
    btn_box.addWidget(btn_warn)

    layout.addLayout(btn_box)

    main_window.show()
    return app.exec_()


if __name__ == "__main__":
    _sys.exit(run_demo())
