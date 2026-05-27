import json
from pathlib import Path
from typing import Any, cast

import json5
from jsonschema import ValidationError, validate

from linux_host.linux_host_lib.slugify import slugify


def read_linux_host_jsonc_config(jsonc_path: Path) -> dict[str, Any]:
    try:
        jsonc_data = cast(dict[str, Any], json5.loads(jsonc_path.read_text()))
    except Exception as e:
        raise RuntimeError(f'Error parsing config file {jsonc_path}: {e}') from e

    _validate_jsonc_config_schema(jsonc_data, jsonc_path.parent / 'schema.json')

    for domain_data in jsonc_data['domains']:
        domain_data['slug'] = slugify(domain_data['domain'], separator='_')

        if domain_data['cert']['type'] == 'upload':
            domain_data['cert_file'] = f'/data/nginx/certs/ofm-{domain_data["slug"]}.cert'
            domain_data['key_file'] = f'/data/nginx/certs/ofm-{domain_data["slug"]}.key'

    return jsonc_data


def _validate_jsonc_config_schema(jsonc_data: dict[str, Any], schema_path: Path) -> None:
    try:
        schema = json.loads(schema_path.read_text())
        validate(instance=jsonc_data, schema=schema)
        print('✓ Configuration is valid')
    except ValidationError as e:
        error_msg = f'Configuration validation failed: {e.message}'
        if e.path:
            error_msg += f'\nPath: {".".join(str(p) for p in e.path)}'
        raise RuntimeError(error_msg) from e
    except Exception as e:
        raise RuntimeError(f'Validation error: {e}') from e
