# In the container, link_handler/bot_keys.py is bind-mounted to replace this file.
# For local tests, this shim loads the real module and registers it as 'bot_keys'
# in sys.modules so that monkeypatching its attributes affects the functions too.
import importlib.util
import sys
from pathlib import Path

_src = Path(__file__).parent.parent / "link_handler" / "bot_keys.py"
if _src.exists() and __name__ == "bot_keys":
    _spec = importlib.util.spec_from_file_location("bot_keys", _src)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    # Replace this stub in sys.modules with the real module so all future
    # imports and monkeypatching target the same object.
    sys.modules["bot_keys"] = _mod
    # Make the shim's own namespace mirror the real module so `import bot_keys`
    # after the replacement sees the right names.
    globals().update(vars(_mod))
