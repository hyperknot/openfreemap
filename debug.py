#!/usr/bin/env -S uv run
import click

from linux_host.deploy_linux_host.linux_host_deploy_config import linux_host_deploy_config
from linux_host.deploy_linux_host.tasks_linux_host import upload_jsonc_config_and_certs
from linux_host.linux_host_lib.linux_host_config import read_linux_host_jsonc_config
from shared_lib.deploy_shared.cli_helpers import common_options, get_connection


@click.group()
def cli():
    pass


@cli.command()
@common_options
def debug(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    jsonc_config_path = linux_host_deploy_config.local_linux_host_config_dir / 'config.jsonc'
    jsonc_config = read_linux_host_jsonc_config(jsonc_config_path)

    c = get_connection(hostname, user, port)
    upload_jsonc_config_and_certs(c, jsonc_config_path, jsonc_config)


if __name__ == '__main__':
    cli()
