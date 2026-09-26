import dataclasses as _dataclasses
import typing as _t
from collections import abc as _abc_collections

from qt_gateway import QtCore as _QtCore, QtGui as _QtGui, QtWidgets as _QtWidgets

from qt_helpers import constants as _constants
from qt_helpers.delegates import left_click as _left_click_delegate

_VIEW_EDIT_TRIGGER_EVENT = _QtCore.QEvent.registerEventType()


class _ViewEditTriggerEvent(_QtCore.QEvent):
    def __init__(self) -> None:
        super().__init__(_QtCore.QEvent.Type(_VIEW_EDIT_TRIGGER_EVENT))

    pass


@_dataclasses.dataclass(frozen=True)
class ComboOption:
    text: str
    value: _t.Any = None


class ComboBoxDelegate(_left_click_delegate.LeftClickDelegate):
    OPTIONS_ROLE = _constants.CustomDataRole.COMBO_OPTIONS

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
        # ========================
        # Calculate drop-down arrow rect
        # ========================
        combo_option = _QtWidgets.QStyleOptionComboBox()
        combo_option.rect = option.rect
        arrow_rect = style.subControlRect(
            _QtWidgets.QStyle.ComplexControl.CC_ComboBox,
            combo_option,
            _QtWidgets.QStyle.SubControl.SC_ComboBoxArrow,
            option.widget,
        )

        # ========================
        # Draw full background so that the arrow background behaves the same as other cells.
        # ========================
        arrow_bg_option = _QtWidgets.QStyleOptionViewItem(option)
        arrow_bg_option.rect = arrow_rect
        style.drawPrimitive(
            style.PrimitiveElement.PE_PanelItemViewItem,
            arrow_bg_option,
            painter,
            option.widget,
        )

        # ========================
        # Draw drop-down arrow
        # ========================
        arrow_option = _QtWidgets.QStyleOptionButton()
        arrow_option.rect = arrow_rect
        arrow_option.state = option.state

        style.drawPrimitive(
            style.PrimitiveElement.PE_IndicatorArrowDown,
            arrow_option,
            painter,
            option.widget,
        )

        # ========================
        # Draw full item but adjust for arrow
        # ========================
        option.rect = option.rect.adjusted(
            0,
            0,
            -arrow_rect.width(),
            0,
        )
        super().paint(painter, option, index)

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
        # This is important to avoid recursion as the view.edit() call
        # on click edit will come back to the event handler here,
        # and we must not process further.
        if event.type() == _VIEW_EDIT_TRIGGER_EVENT:
            return False

        return super().editorEvent(event, model, option, index)

    def createEditor(
        self,
        parent: _t.Optional[_QtWidgets.QWidget],
        option: _QtWidgets.QStyleOptionViewItem,
        index: _t.Union[_QtCore.QModelIndex, _QtCore.QPersistentModelIndex],
    ) -> _QtWidgets.QWidget:
        combo_box = _QtWidgets.QComboBox(parent)
        combo_box.setEditable(True)
        combo_box.completer().setCompletionMode(
            _QtWidgets.QCompleter.CompletionMode.PopupCompletion,
        )
        combo_box.completer().setFilterMode(_QtCore.Qt.MatchFlag.MatchContains)
        combo_box.setInsertPolicy(_QtWidgets.QComboBox.InsertPolicy.NoInsert)
        options_list = index.data(_constants.CustomDataRole.COMBO_OPTIONS)
        if isinstance(options_list, _abc_collections.Iterable):
            for combo_option in options_list:
                if isinstance(combo_option, ComboOption):
                    combo_box.addItem(combo_option.text, combo_option.value)

        return combo_box

    def updateEditorGeometry(
        self,
        editor: _QtWidgets.QWidget,
        option: _QtWidgets.QStyleOptionViewItem,
        index: _t.Union[_QtCore.QModelIndex, _QtCore.QPersistentModelIndex],
    ) -> None:
        super().updateEditorGeometry(editor, option, index)
        editor.showPopup()
        return

    def setEditorData(
        self,
        editor: _QtWidgets.QWidget,
        index: _t.Union[_QtCore.QModelIndex, _QtCore.QPersistentModelIndex],
    ) -> None:
        if isinstance(editor, _QtWidgets.QComboBox):
            current_value = index.data(_QtCore.Qt.ItemDataRole.EditRole)
            for editor_index in range(editor.count()):
                index_value = editor.itemData(
                    editor_index, _QtCore.Qt.ItemDataRole.UserRole
                )
                if index_value == current_value:
                    editor.setCurrentIndex(editor_index)
                    return None

        return super().setEditorData(editor, index)

    def setModelData(
        self,
        editor: _QtWidgets.QWidget,
        model: _QtCore.QAbstractItemModel,
        index: _t.Union[_QtCore.QModelIndex, _QtCore.QPersistentModelIndex],
    ) -> None:
        if isinstance(editor, _QtWidgets.QComboBox):
            current_value = editor.itemData(
                editor.currentIndex(), _QtCore.Qt.ItemDataRole.UserRole
            )

            if current_value:
                model.setData(index, current_value, _QtCore.Qt.ItemDataRole.EditRole)

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
        option = _QtWidgets.QStyleOptionViewItem(option)
        if not isinstance(option.widget, _QtWidgets.QAbstractItemView):
            return False

        view = option.widget
        view.setCurrentIndex(index)
        view.edit(index, view.EditTrigger.AllEditTriggers, _ViewEditTriggerEvent())
        return True

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
