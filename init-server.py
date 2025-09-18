#!/usr/bin/env python3

import click
from fabric import Config, Connection

from ssh_lib import MODULES_DIR, dotenv_val
from ssh_lib.tasks import (
    prepare_http_host,
    prepare_shared,
    prepare_tile_gen,
    run_http_host_sync,
)
from ssh_lib.utils import (
    put,
)


def get_connection(hostname, user, port):
    ssh_passwd = dotenv_val('SSH_PASSWD')

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
    func = click.option('-y', '--noninteractive', is_flag=True, help='Skip confirmation questions')(
        func
    )
    return func


@click.group()
def cli():
    pass


@cli.command()
@common_options
def http_host_static(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    prepare_shared(c)
    prepare_http_host(c)

    run_http_host_sync(c)


@cli.command()
@common_options
def http_host_autoupdate(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    c.sudo('rm -f /etc/cron.d/ofm_http_host')

    prepare_shared(c)
    prepare_http_host(c)

    run_http_host_sync(c)  # disable for first install if you don't want to wait

    put(c, MODULES_DIR / 'http_host' / 'cron.d' / 'ofm_http_host', '/etc/cron.d/')


@cli.command()
@common_options
@click.option('--cron', is_flag=True, help='Enable cron task')
@click.option('--reinstall', is_flag=True, help='Reinstall everything in /data/ofm folder')
def tile_gen(
    hostname,
    user,
    port,
    noninteractive,
    #
    cron,
    reinstall,
):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    if reinstall:
        c.sudo('rm -rf /data/ofm')

    prepare_shared(c)
    prepare_tile_gen(c, enable_cron=cron)


@cli.command()
@common_options
def http_host_sync(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)
    run_http_host_sync(c)


@cli.command()
@common_options
def debug(hostname, user, port, noninteractive):
    c = get_connection(hostname, user, port)
    run_http_host_sync(c)


if __name__ == '__main__':
    cli()
