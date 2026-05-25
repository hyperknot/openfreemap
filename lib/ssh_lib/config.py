import os
from pathlib import Path


class Configuration:
    # local paths relative to this file
    local_assets_dir = Path(__file__).parent.parent / 'assets'


config = Configuration()
