import json
import socket
from dataclasses import dataclass, field
from pathlib import Path

import json5
from jsonschema import ValidationError, validate

from linux_host.linux_host_lib.slugify import slugify


def read_linux_host_jsonc_config(jsonc_config_path: Path) -> dict:
    try:
        jsonc_config = json5.loads(jsonc_config_path.read_text())
    except Exception as e:
        raise RuntimeError(f'Error parsing config file {jsonc_config_path}: {e}') from e

    validate_jsonc_config_schema(jsonc_config)

    for domain_data in jsonc_config['domains']:
        domain_data['slug'] = slugify(domain_data['domain'], separator='_')

        if domain_data['cert']['type'] == 'upload':
            domain_data['cert_file'] = f'/data/nginx/certs/ofm-{domain_data["slug"]}.cert'
            domain_data['key_file'] = f'/data/nginx/certs/ofm-{domain_data["slug"]}.key'

    return jsonc_config


def validate_jsonc_config_schema(jsonc_config: dict) -> None:
    schema_path = Path(__file__).resolve().parents[2] / 'config' / 'linux_host' / 'schema.json'

    try:
        schema = json.loads(schema_path.read_text())
        validate(instance=jsonc_config, schema=schema)
        print('✓ Configuration is valid')
    except ValidationError as e:
        error_msg = f'Configuration validation failed: {e.message}'
        if e.path:
            error_msg += f'\nPath: {".".join(str(p) for p in e.path)}'
        raise RuntimeError(error_msg) from e
    except Exception as e:
        raise RuntimeError(f'Validation error: {e}') from e


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
    jsonc_config_path: Path = field(init=False)
    deployed_versions_dir: Path = field(init=False)

    telegram_token: str | None = None
    telegram_chat_id: str | None = None
    jsonc_config: dict = field(default_factory=dict)

    ofm_host_prefix: str = f'OFM linux_host {socket.gethostname()}'

    def __post_init__(self) -> None:
        if Path('/data/ofm').exists():
            self.linux_host_config_dir = Path('/data/ofm/config/linux_host')
        else:
            self.linux_host_config_dir = self.repo_root / 'config' / 'linux_host'

        self.jsonc_config_path = self.linux_host_config_dir / 'config.jsonc'
        self.deployed_versions_dir = self.linux_host_config_dir / 'deployed_versions'

    def load_jsonc_config(self) -> None:
        if not self.jsonc_config_path.is_file():
            raise FileNotFoundError(f'Linux host config file not found: {self.jsonc_config_path}')

        self.jsonc_config = read_linux_host_jsonc_config(self.jsonc_config_path)
        self.telegram_token = self.jsonc_config.pop('telegram_token', None)
        self.telegram_chat_id = self.jsonc_config.pop('telegram_chat_id', None)


linux_host_config = LinuxHostConfig()
