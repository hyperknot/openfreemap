from pathlib import Path

from dotenv import dotenv_values


ASSETS_DIR = Path(__file__).parent / 'assets'
CONFIG_DIR = Path(__file__).parent.parent / 'config'
SCRIPTS_DIR = Path(__file__).parent.parent / 'scripts'

OFM_DIR = '/data/ofm'
REMOTE_CONFIG = '/data/ofm/config'
TILE_GEN_BIN = '/data/ofm/tile_gen/bin'
HTTP_HOST_BIN = '/data/ofm/http_host/bin'

DOTENV_VALUES = dotenv_values(f'{CONFIG_DIR}/.env')


def dotenv_val(key):
    return DOTENV_VALUES.get(key, '').strip()
