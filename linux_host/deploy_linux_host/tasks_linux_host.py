import shlex
from pathlib import Path

from fabric import Connection

from linux_host.deploy_linux_host.linux_host_deploy_config import linux_host_deploy_config
from linux_host.deploy_linux_host.nginx import configure_nginx
from linux_host.linux_host_lib.config_loader import (
    read_linux_host_jsonc_config,
    resolve_upload_cert_paths,
)
from shared_lib.ssh_lib.kernel import kernel_limits1m, kernel_somaxconn65k
from shared_lib.ssh_lib.utils import put


def clean_linux_host(c: Connection, areas: list[str]) -> None:
    # Replicas are rebuilt offline instead of reconciling old and new runtime
    # code. Assets, ACME state, and complete images for configured areas survive.
    c.sudo('rm -f /etc/cron.d/ofm_linux_host')
    c.sudo('rm -f /etc/logrotate.d/openfreemap-nginx')
    c.sudo('tmux kill-session -t ofm_linux_host_sync', warn=True, hide=True)
    for signal in ('TERM', 'KILL'):
        command = (
            f"for pid in $(pgrep -f '[l]inux_host.py sync'); do "
            f'pkill -{signal} -P "$pid" || true; done'
        )
        c.sudo(f'bash -c {shlex.quote(command)}', warn=True)
        c.sudo(f"pkill -{signal} -f '[l]inux_host.py sync'", warn=True)
    c.sudo('systemctl stop nginx', warn=True)
    unmounts = "findmnt -rn -o TARGET | grep '^/mnt/ofm/' | sort -r | xargs -r -n1 umount"
    c.sudo(f'bash -c {shlex.quote(unmounts)}')
    c.sudo('rm -rf /mnt/ofm')
    c.sudo('mkdir -p /mnt/ofm')

    versions_dir = f'{linux_host_deploy_config.remote_linux_host_dir}/versions'
    c.sudo(f'mkdir -p {versions_dir}')
    keep_areas = ' '.join(f'! -name {shlex.quote(area)}' for area in areas)
    c.sudo(f'find {versions_dir} -mindepth 1 -maxdepth 1 {keep_areas} -exec rm -rf -- {{}} +')
    c.sudo(
        f'rm -rf {linux_host_deploy_config.remote_linux_host_dir}/runs '
        f'{linux_host_deploy_config.remote_linux_host_dir}/tmp'
    )

    c.sudo(
        f'rm -rf {linux_host_deploy_config.remote_source_dir} '
        f'{linux_host_deploy_config.remote_linux_host_config} '
        f'{linux_host_deploy_config.remote_linux_host_dir}/state '
        f'{linux_host_deploy_config.remote_linux_host_dir}/logs '
        f'{linux_host_deploy_config.remote_linux_host_dir}/logs_nginx '
        '/data/nginx/certs /data/nginx/config /data/nginx/logs /data/nginx/sites'
    )
    c.sudo('rm -f /run/lock/ofm_linux_host.lock')


def prepare_linux_host(c: Connection, jsonc_path: Path) -> None:
    kernel_somaxconn65k(c)
    kernel_limits1m(c)
    configure_nginx(c)
    c.sudo('ufw allow 80/tcp comment "HTTP"', echo=True)
    c.sudo('ufw allow 443/tcp comment "HTTPS"', echo=True)

    c.sudo(f'mkdir -p {linux_host_deploy_config.remote_linux_host_dir}/logs')
    c.sudo(f'chown ofm:ofm {linux_host_deploy_config.remote_linux_host_dir}/logs')

    nginx_logs_dir = f'{linux_host_deploy_config.remote_linux_host_dir}/logs_nginx'
    c.sudo(f'mkdir -p {nginx_logs_dir}')
    c.sudo(f'chown nginx:nginx {nginx_logs_dir}')

    jsonc_data = read_linux_host_jsonc_config(jsonc_path)
    nginx_log_paths = ['/data/nginx/logs/nginx-error.log']
    for domain_data in jsonc_data['domains']:
        base_path = f'{nginx_logs_dir}/{domain_data["slug"]}'
        nginx_log_paths.extend(
            [f'{base_path}-access.jsonl', f'{base_path}-error.log', f'{base_path}-deny.log']
        )
    quoted_log_paths = ' '.join(shlex.quote(path) for path in nginx_log_paths)
    c.sudo(f'touch {quoted_log_paths}')
    c.sudo(f'chown nginx:adm {quoted_log_paths}')
    c.sudo(f'chmod 0640 {quoted_log_paths}')

    upload_jsonc_config_and_certs(c, jsonc_path)


def upload_jsonc_config_and_certs(c: Connection, jsonc_path: Path) -> None:
    jsonc_data = read_linux_host_jsonc_config(jsonc_path)
    c.sudo('mkdir -p /data/nginx/certs')
    c.sudo('rm -rf /data/nginx/certs/ofm-*')

    for domain_data in jsonc_data['domains']:
        if domain_data['cert']['type'] == 'upload':
            local_cert_path, local_key_path = resolve_upload_cert_paths(
                jsonc_path, domain_data['cert']['cert_path']
            )
            remote_cert_path = f'/data/nginx/certs/ofm-{domain_data["slug"]}.cert'
            remote_key_path = f'/data/nginx/certs/ofm-{domain_data["slug"]}.key'

            put(c, local_cert_path, remote_cert_path)
            put(c, local_key_path, remote_key_path)

    put(
        c,
        jsonc_path,
        f'{linux_host_deploy_config.remote_linux_host_config}/config.jsonc',
        user='ofm',
        create_parent_dir=True,
    )
    put(
        c,
        jsonc_path.parent / 'schema.json',
        f'{linux_host_deploy_config.remote_linux_host_config}/schema.json',
        user='ofm',
    )


def run_linux_host_sync_detached(c: Connection, hostname: str) -> None:
    command = (
        f'cd {linux_host_deploy_config.remote_source_dir} && '
        'env PYTHONUNBUFFERED=1 ./linux_host/scripts/linux_host.py sync'
    )
    c.sudo(f'tmux new-session -d -s ofm_linux_host_sync {shlex.quote(command)}')
    print(f'Attach with: ssh -t {shlex.quote(hostname)} sudo tmux attach -t ofm_linux_host_sync')


def install_linux_host_cron(c: Connection) -> None:
    put(
        c,
        linux_host_deploy_config.local_linux_host_dir / 'cron.d' / 'ofm_linux_host',
        '/etc/cron.d/',
    )
