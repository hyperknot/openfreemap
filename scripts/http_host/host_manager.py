#!/usr/bin/env python3

import datetime
import subprocess
import sys
from pathlib import Path

import click
import requests
from http_host_lib.config import config
from http_host_lib.download_assets import (
    download_and_extract_asset_tar_gz,
    download_sprites,
)
from http_host_lib.download_tileset import download_and_extract_tileset
from http_host_lib.mount import clean_up_mounts, create_fstab
from http_host_lib.nginx import write_nginx_config
from http_host_lib.set_tileset_versions import set_tileset_versions
from http_host_lib.utils import assert_linux, assert_sudo


@click.group()
def cli():
    """
    Manages OpenFreeMap HTTP hosts, including:\n
    - Downloading assets\n
    - Downloading tilesets\n
    - Mounting directories\n
    - Updating nginx config\n
    - Setting the latest versions of tilesets\n
    - Running the sync cron task (called every minute)
    """


@cli.command()
@click.argument('area', required=False)
@click.option('--version', default='latest', help='Version string, like "20231227_043106_pt"')
@click.option(
    '--runs-dir',
    help='Specify runs directory',
    type=click.Path(dir_okay=True, file_okay=False, path_type=Path),
)
@click.option('--list-versions', is_flag=True, help='List all versions in an area and terminate')
def download_tileset(area: str, version: str, list_versions: bool, runs_dir: Path):
    """
    Downloads and extracts the latest tiles.btrfs file from the public bucket.
    Version can also be specified.
    """

    print('running download_tileset')

    if area not in {'planet', 'monaco'}:
        sys.exit('  please specify area: "planet" or "monaco"')

    r = requests.get(f'https://{area}.openfreemap.com/dirs.txt', timeout=30)
    r.raise_for_status()

    versions = sorted(r.text.splitlines())

    all_versions_str = '\n'.join(versions)
    if list_versions:
        print(all_versions_str)
        return

    if version == 'latest':
        selected_version = versions[-1]
    else:
        if version not in versions:
            sys.exit(f'Requested version is not available. Available versions:\n{all_versions_str}')
        selected_version = version

    if not runs_dir:
        runs_dir = config.runs_dir

    if not runs_dir.parent.exists():
        sys.exit("runs dir's parent doesn't exist")

    return download_and_extract_tileset(area, selected_version, runs_dir)


@cli.command()
@click.option(
    '--assets-dir',
    help='Specify assets directory',
    type=click.Path(dir_okay=True, file_okay=False, path_type=Path),
)
def download_assets(assets_dir: Path):
    """
    Downloads and extracts assets
    """

    print('running download_assets')

    if not assets_dir:
        assets_dir = config.assets_dir

    if not assets_dir.parent.exists():
        sys.exit("asset dir's parent doesn't exist")

    download_and_extract_asset_tar_gz(assets_dir, 'fonts')
    download_and_extract_asset_tar_gz(assets_dir, 'styles')
    download_and_extract_asset_tar_gz(assets_dir, 'natural_earth')

    download_sprites(assets_dir)


@cli.command()
def mount():
    """
    Mounts/unmounts the btrfs images from /data/ofm/http_host/runs automatically.
    When finished, /mnt/ofm dir will have all the present tiles.btrfs files mounted in a read-only way.
    """

    print('running mount')

    assert_linux()
    assert_sudo()

    if not config.runs_dir.exists():
        sys.exit('  download_tileset needs to be run first')

    clean_up_mounts(config.mnt_dir)
    create_fstab()

    print('  running mount -a')
    subprocess.run(['mount', '-a'], check=True)

    clean_up_mounts(config.mnt_dir)


@cli.command()
def set_latest_versions():
    """
    Sets the latest version of the tilesets to the version specified by
    https://assets.openfreemap.com/versions/deployed_planet.txt

    1. Checks if the given version is present on the disk and is mounted
    2. Writes to a version file
    """

    print('running set_latest_versions')

    assert_linux()
    assert_sudo()

    if not config.mnt_dir.exists():
        sys.exit('  mount needs to be run first')

    return set_tileset_versions()


@cli.command()
def nginx_sync():
    """
    Syncs the nginx config to the state of the system
    """

    print('running nginx_sync')

    assert_linux()
    assert_sudo()

    if not config.mnt_dir.exists():
        sys.exit('  mount needs to be run first')

    write_nginx_config()


@cli.command()
@click.option('--force', is_flag=True, help='Force nginx sync run')
@click.pass_context
def sync(ctx, force):
    """
    Runs the sync task, normally called by cron every minute
    On a new server this also takes care of everything, no need to run anything manually.
    """

    print('---')
    print('running sync')
    print(datetime.datetime.now(tz=datetime.timezone.utc))

    assert_linux()
    assert_sudo()

    download_done = False
    download_done += ctx.invoke(download_tileset, area='monaco')

    if not config.host_config.get('skip_planet'):
        download_done += ctx.invoke(download_tileset, area='planet')

    if download_done:
        ctx.invoke(mount)

    ctx.invoke(download_assets)

    deploy_done = ctx.invoke(set_latest_versions)

    if download_done or deploy_done or force:
        ctx.invoke(nginx_sync)


if __name__ == '__main__':
    # print(config.host_config)
    cli()
