#!/usr/bin/env python3

import click
from fabric import Config, Connection

from ssh_lib import MODULES_DIR, dotenv_val
from ssh_lib.tasks import (
    prepare_http_host,
    prepare_shared,
    prepare_tile_gen,
    run_http_host_sync,
    setup_ledns_writer,
    setup_loadbalancer,
    upload_config_json,
    upload_http_host_files,
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
    return func


@click.group()
def cli():
    pass


@cli.command()
@common_options
def http_host_static(hostname, user, port):
    if not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    prepare_shared(c)
    upload_config_json(c)

    prepare_http_host(c)

    run_http_host_sync(c)


@cli.command()
@common_options
def http_host_autoupdate(hostname, user, port):
    if not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    c.sudo('rm -f /etc/cron.d/ofm_http_host')

    prepare_shared(c)

    upload_config_json(c)
    prepare_http_host(c)

    run_http_host_sync(c)

    put(c, MODULES_DIR / 'http_host' / 'cron.d' / 'ofm_http_host', '/etc/cron.d/')


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
def ledns(hostname, user, port):
    if not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    setup_ledns_writer(c)


@cli.command()
@common_options
def loadbalancer(hostname, user, port):
    if not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)
    prepare_shared(c)

    setup_loadbalancer(c)


@cli.command()
@common_options
def debug(hostname, user, port):
    c = get_connection(hostname, user, port)

    upload_config_json(c)


if __name__ == '__main__':
    cli()
