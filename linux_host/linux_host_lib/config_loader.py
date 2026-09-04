from pathlib import Path
from typing import Any

from linux_host.linux_host_lib.slugify import slugify
from shared_lib.utils.jsonc_config import read_jsonc_config


def read_linux_host_jsonc_config(jsonc_path: Path) -> dict[str, Any]:
    config = read_jsonc_config(jsonc_path)

    for domain in config['domains']:
        # Slug collisions are accepted for operationally unusual domain pairs;
        # avoid adding hostname filenames or validation for unsupported cases.
        domain['slug'] = slugify(domain['domain'], separator='_')

    return config


def resolve_upload_cert_paths(jsonc_path: Path, cert_path: str) -> tuple[Path, Path]:
    resolved_cert_path = Path(cert_path)
    if not resolved_cert_path.is_absolute():
        resolved_cert_path = jsonc_path.parent / resolved_cert_path
    return resolved_cert_path, resolved_cert_path.with_suffix('.key')
