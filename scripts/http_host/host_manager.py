#!/usr/bin/env python3
import datetime
import subprocess
import sys
from pathlib import Path

import click
import requests
from http_host_lib import DEFAULT_ASSETS_DIR, DEFAULT_RUNS_DIR, MNT_DIR
from http_host_lib.download_fonts import download_fonts
from http_host_lib.download_tileset import download_and_extract_tileset
from http_host_lib.mount import clean_up_mounts, create_fstab
from http_host_lib.nginx import write_nginx_config
from http_host_lib.set_tileset_versions import set_tileset_versions
from http_host_lib.utils import assert_linux, assert_single_process, assert_sudo


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

    r = requests.get(f'https://{area}.openfreemap.com/dirs.txt')
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
        runs_dir = DEFAULT_RUNS_DIR

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
        assets_dir = DEFAULT_ASSETS_DIR

    if not assets_dir.parent.exists():
        sys.exit("asset dir's parent doesn't exist")

    download_fonts(assets_dir)


@cli.command()
def mount():
    """
    Mounts/unmounts the btrfs images from /data/ofm/http_host/runs automatically.
    When finished, /mnt/ofm dir will have all the present tiles.btrfs files mounted in a read-only way.
    """

    print('running mount')

    assert_linux()
    assert_sudo()

    if not DEFAULT_RUNS_DIR.exists():
        sys.exit('  download_tileset needs to be run first')

    clean_up_mounts(MNT_DIR)
    create_fstab()

    print('  running mount -a')
    subprocess.run(['mount', '-a'], check=True)

    clean_up_mounts(MNT_DIR)


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

    if not MNT_DIR.exists():
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

    if not MNT_DIR.exists():
        sys.exit('  mount needs to be run first')

    write_nginx_config()


@cli.command()
@click.pass_context
def sync(ctx):
    """
    Runs the sync task, normally called by cron every minute
    On a new server this also takes care of everything, no need to run anything manually.
    """

    print('---')
    print('running sync')
    print(datetime.datetime.now(tz=datetime.timezone.utc))

    download_done = False
    download_done += ctx.invoke(download_tileset, area='monaco')
    download_done += ctx.invoke(download_tileset, area='planet')

    if download_done:
        ctx.invoke(mount)

    ctx.invoke(download_assets)

    deploy_done = ctx.invoke(set_latest_versions)

    if download_done or deploy_done:
        ctx.invoke(nginx_sync)


if __name__ == '__main__':
    cli()
