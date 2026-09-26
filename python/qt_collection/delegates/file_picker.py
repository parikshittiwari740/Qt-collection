import dataclasses as _dataclasses
import pathlib as _pathlib
import typing as _t

from qt_gateway import QtCore as _QtCore, QtGui as _QtGui, QtWidgets as _QtWidgets

from qt_helpers import constants as _constants, resources as _resources
from qt_helpers.delegates import left_click as _left_click_delegate


@_dataclasses.dataclass(frozen=True)
class FilePickerSettings:
    title: str
    dir_path: _t.Optional[_pathlib.Path] = None
    filter: _t.Optional[str] = None
    options: _t.Optional[_QtWidgets.QFileDialog.Option] = None


class FilePickerDelegate(_left_click_delegate.LeftClickActionDelegate):
    FILE_PICKER_SETTINGS_ROLE = _constants.CustomDataRole.FILE_PICKER_SETTINGS

    def createEditor(
        self,
        parent: _t.Optional[_QtWidgets.QWidget],
        option: _QtWidgets.QStyleOptionViewItem,
        index: _t.Union[_QtCore.QModelIndex, _QtCore.QPersistentModelIndex],
    ) -> None:
        self._trigger_path_prompt(index.model(), index)
        return

    def _get_action_icon(self) -> _QtGui.QIcon:
        attr_name = "_icon_cached"
        icon = getattr(self, attr_name, None)
        if not icon:
            icon = _resources.ResourceIcon.PENCIL_COLORED.get_icon()
            setattr(self, attr_name, icon)
        return icon

    def _trigger_path_prompt(
        self,
        model: _QtCore.QAbstractItemModel,
        index: _t.Union[
            _QtCore.QModelIndex,
            _QtCore.QPersistentModelIndex,
        ],
    ) -> bool:
        picker_settings = index.data(role=self.FILE_PICKER_SETTINGS_ROLE)
        if isinstance(picker_settings, FilePickerSettings):
            kwargs = {}
            if picker_settings.options:
                kwargs["options"] = picker_settings.options

            if picker_settings.filter:
                kwargs["filter"] = picker_settings.filter

            existing_path = index.data(role=_QtCore.Qt.ItemDataRole.EditRole)
            if existing_path:
                if _pathlib.Path(existing_path).exists():
                    kwargs["dir"] = str(_pathlib.Path(existing_path).parent)

            if picker_settings.dir_path:
                kwargs["dir"] = str(picker_settings.dir_path)

            path = _QtWidgets.QFileDialog.getOpenFileName(
                None,
                picker_settings.title,
                **kwargs,
            )[0]
            if path:
                print(path)
                model.setData(
                    index,
                    path,
                    role=_QtCore.Qt.ItemDataRole.EditRole,
                )
                return True
        return False

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
        return self._trigger_path_prompt(model, index)
