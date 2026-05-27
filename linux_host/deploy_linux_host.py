#!/usr/bin/env -S uv run python -P
from pathlib import Path
from typing import Any

import click

from linux_host.deploy_linux_host.linux_host_deploy_config import linux_host_deploy_config
from linux_host.deploy_linux_host.tasks_linux_host import (
    install_linux_host_cron,
    prepare_linux_host,
    run_linux_host_sync,
)
from linux_host.linux_host_lib.linux_host_jsonc_config import read_linux_host_jsonc_config
from shared_lib.deploy_shared.cli_helpers import common_options, get_connection
from shared_lib.deploy_shared.tasks_shared import prepare_shared
from shared_lib.utils.server_health import check_server_health


@click.group()
def cli():
    pass


@cli.command()
@common_options
@click.option('--config', default='config', show_default=True, help='Config name without .jsonc')
def init_static(
    hostname: str, user: str | None, port: int | None, noninteractive: bool, config: str
):
    jsonc_config_path, jsonc_config = load_jsonc_config(config)

    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    prepare_shared(c, linux_host_deploy_config)
    prepare_linux_host(c, jsonc_config_path)

    run_linux_host_sync(c)

    check_server_health(jsonc_config, hostname, print_results=True)


@cli.command()
@common_options
@click.option('--config', default='config', show_default=True, help='Config name without .jsonc')
@click.option('--sync', is_flag=True, help='Run manual sync after init')
def init_autoupdate(
    hostname: str,
    user: str | None,
    port: int | None,
    noninteractive: bool,
    sync: bool,
    config: str,
):
    jsonc_config_path, jsonc_config = load_jsonc_config(config)

    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    c.sudo('rm -f /etc/cron.d/ofm_linux_host')

    prepare_shared(c, linux_host_deploy_config)
    prepare_linux_host(c, jsonc_config_path)

    if sync:
        run_linux_host_sync(c)

    install_linux_host_cron(c)

    check_server_health(jsonc_config, hostname, print_results=True)


@cli.command()
@common_options
@click.option('--config', default='config', show_default=True, help='Config name without .jsonc')
def sync(hostname: str, user: str | None, port: int | None, noninteractive: bool, config: str):
    _, jsonc_config = load_jsonc_config(config)

    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)
    run_linux_host_sync(c)

    check_server_health(jsonc_config, hostname, print_results=True)


def load_jsonc_config(config_name: str) -> tuple[Path, dict[str, Any]]:
    if config_name.endswith('.jsonc'):
        raise click.ClickException(
            'Pass the config name without .jsonc, for example: --config staging'
        )

    jsonc_config_path = (
        linux_host_deploy_config.local_linux_host_config_dir / f'{config_name}.jsonc'
    )
    if not jsonc_config_path.is_file():
        raise click.ClickException(
            f'{jsonc_config_path} not found. Copy config/linux_host/config.sample.jsonc to '
            + 'config/linux_host/config.jsonc or pass --config YOUR_CONFIG_NAME_WITHOUT_JSONC.'
        )

    try:
        jsonc_config = read_linux_host_jsonc_config(jsonc_config_path)
    except RuntimeError as e:
        raise click.ClickException(str(e)) from e

    return jsonc_config_path, jsonc_config


if __name__ == '__main__':
    cli()
