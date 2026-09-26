import typing as _t

try:
    # https://github.com/mottosso/Qt.py
    from Qt import QtWidgets as _QtWidgets, QtCore as _QtCore
except ModuleNotFoundError:
    from PySide2 import (  # type: ignore # https://github.com/mottosso/Qt.py?tab=readme-ov-file#project-goals
        QtWidgets as _QtWidgets,
        QtCore as _QtCore,
    )

_R = _t.TypeVar("_R")


class SingleShotConnect(_t.Generic[_R]):
    """
    A utility class to connect a Qt signal to a slot for a single execution.

    This class ensures that the slot is executed only once when the signal is emitted,
    and then automatically disconnects the slot.

    To prevent premature garbage collection, the instance of this class is stored
    in a class-level set (`_INSTANCES`). This ensures that the object remains alive
    until the signal is emitted, even if the client does not explicitly retain a
    reference to the instance.
    """

    _INSTANCES: _t.ClassVar[_t.Set["SingleShotConnect"]] = set()

    def __init__(
        self,
        signal: "_QtCore.SignalInstance",
        slot: _t.Callable[..., _R],
    ) -> None:
        """
        Initialize a `SingleShotConnect` instance.

        Args:
            signal: The Qt signal to connect.
            slot: The callable slot to execute when the signal is emitted.
        """
        self._signal = signal
        self._slot = slot
        self._signal.connect(self._single_shot_wrapper)
        SingleShotConnect._INSTANCES.add(self)

    def _single_shot_wrapper(self, *args: _t.Any, **kwargs: _t.Any) -> _R:
        """
        Get wrapper method that disconnects the signal after the slot is executed.

        This method is called when the signal is emitted. It ensures that the slot
        is called with the given arguments, disconnects the signal, and removes
        the instance from the tracking set.

        Returns:
            The result after slot execution.
        """
        self._signal.disconnect(self._single_shot_wrapper)
        SingleShotConnect._INSTANCES.remove(self)
        return self._slot(*args, **kwargs)


def _test():
    class MyWindow(_QtWidgets.QWidget):
        def __init__(self, parent: _t.Optional[_QtWidgets.QWidget] = None) -> None:
            super().__init__(parent=parent)
            self._button = _QtWidgets.QPushButton("Click me and I will print once!")
            SingleShotConnect(self._button.clicked, self._single_shot_message)

            self._main_layout = _QtWidgets.QVBoxLayout()
            self._main_layout.addWidget(self._button)
            self.setLayout(self._main_layout)
            self.resize(300, 300)

        @staticmethod
        def _single_shot_message():
            print("I am done doing my thing! You should not see me again.")

    app = _QtWidgets.QApplication([])
    widget = MyWindow()
    widget.show()
    app.exec_()


if __name__ == "__main__":
    _test()
