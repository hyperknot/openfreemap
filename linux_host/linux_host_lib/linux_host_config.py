import copy
import json
import socket
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
