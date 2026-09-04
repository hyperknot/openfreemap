#!/usr/bin/env -S uv run python -P

from datetime import UTC, datetime

import click

from linux_host.linux_host_lib.sync import full_sync


@click.group()
def cli() -> None:
    """Manage OpenFreeMap linux_host servers."""


@cli.command()
def sync() -> None:
    """Run the complete host sync task."""
    print(f'---\n{datetime.now(UTC)}\nStarting sync')
    full_sync()


if __name__ == '__main__':
    cli()
