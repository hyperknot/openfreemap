import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from linux_host.linux_host_lib.linux_host_jsonc_config import read_linux_host_jsonc_config


@dataclass(slots=True)
class LinuxHostConfig:
    areas: tuple[str, ...] = ('planet', 'monaco')

    repo_root: Path = Path(__file__).resolve().parents[2]
    package_dir: Path = Path(__file__).resolve().parents[1]
    scripts_dir: Path = package_dir / 'scripts'
    nginx_templates: Path = package_dir / 'nginx_templates'

    linux_host_dir: Path = Path('/data/ofm/linux_host')
    runs_dir: Path = linux_host_dir / 'runs'
    assets_dir: Path = linux_host_dir / 'assets'

    mnt_dir: Path = Path('/mnt/ofm')

    nginx_certs_dir: Path = Path('/data/nginx/certs')
    nginx_sites_dir: Path = Path('/data/nginx/sites')

    linux_host_config_dir: Path = field(init=False)
    deployed_versions_dir: Path = field(init=False)

    domains: list[dict[str, Any]] = field(init=False)
    skip_planet: bool = field(init=False)
    telegram_token: str | None = None
    telegram_chat_id: str | None = None

    ofm_host_prefix: str = f'OFM linux_host {socket.gethostname()}'

    def __post_init__(self) -> None:
        if Path('/data/ofm').exists():
            self.linux_host_config_dir = Path('/data/ofm/config/linux_host')
        else:
            self.linux_host_config_dir = self.repo_root / 'config' / 'linux_host'

        self.deployed_versions_dir = self.linux_host_config_dir / 'deployed_versions'

        jsonc_config_path = self.linux_host_config_dir / 'config.jsonc'
        if not jsonc_config_path.is_file():
            raise FileNotFoundError(f'Linux host config file not found: {jsonc_config_path}')

        jsonc_config = read_linux_host_jsonc_config(jsonc_config_path)

        self.domains = jsonc_config['domains']
        self.skip_planet = jsonc_config.get('skip_planet', False)
        self.telegram_token = jsonc_config.get('telegram_token')
        self.telegram_chat_id = jsonc_config.get('telegram_chat_id')


linux_host_config = LinuxHostConfig()
