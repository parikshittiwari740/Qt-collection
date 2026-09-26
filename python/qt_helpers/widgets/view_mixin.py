from qt_gateway import QtCore as _QtCore, QtGui as _QtGui, QtWidgets as _QtWidgets


class AbstractViewMixin:
    _PLACEHOLDER_COLOR = (128, 128, 128)

    def set_placeholder_text(self, text: str) -> None:
        setattr(self, "_placeholder_text", text)

    def paintEvent(self, e: _QtGui.QPaintEvent) -> None:
        assert isinstance(self, _QtWidgets.QAbstractItemView)
        super().paintEvent(e)

        text = getattr(self, "_placeholder_text", None)
        if not text:
            return

        viewport_is_empty = self.model() is not None and self.model().rowCount() <= 0
        if not viewport_is_empty:
            return

        painter = _QtGui.QPainter(self.viewport())
        painter.setPen(_QtGui.QColor(*self._PLACEHOLDER_COLOR))

        rect = self.viewport().rect()
        painter.drawText(
            rect,
            _QtCore.Qt.AlignmentFlag.AlignCenter,
            text,
        )
