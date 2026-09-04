#!/usr/bin/env -S uv run python -P

from pathlib import Path
from typing import Any

import click

from linux_host.deploy_linux_host.linux_host_deploy_config import linux_host_deploy_config
from linux_host.deploy_linux_host.tasks_linux_host import (
    clean_linux_host,
    install_linux_host_cron,
    prepare_linux_host,
    run_linux_host_sync_detached,
)
from linux_host.linux_host_lib.config_loader import (
    read_linux_host_jsonc_config,
    resolve_upload_cert_paths,
)
from shared_lib.deploy_shared.cli_helpers import common_options, get_connection
from shared_lib.deploy_shared.tasks_shared import prepare_shared


@click.command()
@common_options
def deploy(
    config_name: str,
    hostname: str | None,
    user: str | None,
    port: int | None,
    noninteractive: bool,
) -> None:
    jsonc_path, jsonc_data = load_jsonc_config(config_name)
    validate_local_cert_files(jsonc_path, jsonc_data)
    hosts = resolve_hosts(jsonc_data, hostname)
    if not confirm_hosts(hosts, noninteractive):
        return

    for host in hosts:
        c = get_connection(host, user, port)
        clean_linux_host(c, jsonc_data['areas'])
        prepare_shared(c, linux_host_deploy_config)
        prepare_linux_host(c, jsonc_path)
        if jsonc_data['auto_update']:
            install_linux_host_cron(c)
            click.echo(f'Automatic sync scheduled on {host}.')
        else:
            run_linux_host_sync_detached(c, host)
        print_success_message(jsonc_data)


def validate_local_cert_files(jsonc_path: Path, jsonc_data: dict[str, Any]) -> None:
    # Validate every upload before opening any SSH connection. Direct upload then
    # needs no remote staging and invalid local input cannot change a replica.
    for domain_data in jsonc_data['domains']:
        cert = domain_data['cert']
        if cert['type'] != 'upload':
            continue

        cert_path, key_path = resolve_upload_cert_paths(jsonc_path, cert['cert_path'])
        if not cert_path.is_file() or not key_path.is_file():
            raise click.ClickException(
                f'Certificate or key file for {domain_data["domain"]} was not found.\n'
                f'Make sure these files exist:\n{cert_path}\n{key_path}'
            )


def resolve_hosts(jsonc_data: dict[str, Any], hostname: str | None) -> list[str]:
    hosts = jsonc_data['hosts']
    if hostname and hostname not in hosts:
        raise click.ClickException(f'Host {hostname} not found in hosts config')
    if not hostname and len(hosts) > 1:
        raise click.ClickException(
            'The config contains multiple hosts. Select one with --host to avoid downtime.'
        )
    return [hostname] if hostname else hosts


def confirm_hosts(hosts: list[str], noninteractive: bool) -> bool:
    return noninteractive or click.confirm(f'Run on {", ".join(hosts)}?')


def print_success_message(jsonc_data: dict[str, Any]) -> None:
    style_url = f'https://{jsonc_data["domains"][0]["domain"]}/styles/liberty'
    click.echo()
    click.secho('linux_host setup complete.', fg='green')
    click.echo('After synchronization, use this style URL in a MapLibre map:')
    click.secho(style_url, fg='cyan')
    click.echo()


def load_jsonc_config(config_name: str) -> tuple[Path, dict[str, Any]]:
    if config_name.endswith('.jsonc'):
        raise click.ClickException(
            'Config names should not include .jsonc.\n\nExample:\n'
            '  ./linux_host/deploy_linux_host.py --config staging'
        )

    jsonc_path = linux_host_deploy_config.local_linux_host_config_dir / f'{config_name}.jsonc'
    if not jsonc_path.is_file():
        config_dir = linux_host_deploy_config.local_linux_host_config_dir
        repo_root = linux_host_deploy_config.local_repo_root
        raise click.ClickException(
            f'Config file not found:\n  {jsonc_path.relative_to(repo_root)}\n\n'
            f'Create it from the sample:\n  cp '
            f'{(config_dir / "config.sample.jsonc").relative_to(repo_root)} '
            f'{(config_dir / f"{config_name}.jsonc").relative_to(repo_root)}\n\n'
            f'Then run:\n  ./linux_host/deploy_linux_host.py --config {config_name}'
        )

    try:
        jsonc_data = read_linux_host_jsonc_config(jsonc_path)
    except RuntimeError as e:
        raise click.ClickException(str(e)) from e
    return jsonc_path, jsonc_data


if __name__ == '__main__':
    deploy()
