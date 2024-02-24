#!/usr/bin/env python3
import json
import sys

import click
from dotenv import dotenv_values
from fabric import Config, Connection

from ssh_lib import CONFIG_DIR, HTTP_HOST_BIN, OFM_DIR, REMOTE_CONFIG, SCRIPTS_DIR, TILE_GEN_BIN
from ssh_lib.benchmark import c1000k, wrk
from ssh_lib.kernel import kernel_tweaks_ofm
from ssh_lib.nginx import certbot, nginx
from ssh_lib.pkg_base import pkg_base, pkg_upgrade
from ssh_lib.planetiler import planetiler
from ssh_lib.rclone import rclone
from ssh_lib.utils import add_user, enable_sudo, put, put_dir, put_str, sudo_cmd


def prepare_shared(c):
    # creates ofm user with uid=2000, disabled password and nopasswd sudo
    add_user(c, 'ofm', uid=2000)
    enable_sudo(c, 'ofm', nopasswd=True)

    pkg_upgrade(c)
    pkg_base(c)

    kernel_tweaks_ofm(c)

    c.sudo(f'mkdir -p {REMOTE_CONFIG}')
    c.sudo('chown ofm:ofm /data/ofm/config')
    c.sudo('chown ofm:ofm /data/ofm')

    prepare_venv(c)


def prepare_venv(c):
    put(
        c,
        SCRIPTS_DIR / 'prepare-virtualenv.sh',
        OFM_DIR,
        permissions='755',
        user='ofm',
    )
    sudo_cmd(c, f'cd {OFM_DIR} && source prepare-virtualenv.sh')


def prepare_tile_gen(c):
    planetiler(c)
    rclone(c)

    for file in [
        'extract_btrfs.sh',
        'planetiler_monaco.sh',
        'planetiler_planet.sh',
        'cloudflare_index.sh',
        'cloudflare_upload.sh',
    ]:
        put(
            c,
            SCRIPTS_DIR / 'tile_gen' / file,
            TILE_GEN_BIN,
            permissions='755',
        )

    put(
        c,
        SCRIPTS_DIR / 'tile_gen' / 'extract_mbtiles' / 'extract_mbtiles.py',
        f'{TILE_GEN_BIN}/extract_mbtiles/extract_mbtiles.py',
        create_parent_dir=True,
    )

    put(
        c,
        SCRIPTS_DIR / 'tile_gen' / 'shrink_btrfs' / 'shrink_btrfs.py',
        f'{TILE_GEN_BIN}/shrink_btrfs/shrink_btrfs.py',
        create_parent_dir=True,
    )

    if (CONFIG_DIR / 'rclone.conf').exists():
        put(
            c,
            CONFIG_DIR / 'rclone.conf',
            f'{REMOTE_CONFIG}/rclone.conf',
            permissions='600',
            user='ofm',
        )

    c.sudo('chown ofm:ofm /data/ofm/tile_gen')
    c.sudo('chown ofm:ofm -R /data/ofm/tile_gen/bin')


def upload_http_host_config(c):
    domain_direct = dotenv_values(f'{CONFIG_DIR}/.env').get('DOMAIN_DIRECT', '').strip()
    domain_cf = dotenv_values(f'{CONFIG_DIR}/.env').get('DOMAIN_CF', '').strip()
    skip_planet = (
        dotenv_values(f'{CONFIG_DIR}/.env').get('SKIP_PLANET', '').lower().strip() == 'true'
    )

    if not (domain_direct or domain_cf):
        sys.exit('Please specify DOMAIN_DIRECT or DOMAIN_CF in config/.env')

    if domain_cf:
        if (
            not (CONFIG_DIR / 'certs' / 'cf.key').exists()
            or not (CONFIG_DIR / 'certs' / 'cf.cert').exists()
        ):
            sys.exit('When using DOMAIN_CF, please put cf.key and cf.cert files in config/certs')

    host_config = {
        'domain_direct': domain_direct,
        'domain_cf': domain_cf,
        'skip_planet': skip_planet,
    }

    host_config_str = json.dumps(host_config, indent=2, ensure_ascii=False)
    print(host_config_str)
    put_str(c, '/data/ofm/config/http_host.json', host_config_str)


