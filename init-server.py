#!/usr/bin/env python3
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
from ssh_lib.utils import add_user, enable_sudo, put, put_dir, reboot, sudo_cmd


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
        owner='ofm',
    )
    sudo_cmd(c, f'cd {OFM_DIR} && source prepare-virtualenv.sh', user='ofm')


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
            owner='ofm',
        )

    c.sudo('chown ofm:ofm /data/ofm/tile_gen')
    c.sudo('chown ofm:ofm -R /data/ofm/tile_gen/bin')


def prepare_http_host(c, skip_cron: bool):
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

    # always last
    if not skip_cron:
        put(c, SCRIPTS_DIR / 'http_host' / 'cron.d' / 'ofm_http_host', '/etc/cron.d/')


def upload_https_host_files(c):
    c.sudo(f'mkdir -p {HTTP_HOST_BIN}')

    put_dir(c, SCRIPTS_DIR / 'http_host', HTTP_HOST_BIN, file_permissions='755')
    put_dir(c, SCRIPTS_DIR / 'http_host' / 'http_host_lib', f'{HTTP_HOST_BIN}/http_host_lib')
    put_dir(
        c,
        SCRIPTS_DIR / 'http_host' / 'http_host_lib' / 'templates',
        f'{HTTP_HOST_BIN}/http_host_lib/templates',
    )

    c.sudo('chown -R ofm:ofm /data/ofm/http_host')


def upload_certificates(c):
    put_dir(c, CONFIG_DIR / 'certs', '/data/nginx/certs', file_permissions=400)
    c.sudo('chown -R nginx:nginx /data/nginx')


def install_benchmark(c):
    c1000k(c)
    wrk(c)


def debug_tmp(c):
    upload_https_host_files(c)
    # put(c, SCRIPTS_DIR / 'http_host' / 'cron.d' / 'ofm_http_host', '/etc/cron.d/')


@click.command()
@click.argument('hostname')
@click.option('--port', type=int, help='SSH port (if not in .ssh/config)')
@click.option('--user', help='SSH user (if not in .ssh/config)')
@click.option('--tile-gen', is_flag=True, help='Install tile-gen task')
@click.option('--http-host', is_flag=True, help='Install http-host task')
@click.option('--debug', is_flag=True)
@click.option(
    '--skip-shared', is_flag=True, help='Skip the shared installtion step (useful for development)'
)
@click.option('--skip-cron', is_flag=True, help='Skip the cronjob (useful for development)')
def main(hostname, user, port, tile_gen, http_host, skip_shared, skip_cron, debug):
    if not debug and not click.confirm(f'Run script on {hostname}?'):
        return

    if not tile_gen and not http_host and not debug:
        tile_gen = click.confirm('Would you like to install tile-gen task?')
        http_host = click.confirm('Would you like to install http-host task?')
        if not tile_gen and not http_host:
            return

    ssh_passwd = dotenv_values(f'{CONFIG_DIR}/.env').get('SSH_PASSWD')

    if ssh_passwd:
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

    if debug:
        debug_tmp(c)
        sys.exit()

    if not skip_shared:
        prepare_shared(c)

    if tile_gen:
        prepare_tile_gen(c)

    if http_host:
        prepare_http_host(c, skip_cron=skip_cron)


if __name__ == '__main__':
    main()
