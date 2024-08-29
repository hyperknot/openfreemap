import json
from pathlib import Path


class Configuration:
    areas = ['planet', 'monaco']

    http_host_dir = Path('/data/ofm/http_host')

    http_host_bin = http_host_dir / 'bin'
    http_host_scripts_dir = http_host_bin / 'scripts'

    runs_dir = http_host_dir / 'runs'
    assets_dir = http_host_dir / 'assets'

    mnt_dir = Path('/mnt/ofm')
    ofm_config_dir = Path('/data/ofm/config')
    deployed_versions_dir = ofm_config_dir / 'deployed_versions'

    certs_dir = Path('/data/nginx/certs')
    nginx_confs = Path(__file__).parent / 'nginx_confs'

    try:
        with open(ofm_config_dir / 'http_host.json') as fp:
            host_config = json.load(fp)
    except Exception:
        host_config = {}


config = Configuration()
