import dataclasses as _dataclasses
import typing as _t

from qt_gateway import QtCore as _QtCore, QtWidgets as _QtWidgets

_S = _t.TypeVar("_S", bound="TableColumnSpec")


class TableColumnSpec:
    def __init__(
        self,
        label: str,
        alignment: _QtCore.Qt.AlignmentFlag = _QtCore.Qt.AlignmentFlag.AlignLeft,
        editable: bool = False,
        width: _t.Optional[int] = None,
        resize_mode: _t.Optional[_QtWidgets.QHeaderView.ResizeMode] = None,
        flags: _t.Optional[_QtCore.Qt.ItemFlags] = None,  # type: ignore
        delegate: _t.Optional[_t.Type[_QtWidgets.QStyledItemDelegate]] = None,
    ) -> None:
        self._label = label
        self._alignment = alignment
        self._width = width
        self._editable = editable
        self._resize_mode = resize_mode
        self._flags = flags
        self._delegate = delegate

    @property
    def editable(self) -> bool:
        return self._editable

    @property
    def label(self) -> str:
        return self._label

    @property
    def alignment(self) -> _QtCore.Qt.AlignmentFlag:
        return self._alignment

    @property
    def width(self) -> _t.Optional[int]:
        return self._width

    @property
    def resize_mode(self) -> _t.Optional[_QtWidgets.QHeaderView.ResizeMode]:
        return self._resize_mode

    @property
    def flags(self) -> _t.Optional[_QtCore.Qt.ItemFlags]:  # type: ignore
        flags = _QtCore.Qt.ItemFlag.ItemIsEnabled | _QtCore.Qt.ItemFlag.ItemIsSelectable
        if self.editable:
            flags |= _QtCore.Qt.ItemFlag.ItemIsEditable  # type: ignore
        return flags

    @property
    def delegate(self) -> _t.Optional[_t.Type[_QtWidgets.QStyledItemDelegate]]:
        return self._delegate


class TableColumns(_t.Generic[_S]):
    @classmethod
    def _columns(cls) -> _t.List[_S]:
        pass

    @classmethod
    def specs_from_column_index(cls, index: int) -> _S:
        return cls._columns()[index]

    @classmethod
    def columns(cls) -> _t.List[_S]:
        return cls._columns()


# ============== Example ==================
# class MyTableColumns(TableColumns):
#     PROJECT_NAME = TableColumnSpec(
#         "Project Name",
#     )
#
#     _COLUMNS = [
#         PROJECT_NAME
#     ]
