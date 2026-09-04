import json
from pathlib import Path
from typing import Any, cast

import json5
from jsonschema import ValidationError, validate


def read_jsonc_config(jsonc_path: Path) -> dict[str, Any]:
    if not jsonc_path.is_file():
        raise FileNotFoundError(f'Config file not found: {jsonc_path}')

    try:
        jsonc_data = cast(dict[str, Any], json5.loads(jsonc_path.read_text()))
    except Exception as e:
        raise RuntimeError(f'Error parsing config file {jsonc_path}: {e}') from e

    _validate_jsonc_config_schema(jsonc_data, jsonc_path.parent / 'schema.json')
    return jsonc_data


def _validate_jsonc_config_schema(jsonc_data: dict[str, Any], schema_path: Path) -> None:
    try:
        schema = json.loads(schema_path.read_text())
        validate(instance=jsonc_data, schema=schema)
    except ValidationError as e:
        error_msg = f'Configuration validation failed: {e.message}'
        if e.path:
            error_msg += f'\nPath: {".".join(str(p) for p in e.path)}'
        raise RuntimeError(error_msg) from None
    except Exception as e:
        raise RuntimeError(f'Validation error: {e}') from e
