import copy
import json
import socket
from dataclasses import dataclass, field
from pathlib import Path

import json5
from jsonschema import ValidationError, validate

from linux_host.linux_host_lib.slugify import slugify


def read_linux_host_config(config_path: Path, *, validate_schema: bool = False) -> dict:
    try:
        config_data = json5.loads(config_path.read_text())
    except Exception as e:
        raise RuntimeError(f'Error parsing config file: {e}') from e

    if validate_schema:
        validate_linux_host_config(config_data, config_path.parent / 'schema.json')

    return with_derived_linux_host_config(config_data)


def with_derived_linux_host_config(config_data: dict) -> dict:
    config_data = copy.deepcopy(config_data)

    for domain_data in config_data['domains']:
        domain_data['slug'] = slugify(domain_data['domain'], separator='_')

        if domain_data['cert']['type'] == 'upload':
            domain_data['cert_file'] = f'/data/nginx/certs/ofm-{domain_data["slug"]}.cert'
            domain_data['key_file'] = f'/data/nginx/certs/ofm-{domain_data["slug"]}.key'

    return config_data


def validate_linux_host_config(config_data: dict, schema_path: Path) -> None:
    try:
        schema = json.loads(schema_path.read_text())
    except Exception as e:
        raise RuntimeError(f'Error loading schema file: {e}') from e

    try:
        validate(instance=config_data, schema=schema)
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

    if Path('/data/ofm').exists():
        linux_host_config_dir: Path = Path('/data/ofm/config/linux_host')
    else:
        linux_host_config_dir: Path = repo_root / 'config' / 'linux_host'

    config_jsonc_path: Path = linux_host_config_dir / 'config.jsonc'

    _json_config = read_linux_host_config(config_jsonc_path) if config_jsonc_path.exists() else {}
    telegram_token: str | None = _json_config.pop('telegram_token', None)
    telegram_chat_id: str | None = _json_config.pop('telegram_chat_id', None)
    json_config: dict = field(default_factory=lambda: copy.deepcopy(LinuxHostConfig._json_config))

    ofm_host_prefix: str = f'OFM linux_host {socket.gethostname()}'

    deployed_versions_dir: Path = linux_host_config_dir / 'deployed_versions'


linux_host_config = LinuxHostConfig()
