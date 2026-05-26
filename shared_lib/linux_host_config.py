import copy
import json
from pathlib import Path

import json5
from jsonschema import ValidationError, validate

from shared_lib.slugify import slugify


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
