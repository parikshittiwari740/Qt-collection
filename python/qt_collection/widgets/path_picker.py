import dataclasses as _dataclasses
import pathlib as _pathlib
import typing as _t

from qt_gateway import QtCore as _QtCore, QtGui as _QtGui, QtWidgets as _QtWidgets


@_dataclasses.dataclass()
class PathPickerSettings:
    dialog_title: _t.Optional[str] = None
    dir_only: bool = False
    working_dir: _t.Optional[str] = None
    filter: _t.Optional[str] = None
    placeholder_text: _t.Optional[str] = None


class PathPickerLine(_QtWidgets.QWidget):
    def __init__(
        self,
        parent=None,
        label: _t.Optional[str] = None,
        picker_settings: _t.Optional[PathPickerSettings] = None,
    ) -> None:
        super(PathPickerLine, self).__init__(parent)
        self._label_text = label
        self._picker_settings = picker_settings or PathPickerSettings()
        self._main_layout = _QtWidgets.QVBoxLayout()
        self._setup_ui()
        self._setup_connections()
        self.setLayout(self._main_layout)
        if parent:
            self._main_layout.setContentsMargins(0, 0, 0, 0)

        if self._picker_settings.placeholder_text:
            self._path_line.setPlaceholderText(self._picker_settings.placeholder_text)

    @property
    def current_path(self) -> _t.Optional[str]:
        return self._path_line.text() or None

    def _setup_ui(self):
        self._path_line = _QtWidgets.QLineEdit()
        self._path_line.setReadOnly(True)

        self._choose_button = _QtWidgets.QPushButton("Choose")

        line_layout = _QtWidgets.QHBoxLayout()
        if self._label_text:
            line_layout.addWidget(_QtWidgets.QLabel(self._label_text))

        line_layout.addWidget(self._path_line)
        line_layout.addWidget(self._choose_button)
        line_layout.setContentsMargins(0, 0, 0, 0)

        self._main_layout.addLayout(line_layout)

    def _setup_connections(self) -> None:
        self._choose_button.clicked.connect(self._on_choose_button_clicked)

    def _on_choose_button_clicked(self) -> None:
        title = "Choose a file"
        if self._picker_settings.dialog_title:
            title = self._picker_settings.dialog_title

        elif self._picker_settings.dir_only:
            title = "Choose a directory"

        dir = self._picker_settings.working_dir
        if self._path_line.text():
            dir = self._path_line.text()
            if not self._picker_settings.dir_only:
                dir = str(_pathlib.Path(dir).parent)

        if self._picker_settings.dir_only:
            path = _QtWidgets.QFileDialog.getExistingDirectory(
                None,
                title,
                dir=dir or "",
            )
        else:
            path = _QtWidgets.QFileDialog.getOpenFileName(
                None,
                title,
                dir=dir or "",
                filter=self._picker_settings.filter or "",
            )

        if path:
            self._path_line.setText(str(_pathlib.Path(path)))
