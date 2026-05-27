#!/usr/bin/env -S uv run python -P
import click

from linux_host.deploy_linux_host.linux_host_deploy_config import linux_host_deploy_config
from linux_host.deploy_linux_host.tasks_linux_host import (
    install_linux_host_cron,
    prepare_linux_host,
    read_jsonc,
    run_linux_host_sync,
)
from shared_lib.deploy_shared.cli_helpers import common_options, get_connection
from shared_lib.deploy_shared.tasks_shared import prepare_shared
from shared_lib.server_health import check_server_health, print_server_health


@click.group()
def cli():
    pass


@cli.command()
@common_options
def init_static(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    prepare_shared(c, linux_host_deploy_config)
    prepare_linux_host(c)

    run_linux_host_sync(c)

    print_linux_host_server_health(hostname)


@cli.command()
@common_options
@click.option('--sync', is_flag=True, help='Run manual sync after init')
def init_autoupdate(hostname, user, port, noninteractive, sync):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    c.sudo('rm -f /etc/cron.d/ofm_linux_host')

    prepare_shared(c, linux_host_deploy_config)
    prepare_linux_host(c)

    # if --sync, run manual sync
    if sync:
        run_linux_host_sync(c)

    install_linux_host_cron(c)

    print_linux_host_server_health(hostname)


@cli.command()
@common_options
def sync(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)
    run_linux_host_sync(c)

    print_linux_host_server_health(hostname)


def print_linux_host_server_health(hostname: str) -> None:
    results = check_server_health(read_jsonc(), hostname)
    print_server_health(results)


if __name__ == '__main__':
    cli()
