#!/usr/bin/env -S uv run python -P

from datetime import UTC, datetime

import click

from linux_host.linux_host_lib.sync import full_sync
from linux_host.linux_host_lib.telegram_alerts import send_telegram


@click.group()
def cli() -> None:
    """Manage OpenFreeMap linux_host servers."""


@cli.command()
def sync() -> None:
    """Run the complete host sync task."""
    print(f'---\n{datetime.now(UTC)}\nStarting sync')
    try:
        full_sync()
    except Exception as e:
        # Cloudflare read errors are handled inside full_sync. Anything else alerts
        # on every run until fixed.
        send_telegram(f'sync failed: {type(e).__name__}: {e}')
        raise


if __name__ == '__main__':
    cli()
