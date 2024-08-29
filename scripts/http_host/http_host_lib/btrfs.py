import shutil
import subprocess
import sys

import requests

from http_host_lib.config import config
from http_host_lib.utils import download_file_aria2, get_remote_file_size


def download_area_version(area: str, version: str):
    print('running download_btrfs')

    if area not in config.areas:
        sys.exit(f'  please specify area: {config.areas}')

    versions = get_versions_for_area(area)

    if version == 'latest':
        selected_version = versions[-1]
    else:
        if version not in versions:
            available_versions_str = '\n'.join(versions)
            sys.exit(
                f'Requested version is not available.\nAvailable versions for {area}:\n{available_versions_str}'
            )
        selected_version = version

    return download_and_extract_btrfs(area, selected_version)


def get_versions_for_area(area: str) -> list:
    r = requests.get('https://btrfs.openfreemap.com/dirs.txt', timeout=30)
    r.raise_for_status()

    versions = [v.split('/')[2] for v in r.text.splitlines() if v.startswith(f'areas/{area}/')]
    return sorted(versions)


def download_and_extract_btrfs(area: str, version: str) -> bool:
    """
    returns True if download successful, False if skipped
    """

    print(f'downloading {area} {version}')

    version_dir = config.runs_dir / area / version
    btrfs_file = version_dir / 'tiles.btrfs'
    if btrfs_file.exists():
        print('  file exists, skipping download')
        return False

    temp_dir = config.runs_dir / '_tmp'
    shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(parents=True)

    url = f'https://btrfs.openfreemap.com/areas/{area}/{version}/tiles.btrfs.gz'

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
