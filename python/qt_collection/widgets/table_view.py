import logging as _logging
import typing as _t
import unicodedata as _unicodedata

from qt_gateway import QtCore as _QtCore, QtWidgets as _QtWidgets

from qt_helpers import constants as _constants, resources as _resources
from qt_helpers.widgets import view_mixin as _view_mixin

_LOGGER = _logging.getLogger(__name__)


class TableView(_view_mixin.AbstractViewMixin, _QtWidgets.QTableView):
    copy_signal = _QtCore.Signal()
    paste_signal = _QtCore.Signal()

    def __init__(
        self,
        parent: _t.Optional[_QtWidgets.QWidget] = None,
        handle_copy_event: _t.Optional[bool] = True,
        handle_paste_event: _t.Optional[bool] = True,
        allow_row_delete: _t.Optional[bool] = False,
    ):
        super(TableView, self).__init__(parent)
        self._include_headers_on_copy = False
        self._allow_row_delete = allow_row_delete
        self.setContextMenuPolicy(_QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            self._on_custom_context_menu_requested  # type: ignore
        )
        if handle_copy_event:
            self.copy_signal.connect(self._on_copy_triggered)

        if handle_paste_event:
            self.paste_signal.connect(self._on_paste_triggered)

    def _on_custom_context_menu_requested(self, pos: _QtCore.QPoint) -> None:
        context_menu = self._build_context_menu()
        context_menu.exec_(self.viewport().mapToGlobal(pos))

    def _build_context_menu(self) -> _QtWidgets.QMenu:
        menu = _QtWidgets.QMenu(self)

        copy_action = _QtWidgets.QAction("Copy", menu)
        copy_action.setIcon(_resources.ResourceIcon.COPY.get_pixmap())
        copy_action.triggered.connect(self.copy_signal)

        include_headers_action = _QtWidgets.QAction("Include headers", menu)
        include_headers_action.setCheckable(True)
        include_headers_action.setChecked(self._include_headers_on_copy)
        include_headers_action.toggled.connect(
            lambda c: setattr(self, "_include_headers_on_copy", c)
        )

        menu.addAction(copy_action)
        menu.addAction(include_headers_action)
        menu.addSeparator()

        paste_action = _QtWidgets.QAction("Paste", menu)
        paste_action.setIcon(_resources.ResourceIcon.PASTE.get_pixmap())
        paste_action.triggered.connect(self.paste_signal)
        if not _QtWidgets.QApplication.clipboard().text():
            paste_action.setDisabled(True)

        menu.addAction(paste_action)

        if self._allow_row_delete:
            row_count = len({index.row() for index in self.selectedIndexes()})
            delete_row = _QtWidgets.QAction(f"Delete row ({row_count})", menu)
            if not row_count:
                delete_row.setDisabled(True)

            delete_row.setIcon(_resources.ResourceIcon.DELETE.get_pixmap())
            delete_row.triggered.connect(self._on_delete_selected_rows_triggered)
            menu.addAction(delete_row)

        return menu

    def _on_delete_selected_rows_triggered(self) -> None:
        selected_indexes = self.selectedIndexes()
        if not selected_indexes:
            return

        row_indexes = list(sorted(index.row() for index in selected_indexes))[::-1]
        for row_index in row_indexes:
            self.model().removeRow(row_index)

    def _get_as_plain_text_table(
        self,
        indexes: _t.List[_QtCore.QModelIndex],
        include_headers: bool = True,
    ) -> str:
        min_row = min(index.row() for index in indexes)
        max_row = max(index.row() for index in indexes)
        min_column = min(index.column() for index in indexes)
        max_column = max(index.column() for index in indexes)

        indexes_by_position = {
            (index.row(), index.column()): index for index in indexes
        }

        rows = []

        if include_headers:
            headers = []

            for column in range(min_column, max_column + 1):
                header = self.model().headerData(
                    column,
                    _QtCore.Qt.Orientation.Horizontal,
                    _QtCore.Qt.ItemDataRole.DisplayRole,
                )
                headers.append(header or "")

            rows.append("\t".join(headers))

        for row in range(min_row, max_row + 1):
            columns = []

            for column in range(min_column, max_column + 1):
                index = indexes_by_position.get((row, column))
                if index.flags() & _QtCore.Qt.ItemFlag.ItemIsUserCheckable:
                    value = index.data(_QtCore.Qt.ItemDataRole.CheckStateRole)
                    value = "True" if value == _QtCore.Qt.Checked else "False"

                elif index.data(_constants.CustomDataRole.PLAIN_TEXT_TABLE_COPY):
                    value = (
                        index.data(_constants.CustomDataRole.PLAIN_TEXT_TABLE_COPY)
                        or ""
                    )
                else:
                    value = (
                        index.data(_QtCore.Qt.ItemDataRole.DisplayRole)
                        if index is not None
                        else ""
                    )

                columns.append(value or "")

            rows.append("\t".join(columns))

        return "\n".join(rows)

    def _on_copy_triggered(self) -> None:
        selected_indexes = self.selectedIndexes()
        if not selected_indexes:
            return

        text = self._get_as_plain_text_table(
            selected_indexes, include_headers=self._include_headers_on_copy
        )
        _QtWidgets.QApplication.clipboard().setText(text)

    def _paste_from_plain_text_table(self, text: str) -> None:
        clipboard_rows = [row.split("\t") for row in text.splitlines()]

        if not clipboard_rows:
            return

        model = self.model()
        if model is None:
            return

        model_row_count = model.rowCount()
        model_column_count = model.columnCount()

        if model_column_count == 0:
            return

        selected_indexes = self.selectedIndexes()

        # Single-cell clipboard pasted into multiple selected indexes.
        if (
            len(clipboard_rows) == 1
            and len(clipboard_rows[0]) == 1
            and len(selected_indexes) > 1
        ):
            value = clipboard_rows[0][0]

            for index in selected_indexes:
                self._set_paste_value(model, index, value)
            return

        # Determine where the rectangular paste should start and the
        # dimensions of the current selection.
        if selected_indexes:
            min_row = min(index.row() for index in selected_indexes)
            max_row = max(index.row() for index in selected_indexes)
            min_column = min(index.column() for index in selected_indexes)
            max_column = max(index.column() for index in selected_indexes)

            start_row = min_row
            start_column = min_column

            selection_row_count = max_row - min_row + 1
            selection_column_count = max_column - min_column + 1
        else:
            start_row = model_row_count
            start_column = 0

            selection_row_count = 0
            selection_column_count = 0

        _LOGGER.debug(
            "[Paste Trigger] start_row: %s, start_column: %s",
            start_row,
            start_column,
        )

        # Check whether the first clipboard row contains table headers.
        model_headers = {}

        for column in range(model_column_count):
            header = model.headerData(
                column,
                _QtCore.Qt.Orientation.Horizontal,
                _QtCore.Qt.ItemDataRole.DisplayRole,
            )

            if header is not None:
                model_headers[str(header)] = column

        clipboard_headers = clipboard_rows[0]

        header_mapping = {}

        for clipboard_column, header in enumerate(clipboard_headers):
            model_column = model_headers.get(header)

            if model_column is not None:
                header_mapping[clipboard_column] = model_column

        has_headers = bool(header_mapping)

        if has_headers:
            data_rows = clipboard_rows[1:]
        else:
            data_rows = clipboard_rows

            header_mapping = {}

            for clipboard_column in range(len(clipboard_rows[0])):
                model_column = start_column + clipboard_column

                if model_column >= model_column_count:
                    break

                header_mapping[clipboard_column] = model_column

        if not data_rows:
            _LOGGER.debug("[Paste Trigger] No data rows to paste.")
            return

        clipboard_row_count = len(data_rows)
        clipboard_column_count = max(len(row) for row in data_rows)

        # The paste area is large enough to contain both the selection and
        # the clipboard. If the selection is larger than the clipboard in
        # either dimension, repeat the clipboard in that dimension.
        paste_row_count = max(
            selection_row_count,
            clipboard_row_count,
        )

        paste_column_count = max(
            selection_column_count,
            clipboard_column_count,
        )

        for row_offset in range(paste_row_count):
            model_row = start_row + row_offset

            # Only paste into rows that already exist in the model.
            if model_row >= model_row_count:
                break

            clipboard_row = data_rows[row_offset % clipboard_row_count]

            for column_offset in range(paste_column_count):
                model_column = start_column + column_offset

                if model_column >= model_column_count:
                    break

                clipboard_column = column_offset % clipboard_column_count

                if clipboard_column >= len(clipboard_row):
                    continue

                value = clipboard_row[clipboard_column]

                index = model.index(
                    model_row,
                    model_column,
                )

                _LOGGER.debug(
                    "[Paste Trigger] Processing paste for index: %s, Value: '%s'",
                    index,
                    value,
                )
                self._set_paste_value(
                    model,
                    index,
                    value,
                )

    def _set_paste_value(
        self,
        model: _QtCore.QAbstractItemModel,
        index: _QtCore.QModelIndex,
        value: str,
    ) -> bool:
        if not index.isValid():
            _LOGGER.debug("[Paste Trigger] Index is not valid.")
            return False

        if not index.flags() & _QtCore.Qt.ItemFlag.ItemIsEnabled:
            _LOGGER.debug("[Paste Trigger] Index is not enabled.")
            return False

        if value.lower() in {"true", "false"}:
            if index.flags() & _QtCore.Qt.ItemFlag.ItemIsUserCheckable:
                check_state = (
                    _QtCore.Qt.CheckState.Checked
                    if value.lower() == "true"
                    else _QtCore.Qt.CheckState.Unchecked
                )

                _LOGGER.debug(
                    "[Paste Trigger] Setting check state for index: %s",
                    index,
                )

                model.setData(
                    index,
                    check_state,
                    _QtCore.Qt.ItemDataRole.CheckStateRole,
                )
                return True

        if index.flags() & _QtCore.Qt.ItemFlag.ItemIsEditable:
            model.setData(
                index,
                value,
                _QtCore.Qt.ItemDataRole.DisplayRole,
            )
            return True
        return False

    def _on_paste_triggered(self) -> None:
        clipboard = _QtWidgets.QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return

        self._paste_from_plain_text_table(text)
