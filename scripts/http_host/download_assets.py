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
    """
    Download and extract font assets if their file differ.
    Making updates atomic, with extract to temp + move instead of extracting in place.
    """

    fonts_dir = assets_dir / 'fonts'
    fonts_dir.mkdir(exist_ok=True, parents=True)

    fonts_temp = assets_dir / 'fonts_temp'

    for font in ['ml', 'omt', 'pm']:
        url = f'https://assets.openfreemap.com/fonts/{font}.tgz'
        local_file = fonts_dir / f'{font}.tgz'
        if not download_if_size_differs(url, local_file):
            continue

        shutil.rmtree(fonts_temp, ignore_errors=True)
        fonts_temp.mkdir()

        subprocess.run(
            ['tar', '-xzf', local_file, '-C', fonts_temp],
            check=True,
        )

        target_dir = fonts_dir / font
        target_dir_renamed = fonts_dir / f'{font}.bak'
        temp_dir = fonts_temp / font

        if target_dir.exists():
            target_dir.rename(target_dir_renamed)
        temp_dir.rename(target_dir)

        shutil.rmtree(target_dir_renamed, ignore_errors=True)

    shutil.rmtree(fonts_temp, ignore_errors=True)


def download_if_size_differs(url: str, local_file: Path):
    if not local_file.exists() or local_file.stat().st_size != get_remote_file_size(url):
        download_file(url, local_file)
        return True

    return False


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
            '--min-split-size=1M',
            '-d',
            local_file.parent,
            '-o',
            local_file.name,
            url,
        ],
        check=True,
    )


if __name__ == '__main__':
    cli()
