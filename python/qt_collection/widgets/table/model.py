import typing as _t

from qt_gateway import QtCore as _QtCore

from qt_helpers.widgets.table import (
    columns as _table_column_spec,
    row_item as _row_item,
)

_C = _t.TypeVar("_C", bound=_table_column_spec.TableColumns)
_R = _t.TypeVar("_R", bound=_row_item.TableRowItem)
_D = _t.TypeVar("_D")
_ModelIndex = _t.Union[_QtCore.QModelIndex, _QtCore.QPersistentModelIndex]


class TableModel(_t.Generic[_C, _R, _D], _QtCore.QAbstractTableModel):
    def __init__(
        self,
        table_columns: _t.Type[_C],
        row_item_spec: _t.Type[_R],
        parent: _t.Optional[_QtCore.QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._row_items: _t.List[_R] = []
        self._table_columns = table_columns
        self._row_item_spec = row_item_spec

    def clear(self) -> None:
        self.beginResetModel()
        self._row_items = []
        self.endResetModel()

    @property
    def row_items(self) -> _t.List[_R]:
        return self._row_items

    @property
    def columns_spec(self) -> _t.Type[_C]:
        return self._table_columns

    @property
    def data_items(self) -> _t.List[_D]:
        return [r_item.data_object for r_item in self._row_items]

    def removeRows(self, start_index: int, count: int, parent=None) -> bool:
        row_count = len(self._row_items)
        if start_index >= row_count:
            return False

        if row_count <= 0:
            return False

        parent = parent or _QtCore.QModelIndex()
        self.beginRemoveRows(parent, start_index, start_index + count - 1)
        del self._row_items[start_index : start_index + count]
        self.endRemoveRows()
        return True

    def add_data_items(
        self,
        data_items: _t.Iterable[_D],
    ) -> None:
        items_list = list(data_items)
        if not items_list:
            return

        start = self.rowCount()
        last = start + len(items_list) - 1

        self.beginInsertRows(_QtCore.QModelIndex(), start, last)
        self._row_items.extend(
            [self._row_item_spec(d, self._table_columns) for d in items_list]
        )
        self.endInsertRows()

    def set_data_items(
        self,
        data_items: _t.Iterable[_D],
    ) -> None:
        self.beginResetModel()
        self._row_items = [
            self._row_item_spec(d, self._table_columns) for d in data_items
        ]
        self.endResetModel()

    def flags(self, index: _ModelIndex) -> _QtCore.Qt.ItemFlags:
        row_item = self._row_items[index.row()]
        flags = row_item.flags(index.column())
        return flags or super().flags(index)

    def rowCount(self, parent=None) -> int:
        return len(self._row_items)

    def columnCount(self, parent=None) -> int:
        return len(self._table_columns.columns())

    def headerData(
        self,
        section: int,
        orientation: _QtCore.Qt.Orientation,
        role: _t.Union[
            int, _QtCore.Qt.ItemDataRole
        ] = _QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> _t.Any:
        if orientation == _QtCore.Qt.Orientation.Horizontal:
            column = self._table_columns.columns()[section]
            if role == _QtCore.Qt.ItemDataRole.DisplayRole:
                return column.label

        return None

    def data(
        self,
        index: _ModelIndex,
        role: _QtCore.Qt.ItemDataRole = _QtCore.Qt.ItemDataRole.DisplayRole,  # type: ignore
    ) -> _t.Any:
        row_item = self._row_items[index.row()]
        return row_item.data(index.column(), role)

    def setData(
        self,
        index: _ModelIndex,
        value: _t.Any,
        role: _QtCore.Qt.ItemDataRole = _QtCore.Qt.ItemDataRole.EditRole,  # type: ignore
    ) -> bool:
        row_item = self._row_items[index.row()]
        success = row_item.set_data(index.column(), value, role)
        if success:
            self.dataChanged.emit(index, index)
        return success
