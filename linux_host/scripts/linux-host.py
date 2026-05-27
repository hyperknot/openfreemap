#!/usr/bin/env -S uv run python -P

from datetime import UTC, datetime

import click

from linux_host.linux_host_lib.assets import download_assets
from linux_host.linux_host_lib.btrfs import download_area_version
from linux_host.linux_host_lib.linux_host_config import linux_host_config
from linux_host.linux_host_lib.mount import auto_mount
from linux_host.linux_host_lib.nginx_config_gen import write_nginx_config
from linux_host.linux_host_lib.sync import auto_clean_btrfs, full_sync
from linux_host.linux_host_lib.versions import fetch_version_files
from shared_lib.get_version_shared import get_versions_for_area


now = datetime.now(UTC)


@click.group()
def cli():
    """
    Manages OpenFreeMap Linux hosts, including:\n
    - Downloading btrfs images\n
    - Downloading assets\n
    - Mounting downloaded btrfs images\n
    - Fetches version files\n
    - Running the sync cron task (called every minute with linux-host-autoupdate)
    """
    try:
        linux_host_config.load_jsonc_config()
    except (FileNotFoundError, RuntimeError) as e:
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument('area', required=False)
@click.option(
    '--version', default='latest', help='Optional version string, like "20231227_043106_pt"'
)
def download_btrfs(area: str, version: str):
    """
    Downloads and uncompresses tiles.btrfs files from the btrfs bucket
    Version can be "latest" (default) or specified, like "20231227_043106_pt"
    Use --version=1 to list all available versions
    """

    download_area_version(area, version)


@cli.command(name='download-assets')
def download_assets_():
    """
    Downloads and extracts assets
    """

    download_assets()


@cli.command()
def mount():
    """
    Mounts/unmounts the btrfs images from /data/ofm/linux_host/runs automatically.
    When finished, /mnt/ofm dir will have all the present tiles.btrfs files mounted in a read-only way.
    """

    auto_mount()


@cli.command(name='fetch-versions')
def fetch_version_files_():
    """
    Fetches the version files from remote to local.
    Remote versions are specified by https://assets.openfreemap.com/versions/deployed_{area}.txt
    """

    fetch_version_files()


@cli.command()
def auto_clean():
    """
    Cleans the old btrfs images
    """

    auto_clean_btrfs()


@cli.command()
def nginx_config():
    """
    Writes the nginx config files and reloads nginx
    """

    write_nginx_config()


@cli.command()
@click.option('--force', is_flag=True, help='Force nginx sync run')
def sync(force):
    """
    Runs the sync task, normally called by cron every minute
    On a new server this also takes care of everything, no need to run anything manually.
    """

    print(f'---\n{now}\nStarting sync')

    full_sync(force)


@cli.command()
def debug():
    versions = get_versions_for_area('monaco')
    print(versions)


if __name__ == '__main__':
    cli()
