# In the container, link_handler/schema.py is bind-mounted to replace this file
# (docker-compose bind-mount in docker-compose.yml). For local tests, this stub
# imports the real class by path so tests can run without a container.
import importlib.util
from pathlib import Path

_src = Path(__file__).parent.parent / "link_handler" / "schema.py"
if _src.exists():
    _spec = importlib.util.spec_from_file_location("_lh_schema", _src)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    SpaceAPISchema = _mod.SpaceAPISchema
else:
    raise ImportError("schema.py not found in link_handler/ — check bind-mount or local path")
