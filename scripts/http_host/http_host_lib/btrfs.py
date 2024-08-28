import shutil
import subprocess
from pathlib import Path

import click

from http_host_lib.utils import download_file_aria2, get_remote_file_size


def download_and_extract_tileset(area: str, version: str, runs_dir: Path) -> bool:
    """
    returns True if downloaded something
    """

    click.echo(f'downloading {area} {version}')

    version_dir = runs_dir / area / version
    btrfs_file = version_dir / 'tiles.btrfs'
    if btrfs_file.exists():
        print('  file exists, skipping download')
        return False

    temp_dir = runs_dir / '_tmp'
    shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(parents=True)

    url = f'https://{area}.openfreemap.com/{version}/tiles.btrfs.gz'

    # check disk space
    disk_free = shutil.disk_usage(temp_dir).free
    file_size = get_remote_file_size(url)
    if not file_size:
        raise ValueError('Cannot get remote file size')

    needed_space = file_size * 3
    if disk_free < needed_space:
        raise ValueError(f'Not enough disk space. Needed: {needed_space}, free space: {disk_free}')

    target_file = temp_dir / 'tiles.btrfs.gz'
    download_file_aria2(url, target_file)

    print('Uncompressing...')
    subprocess.run(['unpigz', temp_dir / 'tiles.btrfs.gz'], check=True)
    btrfs_src = temp_dir / 'tiles.btrfs'

    shutil.rmtree(version_dir, ignore_errors=True)
    version_dir.mkdir(parents=True)

    btrfs_src.rename(btrfs_file)

    shutil.rmtree(temp_dir)
    return True
