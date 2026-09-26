import typing as _t

from qt_gateway import QtWidgets as _QtWidgets

from qt_helpers.widgets import table_view as _table_view
from qt_helpers.widgets.table import model as _table_model


class TableView(_table_view.TableView):
    def __init__(self, parent: _t.Optional[_QtWidgets.QWidget] = None) -> None:
        super().__init__(allow_row_delete=True, parent=parent)
        self._delegates_by_type: _t.Dict[
            _t.Type[_QtWidgets.QStyledItemDelegate], _QtWidgets.QStyledItemDelegate
        ] = {}

    def setModel(self, model: _table_model.TableModel) -> None:
        super().setModel(model)

        for index, column in enumerate(model.columns_spec.columns()):
            if not column.delegate:
                continue

            delegate = self._delegates_by_type.get(column.delegate.__name__)
            if not delegate:
                delegate = column.delegate()
                self._delegates_by_type[column.delegate.__name__] = delegate

            self.setItemDelegateForColumn(index, delegate)
