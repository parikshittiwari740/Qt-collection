## Contents

### 1. `single_shot_connect.py`
This module defines the `SingleShotConnect` class, a utility for connecting Qt signals to slots that are executed only once. It simplifies the management of single-use connections by automatically disconnecting the signal after it is triggered.

#### Key Features:
- Automatically disconnects the signal after the slot is executed.
- Ensures the instance of `SingleShotConnect` remains alive until the signal is emitted, even if the client does not explicitly retain a reference to it.

#### Usage:
```python
from qt_collection.core.utils import single_shot_connect as _s_shot_connect

# Example: Connect a signal for one-time use
def on_signal_emitted(value):
    print(f"Signal emitted with value: {value}")

signal = some_qt_object.some_signal
_s_shot_connect.SingleShotConnect(signal, on_signal_emitted)
