from pathlib import Path

from dotenv import dotenv_values


ASSETS_DIR = Path(__file__).parent / 'assets'
CONFIG_DIR = Path(__file__).parent.parent / 'config'
MODULES_DIR = Path(__file__).parent.parent / 'modules'

OFM_DIR = '/data/ofm'
REMOTE_CONFIG = f'{OFM_DIR}/config'
VENV_BIN = f'{OFM_DIR}/venv/bin'

TILE_GEN_DIR = f'{OFM_DIR}/tile_gen'
TILE_GEN_BIN = f'{TILE_GEN_DIR}/bin'

PLANETILER_SRC = f'{TILE_GEN_DIR}/planetiler_src'
PLANETILER_BIN = f'{TILE_GEN_DIR}/planetiler'

HTTP_HOST_BIN = f'{OFM_DIR}/http_host/bin'

DOTENV_VALUES = dotenv_values(f'{CONFIG_DIR}/.env')


def dotenv_val(key):
    return DOTENV_VALUES.get(key, '').strip()
