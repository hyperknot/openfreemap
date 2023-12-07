#!/usr/bin/env python3

import click
from dotenv import dotenv_values
from fabric import Config, Connection

from ssh_lib.config import scripts
from ssh_lib.kernel import set_cpu_governor, setup_kernel_settings
from ssh_lib.nginx import certbot, nginx
from ssh_lib.pkg_base import pkg_base, pkg_clean, pkg_upgrade
from ssh_lib.planetiler import TILE_GEN_BIN, install_planetiler
from ssh_lib.utils import add_user, put, setup_time, sudo_cmd


def prepare_shared(c):
    add_user(c, 'ofm')

    pkg_upgrade(c)
    pkg_clean(c)
    pkg_base(c)

    setup_time(c)
    setup_kernel_settings(c)
    set_cpu_governor(c)


def prepare_tile_creator(c):
    install_planetiler(c)

    put(
        c,
        scripts / 'tile_creator' / 'prepare-virtualenv.sh',
        TILE_GEN_BIN,
        permissions='755',
        owner='ofm',
    )

    put(
        c,
        scripts / 'tile_creator' / 'run_planet.sh',
        TILE_GEN_BIN,
        permissions='755',
        owner='ofm',
    )

    sudo_cmd(c, f'cd {TILE_GEN_BIN} && source prepare-virtualenv.sh', user='ofm')


def prepare_http_host(c):
    nginx(c)
    certbot(c)


@click.command()
@click.argument('hostname')
@click.option('--port', type=int, help='SSH port (if not in .ssh/config)')
@click.option('--user', help='SSH user (if not in .ssh/config)')
@click.option('--tile-creator', is_flag=True, help='Install tile-creator task')
@click.option('--http-host', is_flag=True, help='Install http-host task')
def main(hostname, user, port, tile_creator, http_host):
    if not click.confirm(f'Run script on {hostname}?'):
        return

    if not tile_creator and not http_host:
        tile_creator = click.confirm('Would you like to install tile-creator task?')
        http_host = click.confirm('Would you like to install http-host task?')
        if not tile_creator and not http_host:
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

    # prepare_shared(c)

    if tile_creator:
        prepare_tile_creator(c)

    if http_host:
        prepare_http_host(c)


if __name__ == '__main__':
    main()
