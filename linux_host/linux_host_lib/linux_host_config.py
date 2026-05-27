import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from linux_host.linux_host_lib.linux_host_jsonc_config import read_linux_host_jsonc_config


@dataclass(slots=True)
class LinuxHostConfig:
    areas: tuple[str, ...] = ('planet', 'monaco')

    repo_root: Path = Path(__file__).resolve().parents[2]
    linux_host_code_dir: Path = repo_root / 'linux_host'
    scripts_dir: Path = linux_host_code_dir / 'scripts'
    nginx_templates_dir: Path = linux_host_code_dir / 'nginx_templates'

    ofm_dir: Path = Path('/data/ofm')
    config_dir: Path = field(init=False)
    linux_host_config_dir: Path = field(init=False)
    linux_host_dir: Path = ofm_dir / 'linux_host'
    runs_dir: Path = linux_host_dir / 'runs'
    assets_dir: Path = linux_host_dir / 'assets'

    mnt_dir: Path = Path('/mnt/ofm')

    nginx_certs_dir: Path = Path('/data/nginx/certs')
    nginx_sites_dir: Path = Path('/data/nginx/sites')

    deployed_versions_dir: Path = field(init=False)

    domains: list[dict[str, Any]] = field(init=False)
    skip_planet: bool = field(init=False)
    telegram_token: str | None = None
    telegram_chat_id: str | None = None

    ofm_host_prefix: str = f'OFM linux_host {socket.gethostname()}'

    def __post_init__(self) -> None:
        if self.ofm_dir.exists():
            self.config_dir = self.ofm_dir / 'config'
        else:
            self.config_dir = self.repo_root / 'config'

        self.linux_host_config_dir = self.config_dir / 'linux_host'
        self.deployed_versions_dir = self.linux_host_config_dir / 'deployed_versions'

        jsonc_path = self.linux_host_config_dir / 'config.jsonc'
        if not jsonc_path.is_file():
            raise FileNotFoundError(f'Linux host config file not found: {jsonc_path}')

        jsonc_data = read_linux_host_jsonc_config(jsonc_path)

        self.domains = jsonc_data['domains']
        self.skip_planet = jsonc_data.get('skip_planet', False)
        self.telegram_token = jsonc_data.get('telegram_token')
        self.telegram_chat_id = jsonc_data.get('telegram_chat_id')


linux_host_config = LinuxHostConfig()
