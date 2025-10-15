#!/usr/bin/env python3

import click
import json5

from ssh_lib.cli_helpers import common_options, get_connection
from ssh_lib.config import config
from ssh_lib.tasks_http_host import prepare_http_host, run_http_host_sync
from ssh_lib.tasks_shared import prepare_shared
from ssh_lib.utils import (
    put,
)


@click.group()
def cli():
    pass


@cli.command()
@common_options
def init_static(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    prepare_shared(c)
    prepare_http_host(c)

    run_http_host_sync(c)


@cli.command()
@common_options
def init_autoupdate(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    c.sudo('rm -f /etc/cron.d/ofm_http_host')

    prepare_shared(c)
    prepare_http_host(c)

    # for the monaco run, wait for the sync to complete
    if json5.loads(config.local_config_jsonc.read_text()).get('skip_planet'):
        run_http_host_sync(c)

    put(c, config.local_modules_dir / 'http_host' / 'cron.d' / 'ofm_http_host', '/etc/cron.d/')


@cli.command()
@common_options
def sync(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)
    run_http_host_sync(c)


if __name__ == '__main__':
    cli()
