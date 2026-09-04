from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

from linux_host.linux_host_lib.config_loader import read_linux_host_jsonc_config


@dataclass(slots=True)
class LinuxHostConfig:
    areas: tuple[str, ...] = field(init=False)
    auto_update: bool = field(init=False)

    repo_root: Path = Path(__file__).resolve().parents[2]
    linux_host_code_dir: Path = repo_root / 'linux_host'
    nginx_templates_dir: Path = linux_host_code_dir / 'nginx_templates'

    ofm_dir: Path = Path('/data/ofm')
    config_dir: Path = field(init=False)
    linux_host_config_dir: Path = field(init=False)
    linux_host_dir: Path = ofm_dir / 'linux_host'
    versions_dir: Path = linux_host_dir / 'versions'
    tmp_dir: Path = linux_host_dir / 'tmp'
    assets_dir: Path = linux_host_dir / 'assets'

    mnt_dir: Path = Path('/mnt/ofm')

    nginx_certs_dir: Path = Path('/data/nginx/certs')
    nginx_sites_dir: Path = Path('/data/nginx/sites')

    deployed_versions_dir: Path = field(init=False)
    lock_file: Path = Path('/run/lock/ofm_linux_host.lock')

    domains: list[dict[str, Any]] = field(init=False)
    hosts: list[str] = field(init=False)
    root_redirect_url: str | None = field(init=False)
    telegram_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_topic_id: int | None = None

    def __post_init__(self) -> None:
        if self.ofm_dir.exists():
            self.config_dir = self.ofm_dir / 'config'
        else:
            self.config_dir = self.repo_root / 'config'

        self.linux_host_config_dir = self.config_dir / 'linux_host'
        self.deployed_versions_dir = self.linux_host_dir / 'state' / 'deployed_versions'

        jsonc_path = self.linux_host_config_dir / 'config.jsonc'
        if not jsonc_path.is_file():
            raise FileNotFoundError(f'linux_host config file not found: {jsonc_path}')

        jsonc_data = read_linux_host_jsonc_config(jsonc_path)

        self.areas = tuple(jsonc_data['areas'])
        self.auto_update = jsonc_data['auto_update']
        self.domains = jsonc_data['domains']
        self.hosts = jsonc_data['hosts']
        self.root_redirect_url = jsonc_data.get('root_redirect_url')
        self.telegram_token = jsonc_data.get('telegram_token')
        self.telegram_chat_id = jsonc_data.get('telegram_chat_id')
        self.telegram_topic_id = jsonc_data.get('telegram_topic_id')


@cache
def get_linux_host_config() -> LinuxHostConfig:
    # Lazy construction keeps Click help and helper imports independent of the
    # ignored machine-specific config while retaining one process-wide config.
    # The accessor avoids threading fixed config through every helper; local
    # imports would still leave reusable helpers coupled to config at import time.
    return LinuxHostConfig()
