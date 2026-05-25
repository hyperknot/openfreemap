import json
from pathlib import Path

import json5
from jsonschema import ValidationError, validate

from .benchmark import c1000k, wrk
from .config import config
from .kernel import kernel_limits1m, kernel_somaxconn65k
from .nginx import nginx
from .slugify import slugify
from .utils import put, put_str, sudo_cmd


def prepare_linux_host(c):
    kernel_somaxconn65k(c)
    kernel_limits1m(c)
    nginx(c)

    c.sudo(f'mkdir -p {config.linux_host_dir}/logs')
    c.sudo(f'chown ofm:ofm {config.linux_host_dir}/logs')

    c.sudo(f'mkdir -p {config.linux_host_dir}/logs_nginx')
    c.sudo(f'chown nginx:nginx {config.linux_host_dir}/logs_nginx')

    upload_config_and_certs(c)


def upload_config_and_certs(c):
    config_data = read_jsonc()

    c.sudo('mkdir -p /data/nginx/certs')
    c.sudo('rm -rf /data/nginx/certs/ofm-*')

    for domain_data in config_data['domains']:
        domain_data['slug'] = slugify(domain_data['domain'], separator='_')

        if domain_data['cert']['type'] == 'upload':
            local_cert_path = Path(domain_data['cert']['cert_path'])
            if not local_cert_path.is_absolute():
                local_cert_path = Path(config.local_config_dir) / local_cert_path

            cert_basename = local_cert_path.stem
            local_key_path = local_cert_path.parent / f'{cert_basename}.key'

            if not local_cert_path.is_file() or not local_key_path.is_file():
                raise FileNotFoundError(
                    f'cert or key file for {domain_data["domain"]} is not found.\n'
                    f'Make sure these files exists:\n{local_cert_path}\n{local_key_path}'
                )

            remote_cert_path = f'/data/nginx/certs/ofm-{domain_data["slug"]}.cert'
            remote_key_path = f'/data/nginx/certs/ofm-{domain_data["slug"]}.key'

            put(c, local_cert_path, remote_cert_path)
            put(c, local_key_path, remote_key_path)

            domain_data['cert_file'] = remote_cert_path
            domain_data['key_file'] = remote_key_path

    config_str = json.dumps(config_data, indent=2, ensure_ascii=False)
    put_str(c, f'{config.remote_config}/config.json', config_str)


def read_jsonc():
    if not config.local_config_jsonc.is_file():
        raise FileNotFoundError(
            f'{config.local_config_jsonc} not found. Make sure it exists in the /config dir'
        )

    try:
        config_data = json5.loads(config.local_config_jsonc.read_text())
    except Exception as e:
        raise RuntimeError(f'Error parsing config file: {e}') from e

    try:
        schema = json.loads(config.config_schema_json.read_text())
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

    return config_data


def install_linux_host_cron(c):
    put(c, config.local_linux_host_dir / 'cron.d' / 'ofm_linux_host', '/etc/cron.d/')


def run_linux_host_sync(c):
    print('Running linux_host sync --force')
    sudo_cmd(
        c, 'uv run python -u -m linux_host.linux_host sync --force', cwd=config.source_dir
    )


def install_benchmark(c):
    """
    Read docs/quick_notes/http_benchmark.md
    """
    c1000k(c)
    wrk(c)
