from pathlib import Path


base = Path(__file__).parent.parent

CONFIG_DIR = base / 'config'
SCRIPTS_DIR = base / 'scripts'
ASSETS_DIR = Path(__file__).parent / 'assets'


OFM_DIR = '/data/ofm'
REMOTE_CONFIG = '/data/ofm/config'
TILE_GEN_BIN = '/data/ofm/tile_gen/bin'
HTTP_HOST_BIN = '/data/ofm/http_host/bin'
