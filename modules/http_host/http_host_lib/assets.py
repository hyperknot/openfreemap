import shutil
import subprocess

import requests

from http_host_lib.config import config
from http_host_lib.utils import download_file_aria2, download_if_size_differs


def download_assets() -> bool:
    """
    Downloads and extracts assets
    """

    changed = False

    changed += download_and_extract_asset_tar_gz('fonts')
    changed += download_and_extract_asset_tar_gz('styles')
    changed += download_and_extract_asset_tar_gz('natural_earth')

    changed += download_sprites()

    return changed


def download_and_extract_asset_tar_gz(asset_kind):
    """
    Download and extract asset.tgz if the file size differ or not available locally
    Returns True if modified
    """

    print(f'Downloading asset {asset_kind}')

    asset_dir = config.local_assets_dir / asset_kind
    asset_dir.mkdir(exist_ok=True, parents=True)

    url = f'https://assets.openfreemap.com/{asset_kind}/ofm.tar.gz'
    local_file = asset_dir / 'ofm.tar.gz'
    if not download_if_size_differs(url, local_file):
        print(f'  skipping asset: {asset_kind}')
        return False

    ofm_dir = asset_dir / 'ofm'
    ofm_dir_bak = asset_dir / 'ofm.bak'
    shutil.rmtree(ofm_dir_bak, ignore_errors=True)
    if ofm_dir.exists():
        ofm_dir.rename(ofm_dir_bak)

    subprocess.run(
        ['tar', '-xzf', local_file, '-C', asset_dir],
        check=True,
    )

    print(f'  downloaded asset: {asset_kind}')
    return True


def download_sprites() -> bool:
    """
    Sprites are special assets, as we have to keep the old versions indefinitely
    """

    print('Downloading sprites')

    sprites_dir = config.local_assets_dir / 'sprites'
    sprites_dir.mkdir(exist_ok=True, parents=True)

    r = requests.get('https://assets.openfreemap.com/files.txt', timeout=30)
    r.raise_for_status()

    sprites_remote = [l for l in r.text.splitlines() if l.startswith('sprites/')]

    changed = False

    for sprite in sprites_remote:
        sprite_name = sprite.split('/')[1].replace('.tar.gz', '')

        if (sprites_dir / sprite_name).is_dir():
            print(f'  skipping sprite version: {sprite_name}')
            continue

        url = f'https://assets.openfreemap.com/sprites/{sprite_name}.tar.gz'
        local_file = sprites_dir / 'temp.tar.gz'
        download_file_aria2(url, local_file)

        subprocess.run(
            ['tar', '-xzf', local_file, '-C', sprites_dir],
            check=True,
        )
        local_file.unlink()
        print(f'  downloaded sprite version: {sprite_name}')
        changed = True

    return changed
