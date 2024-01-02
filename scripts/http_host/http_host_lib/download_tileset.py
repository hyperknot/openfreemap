import shutil
import subprocess
import sys
from pathlib import Path

import click
from http_host_lib.utils import download_file_aria2


def download_and_extract_tileset(area: str, version: str, runs_dir: Path) -> bool:
    """
    returns True if downloaded something
    """

    click.echo(f'Downloading: area: {area}, version: {version}')

    version_dir = runs_dir / area / version
    btrfs_file = version_dir / 'tiles.btrfs'
    if btrfs_file.exists():
        print('File exists, skipping download')
        return False

    temp_dir = runs_dir / '_tmp'
    if temp_dir.exists():
        sys.exit(f'{temp_dir} dir exists, avoiding parallel run')

    temp_dir.mkdir(parents=True)

    url = f'https://{area}.openfreemap.com/{version}/tiles.btrfs.gz'
    target_file = temp_dir / 'tiles.btrfs.gz'
    download_file_aria2(url, target_file)

    subprocess.run(['unpigz', temp_dir / 'tiles.btrfs.gz'], check=True)
    btrfs_src = temp_dir / 'tiles.btrfs'

    shutil.rmtree(version_dir, ignore_errors=True)
    version_dir.mkdir(parents=True)

    btrfs_src.rename(btrfs_file)

    shutil.rmtree(temp_dir)
    return True
