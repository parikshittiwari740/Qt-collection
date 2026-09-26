import typing as _t

from qt_gateway import QtCore as _QtCore, QtGui as _QtGui, QtWidgets as _QtWidgets

from qt_helpers import constants as _constants


# Reference implementation:
# https://codebrowser.dev/qt5/qtbase/src/widgets/itemviews/qstyleditemdelegate.cpp.html
class LeftClickDelegate(_QtWidgets.QStyledItemDelegate):
    """
    Abstract delegate for handling eligible left-clicks.

    Intercepts left mouse clicks within a configurable clickable region
    and delegates the resulting action to subclasses.

    The clickable region and response to an eligible click are both
    customizable, allowing the delegate to be used for controls such as
    checkboxes, combo boxes, buttons, etc.
    """

    DISABLE_REASON_ROLE = _constants.CustomDataRole.DISABLE_REASON

    def editorEvent(
        self,
        event: _QtCore.QEvent,
        model: _QtCore.QAbstractItemModel,
        option: _QtWidgets.QStyleOptionViewItem,
        index: _t.Union[
            _QtCore.QModelIndex,
            _QtCore.QPersistentModelIndex,
        ],
    ) -> bool:
        option = _QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(option, index)

        if self._is_disabled_for_click(model, option, index):
            disable_reason = model.data(index, self.DISABLE_REASON_ROLE)

            if disable_reason:
                _QtWidgets.QToolTip.showText(
                    self._event_global_pos(event),
                    disable_reason,
                )

            return False

        event_type = event.type()

        if event_type not in (
            _QtCore.QEvent.MouseButtonPress,
            _QtCore.QEvent.MouseButtonRelease,
            _QtCore.QEvent.MouseButtonDblClick,
        ):
            return False

        if event.button() != _QtCore.Qt.MouseButton.LeftButton:
            return False

        click_rect = self._click_rect(option)

        if not click_rect.contains(event.pos()):
            return False

        # Consume press and double-click events so that the view does not
        # process them as normal item clicks. The release event is passed
        # to the subclass to perform the actual action.
        if event_type != _QtCore.QEvent.MouseButtonRelease:
            return True

        return self._on_left_click(model, index, option, event)

    def _click_rect(
        self,
        option: _QtWidgets.QStyleOptionViewItem,
    ) -> _QtCore.QRect:
        """Return the region in which a left click is considered eligible.

        Subclasses should override this to provide their own clickable
        region.
        """
        return option.rect

    def _is_disabled_for_click(
        self,
        model: _QtCore.QAbstractItemModel,
        option: _QtWidgets.QStyleOptionViewItem,
        index: _t.Union[
            _QtCore.QModelIndex,
            _QtCore.QPersistentModelIndex,
        ],
    ) -> bool:
        """Return whether the index should not respond to left clicks."""
        return not (
            model.flags(index) & _QtCore.Qt.ItemFlag.ItemIsEnabled
            and option.state & _QtWidgets.QStyle.StateFlag.State_Enabled
        )

    @staticmethod
    def _event_global_pos(event: _QtCore.QEvent) -> _QtCore.QPoint:
        """Return the global mouse position for Qt5/Qt6 events."""
        if hasattr(event, "globalPosition"):
            return event.globalPosition().toPoint()
        return event.globalPos()

    def _on_left_click(
        self,
        model: _QtCore.QAbstractItemModel,
        index: _t.Union[
            _QtCore.QModelIndex,
            _QtCore.QPersistentModelIndex,
        ],
        option: _QtWidgets.QStyleOptionViewItem,
        event: _QtCore.QEvent,
    ) -> bool:
        """Handle an eligible left-click.

        Subclasses should override this method and return whether the
        event was handled.
        """
        return False


class LeftClickActionDelegate(LeftClickDelegate):
    def _get_action_icon(self) -> _QtGui.QIcon:
        raise NotImplementedError(
            f"Subclass {self.__class__.__name__} must implement creating of action icon."
        )

    def paint(
        self,
        painter: _QtGui.QPainter,
        option: _QtWidgets.QStyleOptionViewItem,
        index: _t.Union[_QtCore.QModelIndex, _QtCore.QPersistentModelIndex],
    ) -> None:
        # Reference: https://codebrowser.dev/qt5/qtbase/src/widgets/styles/qcommonstyle.cpp.html
        option = _QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(option, index)

        style = (
            option.widget.style() if option.widget else _QtWidgets.QApplication.style()
        )
        action_rect = self._click_rect(option)

        # ========================
        # Draw full background so that the arrow background behaves the same as other cells.
        # ========================
        action_icon_bg_option = _QtWidgets.QStyleOptionViewItem(option)
        action_icon_bg_option.rect = action_rect
        style.drawPrimitive(
            style.PrimitiveElement.PE_PanelItemViewItem,
            action_icon_bg_option,
            painter,
            option.widget,
        )

        # ========================
        # Draw action button
        # ========================
        icon = self._get_action_icon()
        pixmap = icon.pixmap(_QtCore.QSize(action_rect.width(), action_rect.height()))

        action_option = _QtWidgets.QStyleOptionButton()
        action_option.rect = action_rect
        action_option.state = option.state

        style.drawItemPixmap(
            painter,
            action_rect,
            _QtCore.Qt.AlignmentFlag.AlignCenter,
            pixmap,
        )

        # ========================
        # Draw full item but adjust for arrow
        # ========================
        option.rect = option.rect.adjusted(
            0,
            0,
            -action_rect.width(),
            0,
        )
        super().paint(painter, option, index)

    def _click_rect(
        self,
        option: _QtWidgets.QStyleOptionViewItem,
    ) -> _QtCore.QRect:
        style = (
            option.widget.style() if option.widget else _QtWidgets.QApplication.style()
        )
        combo_option = _QtWidgets.QStyleOptionComboBox()
        combo_option.rect = option.rect
        return style.subControlRect(
            _QtWidgets.QStyle.ComplexControl.CC_ComboBox,
            combo_option,
            _QtWidgets.QStyle.SubControl.SC_ComboBoxArrow,
            option.widget,
        )
