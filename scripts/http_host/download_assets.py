#!/usr/bin/env python3
import shutil
import subprocess
import sys
from pathlib import Path

import click
import requests


DEFAULT_ASSETS_DIR = Path('/data/ofm/http_host/assets')


@click.command()
@click.option(
    '--assets-dir',
    help='Specify assets directory',
    type=click.Path(dir_okay=True, file_okay=False, path_type=Path),
)
def cli(assets_dir):
    """
    Downloads and extracts assets
    """

    if not assets_dir:
        assets_dir = DEFAULT_ASSETS_DIR

    if not assets_dir.parent.exists():
        sys.exit("asset dir's parent doesn't exist")

    download_fonts(assets_dir)


def download_fonts(assets_dir):
    fonts_dir = assets_dir / 'fonts'
    fonts_dir.mkdir(exist_ok=True, parents=True)

    for font in ['ml', 'omt', 'pm']:
        url = f'https://assets.openfreemap.com/fonts/{font}.tgz'
        local_file = fonts_dir / f'{font}.tgz'
        download_if_size_differs(url, local_file)


def download_if_size_differs(url: str, local_file: Path):
    if not local_file.exists() or local_file.stat().st_size != get_remote_file_size(url):
        download_file(url, local_file)


def get_remote_file_size(url: str):
    r = requests.head(url)
    size = r.headers.get('Content-Length')
    return int(size) if size else None


def download_file(url, local_file):
    click.echo(f'Downloading: {url} into {local_file}')

    subprocess.run(
        [
            'aria2c',
            '--split=8',
            '--max-connection-per-server=8',
            '--file-allocation=none',
            '-o',
            local_file,
            url,
        ],
        check=True,
    )


if __name__ == '__main__':
    cli()
