#!/usr/bin/env -S uv run python -P

import click

from linux_host.deploy_linux_host.tasks_linux_host import read_jsonc
from shared_lib.server_health import check_server_health, print_server_health


@click.command()
@click.option('--hostname', help='Check only a specific server')
def cli(hostname):
    results = check_server_health(read_jsonc(), hostname)
    print_server_health(results)


if __name__ == '__main__':
    cli()
