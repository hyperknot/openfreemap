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
from http_host_lib.utils import assert_linux, assert_single_process, assert_sudo


@click.group()
def cli():
    """
    Manages OpenFreeMap HTTP hosts, including:\n
    - Downloading tilesets\n
    - Downloading assets\n
    - Deploying the correct versions of tilesets\n
    - Mounting directories\n
    - Updating nginx config\n
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

    if area not in {'planet', 'monaco'}:
        sys.exit('Please specify area: "planet" or "monaco"')

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
        sys.exit("run dir's parent doesn't exist")

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
    assert_linux()
    assert_sudo()

    if not DEFAULT_RUNS_DIR.exists():
        sys.exit('download_tileset needs to be run first')

    clean_up_mounts(MNT_DIR)
    create_fstab()

    print('Running mount -a')
    subprocess.run(['mount', '-a'], check=True)

    clean_up_mounts(MNT_DIR)


@cli.command()
@click.pass_context
def sync(ctx):
    """
    Runs the sync task, normally called by cron every minute
    """
    print(datetime.datetime.now(tz=datetime.timezone.utc))

    downloaded = False
    downloaded += ctx.invoke(download_tileset, area='monaco')
    # d2 = ctx.invoke(download_tileset, area='planet')

    if downloaded:
        ctx.invoke(mount)

    ctx.invoke(download_assets)


if __name__ == '__main__':
    # TODO
    assert_single_process()
    cli()
