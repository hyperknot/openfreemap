import click

from ssh_lib.cli_helpers import common_options, get_connection
from ssh_lib.tasks_shared import prepare_shared
from ssh_lib.tasks_tile_gen import prepare_tile_gen


@click.group()
def cli():
    pass


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
