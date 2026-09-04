import shutil
import subprocess
import tempfile
from pathlib import Path

import requests

from linux_host.linux_host_lib.linux_host_config import get_linux_host_config
from linux_host.linux_host_lib.utils import download_file_aria2, get_remote_file_size


def download_assets() -> None:
    """Download and extract assets."""
    download_and_extract_asset_tar_gz('fonts')
    download_and_extract_asset_tar_gz('styles')
    download_and_extract_asset_tar_gz('natural_earth')
    download_sprites()


def download_and_extract_asset_tar_gz(asset_kind: str) -> None:
    """Download and extract asset.tgz if its file size differs or it is unavailable locally."""

    print(f'Downloading asset {asset_kind}')

    asset_dir = get_linux_host_config().assets_dir / asset_kind
    asset_dir.mkdir(exist_ok=True, parents=True)

    url = f'https://assets.openfreemap.com/{asset_kind}/ofm.tar.gz'
    local_file = asset_dir / 'ofm.tar.gz'
    ofm_dir = asset_dir / 'ofm'
    needs_download = not local_file.is_file() or local_file.stat().st_size != get_remote_file_size(
        url
    )
    if not needs_download and ofm_dir.is_dir():
        print(f'  skipping asset: {asset_kind}')
        return

    # Never extract into the serving path. Publish the validated directory first,
    # then update the canonical archive so a failed attempt retries cleanly.
    with tempfile.TemporaryDirectory(dir=asset_dir) as temp_dir:
        temp_dir_path = Path(temp_dir)
        archive = local_file
        if needs_download:
            archive = temp_dir_path / 'ofm.tar.gz'
            download_file_aria2(url, archive)

        staged_ofm_dir = _extract_directory(archive, temp_dir_path, 'ofm')
        _replace_directory(staged_ofm_dir, ofm_dir)
        if needs_download:
            archive.replace(local_file)

    print(f'  downloaded asset: {asset_kind}')


def download_sprites() -> None:
    """
    Sprites are special assets, as we have to keep the old versions indefinitely
    """

    print('Downloading sprites')

    sprites_dir = get_linux_host_config().assets_dir / 'sprites'
    sprites_dir.mkdir(exist_ok=True, parents=True)

    r = requests.get('https://assets.openfreemap.com/files.txt', timeout=30)
    r.raise_for_status()

    sprites_remote = [l for l in r.text.splitlines() if l.startswith('sprites/')]

    for sprite in sprites_remote:
        sprite_name = sprite.split('/')[1].replace('.tar.gz', '')

        if (sprites_dir / sprite_name).is_dir():
            print(f'  skipping sprite version: {sprite_name}')
            continue

        url = f'https://assets.openfreemap.com/sprites/{sprite_name}.tar.gz'
        with tempfile.TemporaryDirectory(dir=sprites_dir) as temp_dir:
            temp_dir_path = Path(temp_dir)
            archive = temp_dir_path / 'sprite.tar.gz'
            download_file_aria2(url, archive)
            staged_sprite_dir = _extract_directory(archive, temp_dir_path, sprite_name)
            staged_sprite_dir.rename(sprites_dir / sprite_name)

        print(f'  downloaded sprite version: {sprite_name}')


def _extract_directory(archive: Path, destination: Path, name: str) -> Path:
    subprocess.run(['tar', '-xzf', archive, '-C', destination], check=True)
    extracted_dir = destination / name
    if not extracted_dir.is_dir():
        raise RuntimeError(f'archive does not contain expected directory: {name}')
    return extracted_dir


def _replace_directory(staged_dir: Path, live_dir: Path) -> None:
    backup_dir = live_dir.with_name(f'{live_dir.name}.bak')
    shutil.rmtree(backup_dir, ignore_errors=True)
    if live_dir.exists():
        live_dir.rename(backup_dir)
    try:
        staged_dir.rename(live_dir)
    except Exception:
        if backup_dir.exists():
            backup_dir.rename(live_dir)
        raise
    shutil.rmtree(backup_dir, ignore_errors=True)
