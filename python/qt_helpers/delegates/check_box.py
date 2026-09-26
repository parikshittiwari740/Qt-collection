import typing as _t

from qt_gateway import QtCore as _QtCore, QtGui as _QtGui, QtWidgets as _QtWidgets

from qt_helpers.delegates import left_click as _left_click_delegate


class CenteredCheckBoxDelegate(_left_click_delegate.LeftClickDelegate):
    def paint(
        self,
        painter: _QtGui.QPainter,
        option: _QtWidgets.QStyleOptionViewItem,
        index: _t.Union[_QtCore.QModelIndex, _QtCore.QPersistentModelIndex],
    ) -> None:
        check_state: _t.Optional[_QtCore.Qt.CheckState] = index.data(
            _QtCore.Qt.CheckStateRole
        )
        if check_state is None:
            super().paint(painter, option, index)
            return

        self.initStyleOption(option, index)
        widget = option.widget
        style = widget.style()

        checkbox_rect = style.subElementRect(
            _QtWidgets.QStyle.SE_ItemViewItemCheckIndicator, option, widget=widget
        )
        checkbox_rect.moveCenter(option.rect.center())

        # Draw the item without the built-in check indicator
        option.features &= ~_QtWidgets.QStyleOptionViewItem.HasCheckIndicator
        if not index.flags() & _QtCore.Qt.ItemIsEnabled:
            option.state &= ~_QtWidgets.QStyle.State_Enabled

        style.drawControl(_QtWidgets.QStyle.CE_ItemViewItem, option, painter, widget)

        # Prepare an option for drawing just the checkbox
        check_option = _QtWidgets.QStyleOptionViewItem(option)
        check_option.text = None
        check_option.rect = checkbox_rect
        check_option.state = check_option.state & ~_QtWidgets.QStyle.State_HasFocus

        if check_state == _QtCore.Qt.CheckState.Checked:
            check_option.state |= _QtWidgets.QStyle.State_On
        elif check_state == _QtCore.Qt.CheckState.Unchecked:
            check_option.state |= _QtWidgets.QStyle.State_Off
        else:
            check_option.state |= _QtWidgets.QStyle.State_NoChange

        style.drawPrimitive(
            _QtWidgets.QStyle.PE_IndicatorItemViewItemCheck,
            check_option,
            painter,
            widget,
        )

    def _click_rect(
        self,
        option: _QtWidgets.QStyleOptionViewItem,
    ) -> _QtCore.QRect:
        widget = option.widget
        style = widget.style() if widget else _QtWidgets.QApplication.style()
        check_rect = style.subElementRect(
            _QtWidgets.QStyle.SE_ItemViewItemCheckIndicator,
            option,
            widget=option.widget,
        )
        check_rect.moveCenter(option.rect.center())
        return check_rect

    def _is_disabled_for_click(
        self,
        model: _QtCore.QAbstractItemModel,
        option: _QtWidgets.QStyleOptionViewItem,
        index: _t.Union[_QtCore.QModelIndex, _QtCore.QPersistentModelIndex],
    ) -> bool:
        disabled = super()._is_disabled_for_click(model, option, index)
        if not disabled:
            if model.flags(index) & _QtCore.Qt.ItemFlag.ItemIsUserCheckable:
                return False
        return True

    def _on_left_click(
        self,
        model: _QtCore.QAbstractItemModel,
        index: _t.Union[_QtCore.QModelIndex, _QtCore.QPersistentModelIndex],
        option: _QtWidgets.QStyleOptionViewItem,
        event: _QtCore.QEvent,
    ) -> bool:
        current_state = index.data(_QtCore.Qt.ItemDataRole.CheckStateRole)
        if current_state is None:
            return False

        new_state = (
            _QtCore.Qt.CheckState.Checked
            if current_state == _QtCore.Qt.CheckState.Unchecked
            else _QtCore.Qt.CheckState.Unchecked
        )
        return model.setData(index, new_state, _QtCore.Qt.ItemDataRole.CheckStateRole)
