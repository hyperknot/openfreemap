import json
import sys
from pathlib import Path

import json5
from jsonschema import ValidationError, validate

from ssh_lib.benchmark import c1000k, wrk
from ssh_lib.config import config
from ssh_lib.kernel import kernel_limits1m, kernel_somaxconn65k
from ssh_lib.nginx import certbot, nginx
from ssh_lib.slugify import slugify
from ssh_lib.utils import put, put_dir, put_str, sudo_cmd


def prepare_http_host(c):
    kernel_somaxconn65k(c)
    kernel_limits1m(c)

    nginx(c)
    # certbot(c)

    c.sudo(f'rm -rf {config.http_host_dir}/logs')
    c.sudo(f'mkdir -p {config.http_host_dir}/logs')
    c.sudo(f'chown ofm:ofm {config.http_host_dir}/logs')

    c.sudo(f'rm -rf {config.http_host_dir}/logs_nginx')
    c.sudo(f'mkdir -p {config.http_host_dir}/logs_nginx')
    c.sudo(f'chown nginx:nginx {config.http_host_dir}/logs_nginx')

    upload_http_host_files(c)
    c.sudo(f'{config.venv_bin}/pip install -e {config.http_host_bin} --use-pep517')

    upload_config_and_certs(c)


def upload_config_and_certs(c):
    if not config.local_config_jsonc.is_file():
        print(f'{config.local_config_jsonc} not found. Make sure it exists in the /config dir')
        return

    # Load and parse the JSONC/JSON5 config file
    try:
        config_data = json5.loads(config.local_config_jsonc.read_text())
    except Exception as e:
        print(f'❌ Error parsing config file: {e}')
        return

    # Load the JSON schema
    try:
        schema = json.loads(config.config_schema_json.read_text())
    except Exception as e:
        print(f'❌ Error loading schema file: {e}')
        return

    # Validate the config against the schema
    try:
        validate(instance=config_data, schema=schema)
        print('✓ Configuration is valid')
    except ValidationError as e:
        print('❌ Configuration validation failed:')
        print(f'   Error: {e.message}')
        if e.path:
            print(f'   Path: {".".join(str(p) for p in e.path)}')
        return
    except Exception as e:
        print(f'❌ Validation error: {e}')
        return

    # pre-generate all the slugs
    for domain_data in config_data['domains']:
        domain_data['slug'] = slugify(domain_data['domain'], separator='_')

        if domain_data['cert']['type'] == 'upload':
            print(domain_data)
            local_cert_path = Path(domain_data['cert']['cert_path'])

            # handle relative paths - make them relative to config.local_config_dir
            if not local_cert_path.is_absolute():
                local_cert_path = Path(config.local_config_dir) / local_cert_path

            cert_basename = local_cert_path.stem
            local_key_path = local_cert_path.parent / f'{cert_basename}.key'

            if not local_cert_path.is_file() or not local_key_path.is_file():
                print(
                    f'cert or key file for {domain_data["domain"]} is not found.\nMake sure these files exists:\n{local_cert_path}\n{local_key_path}\n------'
                )

            remote_cert_path = f'/data/nginx/certs/ofm-{domain_data["slug"]}.cert'
            remote_key_path = f'/data/nginx/certs/ofm-{domain_data["slug"]}.key'

            put(c, local_cert_path, remote_cert_path)
            put(c, local_key_path, remote_key_path)

    # generate a normal JSON and upload it
    config_str = json.dumps(config_data, indent=2, ensure_ascii=False)
    put_str(c, f'{config.remote_config}/config.json', config_str)


def upload_http_host_files(c):
    c.sudo(f'rm -rf {config.http_host_bin}')
    c.sudo(f'mkdir -p {config.http_host_bin}')

    put_dir(c, config.local_modules_dir / 'http_host', config.http_host_bin, file_permissions='755')

    for dirname in ['http_host_lib', 'scripts']:
        put_dir(
            c, config.local_modules_dir / 'http_host' / dirname, f'{config.http_host_bin}/{dirname}'
        )

    put_dir(
        c,
        config.local_modules_dir / 'http_host' / 'http_host_lib' / 'nginx_templates',
        f'{config.http_host_bin}/http_host_lib/nginx_templates',
    )

    c.sudo('chown -R ofm:ofm /data/ofm/http_host')


def run_http_host_sync(c):
    print('Running http_host.py sync --force')
    sudo_cmd(c, f'{config.venv_bin}/python -u {config.http_host_bin}/http_host.py sync --force')


def install_benchmark(c):
    """
    Read docs/quick_notes/http_benchmark.md
    """
    c1000k(c)
    wrk(c)
