import json
import socket
import subprocess
from pathlib import Path


class Configuration:
    areas = ['planet', 'monaco']

    repo_root = Path(__file__).resolve().parent.parent
    package_dir = Path(__file__).resolve().parent
    scripts_dir = package_dir / 'scripts'
    nginx_templates = package_dir / 'nginx_templates'

    linux_host_dir = Path('/data/ofm/linux_host')
    runs_dir = linux_host_dir / 'runs'
    assets_dir = linux_host_dir / 'assets'

    mnt_dir = Path('/mnt/ofm')

    nginx_certs_dir = Path('/data/nginx/certs')
    nginx_sites_dir = Path('/data/nginx/sites')

    if Path('/data/ofm').exists():
        ofm_config_dir = Path('/data/ofm/config')
    else:
        ofm_config_dir = repo_root / 'config'

    config_json_path = ofm_config_dir / 'config.json'
    json_config = json.loads(config_json_path.read_text()) if config_json_path.exists() else {}
    telegram_token = json_config.pop('telegram_token', None)
    telegram_chat_id = json_config.pop('telegram_chat_id', None)
    ofm_host_prefix = f'OFM linux_host {socket.gethostname()}'

    deployed_versions_dir = ofm_config_dir / 'deployed_versions'

    rclone_config = ofm_config_dir / 'rclone.conf'
    rclone_bin = subprocess.run(['which', 'rclone'], capture_output=True, text=True).stdout.strip()


config = Configuration()
