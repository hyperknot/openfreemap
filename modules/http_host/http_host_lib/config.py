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

    nginx_templates = Path(__file__).parent / 'nginx_templates'

    nginx_certs_dir = Path('/data/nginx/certs')
    nginx_sites_dir = Path('/data/nginx/sites')

    if Path('/data/ofm').exists():
        ofm_config_dir = Path('/data/ofm/config')
    else:
        repo_root = Path(__file__).parent.parent.parent.parent
        ofm_config_dir = repo_root / 'config'

    json_config = json.loads((ofm_config_dir / 'config.json').read_text())

    deployed_versions_dir = ofm_config_dir / 'deployed_versions'

    rclone_config = ofm_config_dir / 'rclone.conf'
    rclone_bin = subprocess.run(['which', 'rclone'], capture_output=True, text=True).stdout.strip()


config = Configuration()
