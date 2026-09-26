import typing as _t

from qt_gateway import QtCore as _QtCore, QtGui as _QtGui, QtWidgets as _QtWidgets

from qt_helpers import constants as _constants


class RegExpLineEditDelegate(_QtWidgets.QStyledItemDelegate):
    REG_EXP_ROLE = _constants.CustomDataRole.REG_EXP

    def createEditor(
        self,
        parent: _t.Optional[_QtWidgets.QWidget],
        option: _QtWidgets.QStyleOptionViewItem,
        index: _t.Union[_QtCore.QModelIndex, _QtCore.QPersistentModelIndex],
    ) -> _QtWidgets.QWidget:
        line_edit = _QtWidgets.QLineEdit(parent)
        reg_exp = index.data(role=self.REG_EXP_ROLE)
        if reg_exp:
            validator = _QtGui.QRegularExpressionValidator(reg_exp)
            line_edit.setValidator(validator)
        return line_edit
