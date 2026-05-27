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
@click.option(
    '--reinstall', is_flag=True, help='Reinstall everything in /data/ofm and /data/nginx folders'
)
def init_static(
    hostname: str,
    user: str | None,
    port: int | None,
    noninteractive: bool,
    config: str,
    reinstall: bool,
):
    jsonc_path, jsonc_data = load_jsonc_config(config)

    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    if reinstall:
        c.sudo('rm -rf /data/ofm /data/nginx')

    prepare_shared(c, linux_host_deploy_config)
    prepare_linux_host(c, jsonc_path)

    run_linux_host_sync(c)

    check_server_health(jsonc_data, hostname, print_results=True)


@cli.command()
@common_options
@click.option('--config', default='config', show_default=True, help='Config name without .jsonc')
@click.option('--sync', is_flag=True, help='Run manual sync after init')
@click.option(
    '--reinstall', is_flag=True, help='Reinstall everything in /data/ofm and /data/nginx folders'
)
def init_autoupdate(
    hostname: str,
    user: str | None,
    port: int | None,
    noninteractive: bool,
    sync: bool,
    config: str,
    reinstall: bool,
):
    jsonc_path, jsonc_data = load_jsonc_config(config)

    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    if reinstall:
        c.sudo('rm -rf /data/ofm /data/nginx')

    c.sudo('rm -f /etc/cron.d/ofm_linux_host')

    prepare_shared(c, linux_host_deploy_config)
    prepare_linux_host(c, jsonc_path)

    if sync:
        run_linux_host_sync(c)

    install_linux_host_cron(c)

    check_server_health(jsonc_data, hostname, print_results=True)


@cli.command()
@common_options
@click.option('--config', default='config', show_default=True, help='Config name without .jsonc')
def sync(hostname: str, user: str | None, port: int | None, noninteractive: bool, config: str):
    _, jsonc_data = load_jsonc_config(config)

    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)
    run_linux_host_sync(c)

    check_server_health(jsonc_data, hostname, print_results=True)


@cli.command('health-test')
@click.argument('hostname', required=False)
@click.option('--config', default='config', show_default=True, help='Config name without .jsonc')
def health_test(hostname: str | None, config: str):
    _, jsonc_data = load_jsonc_config(config)

    try:
        results = check_server_health(jsonc_data, hostname, print_results=True)
    except ValueError as e:
        raise click.ClickException(str(e)) from e

    if not results:
        raise click.ClickException('No health_check hosts configured')

    if not all(result['all_ok'] for result in results.values()):
        raise click.ClickException('Health test failed')


def load_jsonc_config(config_name: str) -> tuple[Path, dict[str, Any]]:
    if config_name.endswith('.jsonc'):
        raise click.ClickException(
            'Config names should not include .jsonc.\n\nExample:\n  --config staging'
        )

    jsonc_path = linux_host_deploy_config.local_linux_host_config_dir / f'{config_name}.jsonc'
    if not jsonc_path.is_file():
        config_dir = linux_host_deploy_config.local_linux_host_config_dir
        repo_root = linux_host_deploy_config.local_repo_root
        raise click.ClickException(
            f'Config file not found:\n'
            f'  {jsonc_path.relative_to(repo_root)}\n\n'
            f'To create the default config, run from the repo root:\n'
            f'  cp {(config_dir / "config.sample.jsonc").relative_to(repo_root)} '
            f'{(config_dir / "config.jsonc").relative_to(repo_root)}\n\n'
            f'Or use a different config file:\n'
            f'  ./deploy_linux_host.py ... --config dev\n\n'
            f'This would read:\n'
            f'  {(config_dir / "dev.jsonc").relative_to(repo_root)}'
        )

    try:
        jsonc_data = read_linux_host_jsonc_config(jsonc_path)
    except RuntimeError as e:
        raise click.ClickException(str(e)) from e

    return jsonc_path, jsonc_data


if __name__ == '__main__':
    cli()
