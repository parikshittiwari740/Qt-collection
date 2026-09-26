import dataclasses as _dataclasses
import typing as _t

from qt_gateway import QtCore as _QtCore, QtWidgets as _QtWidgets

from qt_helpers.widgets.table import (
    columns as _table_columns,
    model as _table_model,
    row_item as _row_item,
    view as _table_view,
)

_D = _t.TypeVar("_D")


@_dataclasses.dataclass(frozen=True)
class DataItemChangedResult(_t.Generic[_D]):
    data_item: _D


class TableWidget(_t.Generic[_D], _QtWidgets.QWidget):
    data_item_changed_signal: "_QtCore.Signal[_D]" = _QtCore.Signal(
        DataItemChangedResult
    )

    def __init__(
        self,
        parent: _t.Optional[_QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        self._layout = _QtWidgets.QVBoxLayout()
        self._model = self._model_spec()(
            self._table_columns(),
            self._row_item_spec(),
        )
        self._setup_ui()
        self._setup_connections()

        if parent:
            self._layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self._layout)

    @classmethod
    def _table_columns(cls) -> _t.Type[_table_columns.TableColumns]:
        return _table_columns.TableColumns

    @classmethod
    def _model_spec(cls) -> _t.Type[_table_model.TableModel]:
        return _table_model.TableModel

    @classmethod
    def _row_item_spec(cls) -> _t.Type[_row_item.TableRowItem]:
        return _row_item.TableRowItem

    @property
    def rows_removed_signal(self):
        return self._model.rowsRemoved

    @property
    def data_items(self) -> _t.List[_D]:
        return self._model.data_items

    def clear(self) -> None:
        self._model.clear()

    def set_placeholder_text(self, text: str) -> None:
        self._table_view.set_placeholder_text(text)

    def add_data_items(
        self,
        data_items: _t.Iterable[_D],
    ) -> None:
        self._model.add_data_items(data_items)

    def set_data_items(
        self,
        data_items: _t.Iterable[_D],
    ) -> None:
        self._model.set_data_items(data_items)
        self._table_view.setSelectionMode(
            self._table_view.SelectionMode.ExtendedSelection
        )

    def _setup_ui(self) -> None:
        self._table_view = _table_view.TableView()
        self._table_view.setModel(self._model)

        for column_index, column in enumerate(self._table_columns().columns()):
            if column.width:
                self._table_view.horizontalHeader().resizeSection(
                    column_index, column.width
                )

            if column.resize_mode:
                self._table_view.horizontalHeader().setSectionResizeMode(
                    column_index, column.resize_mode
                )

        self._layout.addWidget(self._table_view)

    def _setup_connections(self) -> None:
        self._model.dataChanged.connect(self._on_model_data_changed)

    def _on_model_data_changed(self, index: _QtCore.QModelIndex) -> None:
        change_result = self._get_data_item_change_result(index)
        if change_result:
            self.data_item_changed_signal.emit(change_result)

    def _get_data_item_change_result(
        self,
        index: _QtCore.QModelIndex,
    ) -> _t.Optional[DataItemChangedResult[_D]]:
        try:
            row_item = self._model.row_items[index.row()]
            return DataItemChangedResult(row_item.data_object)
        except IndexError as e:
            return None
