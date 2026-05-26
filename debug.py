#!/usr/bin/env -S uv run
import click

from linux_host.deploy_lib.tasks_linux_host import upload_config_and_certs
from shared_lib.deploy_shared.cli_helpers import common_options, get_connection


@click.group()
def cli():
    pass


@cli.command()
@common_options
def debug(hostname, user, port, noninteractive):
    c = get_connection(hostname, user, port)
    upload_config_and_certs(c)


if __name__ == '__main__':
    cli()
