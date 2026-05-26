import socket
from pathlib import Path

from lib.linux_host_config import read_linux_host_config


class LinuxHostConfig:
    areas = ['planet', 'monaco']

    repo_root = Path(__file__).resolve().parents[2]
    package_dir = Path(__file__).resolve().parents[1]
    scripts_dir = package_dir / 'scripts'
    nginx_templates = package_dir / 'nginx_templates'

    linux_host_dir = Path('/data/ofm/linux_host')
    runs_dir = linux_host_dir / 'runs'
    assets_dir = linux_host_dir / 'assets'

    mnt_dir = Path('/mnt/ofm')

    nginx_certs_dir = Path('/data/nginx/certs')
    nginx_sites_dir = Path('/data/nginx/sites')

    if Path('/data/ofm').exists():
        linux_host_config_dir = Path('/data/ofm/config/linux_host')
    else:
        linux_host_config_dir = repo_root / 'config' / 'linux_host'

    config_jsonc_path = linux_host_config_dir / 'config.jsonc'
    json_config = read_linux_host_config(config_jsonc_path) if config_jsonc_path.exists() else {}
    telegram_token = json_config.pop('telegram_token', None)
    telegram_chat_id = json_config.pop('telegram_chat_id', None)
    ofm_host_prefix = f'OFM linux_host {socket.gethostname()}'

    deployed_versions_dir = linux_host_config_dir / 'deployed_versions'


linux_host_config = LinuxHostConfig()
