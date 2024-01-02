#!/usr/bin/env python3
import sys
from pathlib import Path

import click
import requests
from http_host_lib.download_fonts import download_fonts
from http_host_lib.download_tileset import download_and_extract_tileset


DEFAULT_RUNS_DIR = Path('/data/ofm/http_host/runs')
DEFAULT_ASSETS_DIR = Path('/data/ofm/http_host/assets')


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

    download_and_extract_tileset(area, selected_version, runs_dir)


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


if __name__ == '__main__':
    cli()
