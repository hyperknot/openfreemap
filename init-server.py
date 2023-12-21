#!/usr/bin/env python3
import sys

import click
from dotenv import dotenv_values
from fabric import Config, Connection

from ssh_lib.benchmark import benchmark, c1000k
from ssh_lib.config import config, scripts
from ssh_lib.kernel import set_cpu_governor, setup_kernel_settings
from ssh_lib.nginx import certbot, nginx
from ssh_lib.pkg_base import pkg_base, pkg_upgrade
from ssh_lib.planetiler import TILE_GEN_BIN, install_planetiler
from ssh_lib.utils import add_user, enable_sudo, put, reboot, setup_time, sudo_cmd


def prepare_shared(c):
    # creates ofm user with uid=2000, disabled password and nopasswd sudo
    add_user(c, 'ofm', uid=2000)
    enable_sudo(c, 'ofm', nopasswd=True)

    pkg_upgrade(c)
    pkg_base(c)

    setup_time(c)
    setup_kernel_settings(c)
    set_cpu_governor(c)


def prepare_tile_gen(c):
    install_planetiler(c)

    for file in [
        'extract_btrfs.sh',
        'planetiler_monaco.sh',
        'planetiler_planet.sh',
        'prepare-virtualenv.sh',
        'upload_cloudflare.sh',
    ]:
        put(
            c,
            scripts / 'tile_gen' / file,
            TILE_GEN_BIN,
            permissions='755',
        )

    put(
        c,
        scripts / 'tile_gen' / 'extract_mbtiles' / 'extract_mbtiles.py',
        f'{TILE_GEN_BIN}/extract_mbtiles/extract_mbtiles.py',
        permissions='755',
        create_parent_dir=True,
    )

    put(
        c,
        scripts / 'tile_gen' / 'shrink_btrfs' / 'shrink_btrfs.py',
        f'{TILE_GEN_BIN}/shrink_btrfs/shrink_btrfs.py',
        permissions='755',
        create_parent_dir=True,
    )

    c.sudo('chown ofm:ofm /data/ofm')
    c.sudo(f'chown -R ofm:ofm {TILE_GEN_BIN}')

    sudo_cmd(c, f'cd {TILE_GEN_BIN} && source prepare-virtualenv.sh', user='ofm')


def prepare_http_host(c):
    nginx(c)
    certbot(c)
    c1000k(c)


def debug_tmp(c):
    c.sudo('rm -rf /data/ofm/logs')
    c.sudo('mkdir -p /data/ofm/logs')
    c.sudo('rm -f /data/nginx/logs/*')
    put(c, f'{config}/nginx/nginx.conf', '/etc/nginx/')
    put(c, f'{scripts}/http_host/nginx_site.conf', '/data/nginx/sites')
    c.sudo('nginx -t')
    c.sudo('service nginx restart')

    benchmark(c)


@click.command()
@click.argument('hostname')
@click.option('--port', type=int, help='SSH port (if not in .ssh/config)')
@click.option('--user', help='SSH user (if not in .ssh/config)')
@click.option('--tile-gen', is_flag=True, help='Install tile-gen task')
@click.option('--http-host', is_flag=True, help='Install http-host task')
@click.option('--reboot', 'do_reboot', is_flag=True, help='Reboot after installation')
@click.option('--debug', is_flag=True)
@click.option(
    '--skip-shared', is_flag=True, help='Skip the shared installtion step (useful for development)'
)
def main(hostname, user, port, tile_gen, http_host, skip_shared, do_reboot, debug):
    if not debug and not click.confirm(f'Run script on {hostname}?'):
        return

    if not tile_gen and not http_host and not debug:
        tile_gen = click.confirm('Would you like to install tile-gen task?')
        http_host = click.confirm('Would you like to install http-host task?')
        if not tile_gen and not http_host:
            return

    ssh_passwd = dotenv_values('.env').get('SSH_PASSWD')

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
        prepare_http_host(c)

    if do_reboot:
        reboot(c)


if __name__ == '__main__':
    main()
