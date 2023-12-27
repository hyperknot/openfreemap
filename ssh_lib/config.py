from pathlib import Path


base = Path(__file__).parent.parent

CONFIG_DIR = base / 'config'
SCRIPTS_DIR = base / 'scripts'
ASSETS_DIR = Path(__file__).parent / 'assets'


TILE_GEN_BIN = '/data/ofm/tile_gen/bin'
REMOTE_CONFIG = '/data/ofm/config'
