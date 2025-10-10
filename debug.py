import click

from ssh_lib.cli_helpers import common_options, get_connection
from ssh_lib.tasks_http_host import upload_config_and_certs


@click.group()
def cli():
    pass


@cli.command()
@common_options
def debug(hostname, user, port, noninteractive):
    c = get_connection(hostname, user, port)
    upload_config_and_certs(c)
