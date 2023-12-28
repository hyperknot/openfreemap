#!/usr/bin/env python3
import shutil
import subprocess
import sys
from pathlib import Path

import click
import requests


DEFAULT_RUNS_DIR = Path('/data/ofm/http_host/runs')


@click.command()
@click.option('--area', default='planet', help='The area to process')
@click.option('--version', default='latest', help='Version string, like "20231227_043106_pt"')
@click.option(
    '--runs-dir',
    help='Specify /runs directory',
    type=click.Path(dir_okay=True, file_okay=False, path_type=Path),
)
@click.option('--list-versions', is_flag=True, help='List all versions in an area and terminate')
def cli(area: str, version: str, list_versions: bool, runs_dir: Path):
    if area not in {'planet', 'monaco'}:
        sys.exit('Area must be planet or monaco')

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

    if not runs_dir and not Path('/data/ofm').exists():
        sys.exit('Please specify a runs dir with --runs-dir')

    download(area, selected_version, runs_dir or DEFAULT_RUNS_DIR)


def download(area: str, version: str, runs_dir: Path):
    click.echo(f'Downloading: area: {area}, version: {version}')

    version_dir = runs_dir / version
    btrfs_file = version_dir / 'tiles.btrfs'
    if btrfs_file.exists():
        print('File exists, skipping download')
        return

    temp_dir = runs_dir / '_tmp'
    shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(parents=True)

    gzip_file = temp_dir / 'tiles.btrfs.gz'

    url = f'https://{area}.openfreemap.com/{version}/tiles.btrfs.gz'
    print(url)

    subprocess.run(
        [
            'aria2c',
            '--split=8',
            '--max-connection-per-server=8',
            '--file-allocation=none',
            '-o',
            gzip_file,
            url,
        ],
        check=True,
    )

    subprocess.run(['unpigz', gzip_file])
    btrfs_src = temp_dir / 'tiles.btrfs'

    version_dir.mkdir()
    btrfs_src.rename(btrfs_file)

    shutil.rmtree(temp_dir)


if __name__ == '__main__':
    cli()
