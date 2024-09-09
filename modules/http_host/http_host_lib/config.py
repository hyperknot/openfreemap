import json
import subprocess
from pathlib import Path


class Configuration:
    areas = ['planet', 'monaco']

    http_host_dir = Path('/data/ofm/http_host')

    http_host_bin = http_host_dir / 'bin'
    http_host_scripts_dir = http_host_bin / 'scripts'

    runs_dir = http_host_dir / 'runs'
    assets_dir = http_host_dir / 'assets'

    mnt_dir = Path('/mnt/ofm')

    certs_dir = Path('/data/nginx/certs')
    nginx_confs = Path(__file__).parent / 'nginx_confs'

    ofm_config_dir = Path('/data/ofm/config')
    deployed_versions_dir = ofm_config_dir / 'deployed_versions'

    ofm_config = json.loads((ofm_config_dir / 'config.json').read_text())

    rclone_config = ofm_config_dir / 'rclone.conf'
    rclone_bin = subprocess.run(['which', 'rclone'], capture_output=True, text=True).stdout.strip()


config = Configuration()
