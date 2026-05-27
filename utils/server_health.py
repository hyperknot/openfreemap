#!/usr/bin/env -S uv run python -P

import click

from linux_host.deploy_linux_host.linux_host_deploy_config import linux_host_deploy_config
from linux_host.linux_host_lib.linux_host_jsonc_config import read_linux_host_jsonc_config
from shared_lib.utils.server_health import check_server_health


@click.command()
@click.option('--hostname', help='Check only a specific server')
def cli(hostname: str | None):
    jsonc_config_path = linux_host_deploy_config.local_linux_host_config_dir / 'config.jsonc'
    check_server_health(
        read_linux_host_jsonc_config(jsonc_config_path), hostname, print_results=True
    )


if __name__ == '__main__':
    cli()
