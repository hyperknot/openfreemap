import json
from pathlib import Path


NGINX_DIR = Path(__file__).parent / 'nginx'

DEFAULT_RUNS_DIR = Path('/data/ofm/http_host/runs')
DEFAULT_ASSETS_DIR = Path('/data/ofm/http_host/assets')

MNT_DIR = Path('/mnt/ofm')
OFM_CONFIG_DIR = Path('/data/ofm/config')

try:
    with open('/data/ofm/config/http_host.json') as fp:
        HOST_CONFIG = json.load(fp)
except Exception:
    HOST_CONFIG = {}
