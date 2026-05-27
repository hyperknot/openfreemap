from pathlib import Path
from typing import ClassVar


class Configuration:
    # local paths relative to this file
    local_assets_dir: ClassVar[Path] = Path(__file__).parent.parent / 'assets'


config = Configuration()