def prepare_http_host(c):
    nginx(c)
    certbot(c)

    c.sudo('rm -rf /data/ofm/http_host/logs')
    c.sudo('mkdir -p /data/ofm/http_host/logs')
    c.sudo('chown ofm:ofm /data/ofm/http_host/logs')

    c.sudo('rm -rf /data/ofm/http_host/logs_nginx')
    c.sudo('mkdir -p /data/ofm/http_host/logs_nginx')
    c.sudo('chown nginx:nginx /data/ofm/http_host/logs_nginx')

    upload_https_host_files(c)
    upload_certificates(c)

    c.sudo('/data/ofm/venv/bin/pip install -e /data/ofm/http_host/bin')


def add_http_host_cron(c):
    put(c, SCRIPTS_DIR / 'http_host' / 'cron.d' / 'ofm_http_host', '/etc/cron.d/')


def run_http_host_sync(c):
    sudo_cmd(c, '/data/ofm/venv/bin/python -u /data/ofm/http_host/bin/host_manager.py sync')


def upload_https_host_files(c):
    c.sudo(f'mkdir -p {HTTP_HOST_BIN}')

    put_dir(c, SCRIPTS_DIR / 'http_host', HTTP_HOST_BIN, file_permissions='755')
    put_dir(c, SCRIPTS_DIR / 'http_host' / 'http_host_lib', f'{HTTP_HOST_BIN}/http_host_lib')
    put_dir(
        c,
        SCRIPTS_DIR / 'http_host' / 'http_host_lib' / 'nginx',
        f'{HTTP_HOST_BIN}/http_host_lib/nginx',
    )

    c.sudo('chown -R ofm:ofm /data/ofm/http_host')


def upload_certificates(c):
    put_dir(c, CONFIG_DIR / 'certs', '/data/nginx/certs', file_permissions=400)
    c.sudo('chown -R nginx:nginx /data/nginx')


def install_benchmark(c):
    """
    Read docs/quick_notes/http_benchmark.md
    """
    c1000k(c)
    wrk(c)


def get_connection(hostname, user, port):
    ssh_passwd = dotenv_values(f'{CONFIG_DIR}/.env').get('SSH_PASSWD', '').strip()

    if ssh_passwd:
        print('Using SSH password')

        c = Connection(
            host=hostname,
            user=user,
            port=port,
            connect_kwargs={'password': ssh_passwd},
            config=Config(overrides={'sudo': {'password': ssh_passwd}}),
        )
    else:
        c = Connection(
            host=hostname,
            user=user,
            port=port,
        )

    return c


def common_options(func):
    """Decorator to define common options."""
    func = click.argument('hostname')(func)
    func = click.option('--port', type=int, help='SSH port (if not in .ssh/config)')(func)
    func = click.option('--user', help='SSH user (if not in .ssh/config)')(func)
    return func


@click.group()
def cli():
    pass


@cli.command()
@common_options
def http_host_once(hostname, user, port):
    if not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)
    prepare_shared(c)

    upload_http_host_config(c)
    prepare_http_host(c)

    run_http_host_sync(c)


@cli.command()
@common_options
def http_host_autoupdate(hostname, user, port):
    if not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)
    prepare_shared(c)

    upload_http_host_config(c)
    prepare_http_host(c)

    add_http_host_cron(c)


@cli.command()
@common_options
def tile_gen(hostname, user, port):
    if not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)
    prepare_shared(c)

    prepare_tile_gen(c)


@cli.command()
@common_options
def debug(hostname, user, port):
    c = get_connection(hostname, user, port)

    # upload_http_host_config(c)

    upload_https_host_files(c)
    # run_http_host_sync(c)

    sudo_cmd(c, '/data/ofm/venv/bin/python -u /data/ofm/http_host/bin/host_manager.py nginx-sync')


if __name__ == '__main__':
    cli()
