import json
from pathlib import Path


class Configuration:
    http_host_dir = Path('/data/ofm/http_host')

    nginx_dir = Path(__file__).parent / 'nginx'

    default_runs_dir = http_host_dir / 'runs'
    default_assets_dir = http_host_dir / 'assets'

    mnt_dir = Path('/mnt/ofm')
    ofm_config_dir = Path('/data/ofm/config')
    http_host_bin = http_host_dir / 'bin'

    certs_dir = Path('/data/nginx/certs')

    try:
        with open('/data/ofm/config/http_host.json') as fp:
            host_config = json.load(fp)
    except Exception:
        host_config = {}


config = Configuration()
