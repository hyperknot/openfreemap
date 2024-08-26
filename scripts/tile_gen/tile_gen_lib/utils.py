import os
import sys
from pathlib import Path


def python_venv_executable() -> Path:
    venv_path = os.environ.get('VIRTUAL_ENV')

    if venv_path:
        return Path(venv_path) / 'bin' / 'python'
    elif sys.prefix != sys.base_prefix:
        return Path(sys.prefix) / 'bin' / 'python'
    else:
        return Path(sys.executable)
