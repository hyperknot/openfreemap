from pathlib import Path
from typing import Any

from linux_host.deploy_linux_host.benchmark import c1000k, wrk
from linux_host.deploy_linux_host.linux_host_deploy_config import linux_host_deploy_config
from shared_lib.ssh_lib.kernel import kernel_limits1m, kernel_somaxconn65k
from shared_lib.ssh_lib.nginx import nginx
from shared_lib.ssh_lib.utils import put, sudo_cmd


def prepare_linux_host(c, jsonc_config_path: Path, jsonc_config: dict[str, Any]):
    kernel_somaxconn65k(c)
    kernel_limits1m(c)
    nginx(c)

    c.sudo(f'mkdir -p {linux_host_deploy_config.remote_linux_host_dir}/logs')
    c.sudo(f'chown ofm:ofm {linux_host_deploy_config.remote_linux_host_dir}/logs')

    c.sudo(f'mkdir -p {linux_host_deploy_config.remote_linux_host_dir}/logs_nginx')
    c.sudo(f'chown nginx:nginx {linux_host_deploy_config.remote_linux_host_dir}/logs_nginx')

    upload_jsonc_config_and_certs(c, jsonc_config_path, jsonc_config)


def upload_jsonc_config_and_certs(c, jsonc_config_path: Path, jsonc_config: dict[str, Any]):
    c.sudo('mkdir -p /data/nginx/certs')
    c.sudo('rm -rf /data/nginx/certs/ofm-*')

    for domain_data in jsonc_config['domains']:
        if domain_data['cert']['type'] == 'upload':
            local_cert_path = Path(domain_data['cert']['cert_path'])
            if not local_cert_path.is_absolute():
                local_cert_path = (
                    linux_host_deploy_config.local_linux_host_config_dir / local_cert_path
                )

            cert_basename = local_cert_path.stem
            local_key_path = local_cert_path.parent / f'{cert_basename}.key'

            if not local_cert_path.is_file() or not local_key_path.is_file():
                raise FileNotFoundError(
                    f'cert or key file for {domain_data["domain"]} is not found.\n'
                    f'Make sure these files exists:\n{local_cert_path}\n{local_key_path}'
                )

            put(c, local_cert_path, domain_data['cert_file'])
            put(c, local_key_path, domain_data['key_file'])

    put(
        c,
        jsonc_config_path,
        f'{linux_host_deploy_config.remote_linux_host_config}/config.jsonc',
        user='ofm',
        create_parent_dir=True,
    )


def install_linux_host_cron(c):
    put(
        c,
        linux_host_deploy_config.local_linux_host_dir / 'cron.d' / 'ofm_linux_host',
        '/etc/cron.d/',
    )


def run_linux_host_sync(c):
    print('Running linux_host sync --force')
    sudo_cmd(
        c,
        'PYTHONUNBUFFERED=1 ./linux_host/scripts/linux-host.py sync --force',
        cwd=linux_host_deploy_config.remote_source_dir,
    )


def install_benchmark(c):
    """
    Read docs/quick_notes/http_benchmark.md
    """
    c1000k(c)
    wrk(c)
