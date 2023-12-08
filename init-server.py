#!/usr/bin/env python3

import click
from dotenv import dotenv_values
from fabric import Config, Connection

from ssh_lib.config import scripts
from ssh_lib.kernel import set_cpu_governor, setup_kernel_settings
from ssh_lib.nginx import certbot, nginx
from ssh_lib.pkg_base import pkg_base, pkg_clean, pkg_upgrade
from ssh_lib.planetiler import TILE_GEN_BIN, install_planetiler
from ssh_lib.utils import add_user, enable_sudo, put, setup_time, sudo_cmd


def prepare_shared(c):
    add_user(
        c,
        'ofm',
        passwd='x',
    )
    enable_sudo(c, 'ofm')

    pkg_upgrade(c)
    pkg_clean(c)
    pkg_base(c)

    setup_time(c)
    setup_kernel_settings(c)
    set_cpu_governor(c)


def prepare_tile_gen(c):
    # install_planetiler(c)

    for file in [
        'prepare-virtualenv.sh',
        'planetiler_planet.sh',
        'planetiler_monaco.sh',
        'gen_monaco.sh',
        'extract.sh',
    ]:
        put(
            c,
            scripts / 'tile_gen' / file,
            TILE_GEN_BIN,
            permissions='755',
            owner='ofm',
        )

    # sudo_cmd(c, f'cd {TILE_GEN_BIN} && source prepare-virtualenv.sh', user='ofm')


def prepare_http_host(c):
    nginx(c)
    certbot(c)


@click.command()
@click.argument('hostname')
@click.option('--port', type=int, help='SSH port (if not in .ssh/config)')
@click.option('--user', help='SSH user (if not in .ssh/config)')
@click.option('--tile-gen', is_flag=True, help='Install tile-gen task')
@click.option('--http-host', is_flag=True, help='Install http-host task')
@click.option(
    '--skip-shared', is_flag=True, help='Skip the shared installtion step (useful for development)'
)
def main(hostname, user, port, tile_gen, http_host, skip_shared):
    if not click.confirm(f'Run script on {hostname}?'):
        return

    if not tile_gen and not http_host:
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

    if not skip_shared:
        prepare_shared(c)

    if tile_gen:
        prepare_tile_gen(c)

    if http_host:
        prepare_http_host(c)


if __name__ == '__main__':
    main()
