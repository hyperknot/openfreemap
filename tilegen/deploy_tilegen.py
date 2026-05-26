#!/usr/bin/env -S uv run python -P
import click

from shared_lib.deploy.cli_helpers import common_options, get_connection
from shared_lib.deploy.tasks_shared import prepare_shared
from tilegen.deploy_lib.tasks_tilegen import prepare_tilegen
from tilegen.deploy_lib.tilegen_deploy_config import tilegen_deploy_config


@click.group()
def cli():
    pass


@cli.command()
@common_options
@click.option('--cron', is_flag=True, help='Enable cron task')
@click.option('--reinstall', is_flag=True, help='Reinstall everything in /data/ofm folder')
def tilegen(
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

    prepare_shared(c, tilegen_deploy_config)
    prepare_tilegen(c, enable_cron=cron)


if __name__ == '__main__':
    cli()
