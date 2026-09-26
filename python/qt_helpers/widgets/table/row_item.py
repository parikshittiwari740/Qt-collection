import abc as _abc
import typing as _t

from qt_gateway import QtCore as _QtCore

from qt_helpers.delegates import combo_box as _combo_box_delegate
from qt_helpers.widgets.table import columns as _column_spec

_D = _t.TypeVar("_D")
_C = _t.TypeVar("_C", bound=_column_spec.TableColumns)


class TableRowItem(_t.Generic[_D, _C], _abc.ABC):
    def __init__(
        self,
        data_object: _D,
        table_columns: _t.Type[_C],
    ):
        super().__init__()
        self._data_object = data_object
        self._table_columns = table_columns

    @property
    def data_object(self) -> _D:
        return self._data_object

    def flags(self, column_index: int) -> _t.Optional[_QtCore.Qt.ItemFlags]:
        column = self._table_columns.specs_from_column_index(column_index)
        return column.flags

    @_abc.abstractmethod
    def data(self, column_index: int, role: _QtCore.Qt.ItemDataRole) -> _t.Any:
        column = self._table_columns.specs_from_column_index(column_index)
        if role == _QtCore.Qt.ItemDataRole.TextAlignmentRole:
            if column.alignment:
                return column.alignment
        return None

    @_abc.abstractmethod
    def set_data(
        self, column_index: int, value: _t.Any, role: _QtCore.Qt.ItemDataRole
    ) -> bool: ...
