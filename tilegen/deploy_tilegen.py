#!/usr/bin/env -S uv run python -P

import click

from shared_lib.deploy_shared.cli_helpers import common_options, get_connection
from shared_lib.deploy_shared.tasks_shared import prepare_shared
from shared_lib.utils.jsonc_config import read_jsonc_config
from tilegen.deploy_tilegen.tasks_tilegen import (
    disable_tilegen_cron,
    prepare_tilegen,
    stop_tilegen,
    tile_build_running,
    unmount_tilegen_filesystems,
)
from tilegen.deploy_tilegen.tilegen_deploy_config import tilegen_deploy_config


@click.command()
@common_options
@click.option('--reinstall', is_flag=True, help='Reinstall everything in /data/ofm folder')
def deploy(
    config_name: str,
    hostname: str | None,
    user: str | None,
    port: int | None,
    noninteractive: bool,
    reinstall: bool,
) -> None:
    if config_name.endswith('.jsonc'):
        raise click.ClickException('Config names should not include .jsonc')
    config_path = tilegen_deploy_config.local_tilegen_config_dir / f'{config_name}.jsonc'
    try:
        jsonc_data = read_jsonc_config(config_path)
    except (FileNotFoundError, RuntimeError) as e:
        raise click.ClickException(str(e)) from e

    hosts = jsonc_data['hosts']
    if hostname and hostname not in hosts:
        raise click.ClickException(f'Host {hostname} not found in hosts config')
    targets = [hostname] if hostname else hosts
    if not noninteractive and not click.confirm(f'Run on {", ".join(targets)}?'):
        return

    for host in targets:
        c = get_connection(host, user, port)

        # Deployments are rare, so a process check is simpler than a runtime lock.
        # The tiny race before cron removal is acceptable here.
        if not reinstall and tile_build_running(c):
            raise click.ClickException(
                f'A tile build is running on {host}; deployment made no changes. '
                'Use --reinstall to stop the build and perform a clean reinstall.'
            )

        disable_tilegen_cron(c)
        if reinstall:
            stop_tilegen(c)
            unmount_tilegen_filesystems(c)
            c.sudo('rm -rf /data/ofm')

        prepare_shared(c, tilegen_deploy_config)
        prepare_tilegen(c, config_path, enable_cron=jsonc_data['cron'])
        click.echo(f'Manual tile build command on {host}:')
        click.echo(
            'cd /data/ofm/src && sudo -u ofm env PYTHONUNBUFFERED=1 '
            './tilegen/scripts/tilegen.py make-tiles planet --upload'
        )


if __name__ == '__main__':
    deploy()
