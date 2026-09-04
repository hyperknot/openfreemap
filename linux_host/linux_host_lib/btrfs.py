import shutil
import subprocess

import requests

from linux_host.linux_host_lib.linux_host_config import get_linux_host_config
from linux_host.linux_host_lib.utils import download_file_aria2, get_remote_file_size


def prepare_version(area: str, version: str) -> None:
    """Download, verify, and atomically publish one version."""
    version_dir = get_linux_host_config().versions_dir / area / version
    if (version_dir / 'tiles.btrfs').is_file():
        return

    shutil.rmtree(version_dir, ignore_errors=True)
    tmp_dir = get_linux_host_config().tmp_dir / area / version
    shutil.rmtree(tmp_dir, ignore_errors=True)

    base_url = f'https://btrfs.openfreemap.com/areas/{area}/{version}'
    url = f'{base_url}/tiles.btrfs'
    tmp_file = tmp_dir / 'tiles.btrfs'

    try:
        response = requests.get(f'{base_url}/SHA256SUMS', timeout=30)
        response.raise_for_status()
        expected_hash = next(
            (
                parts[0]
                for line in response.text.splitlines()
                if len(parts := line.split()) >= 2 and parts[1] == 'tiles.btrfs'
            ),
            None,
        )
        if not expected_hash:
            raise RuntimeError('tiles.btrfs is missing from SHA256SUMS')

        remote_size = get_remote_file_size(url)
        if remote_size is None:
            raise RuntimeError(f'cannot get remote file size for {url}')

        tmp_dir.mkdir(parents=True)
        needed_space = remote_size + 1024**3
        free_space = shutil.disk_usage(tmp_dir).free
        if free_space < needed_space:
            raise RuntimeError(
                f'not enough disk space. Needed: {needed_space}, free space: {free_space}'
            )

        download_file_aria2(url, tmp_file)
        if tmp_file.stat().st_size != remote_size:
            raise RuntimeError(
                f'incorrect file size: expected {remote_size}, got {tmp_file.stat().st_size}'
            )

        digest = subprocess.run(
            ['sha256sum', str(tmp_file)], capture_output=True, text=True, check=True
        ).stdout.split()[0]
        if digest.lower() != expected_hash.lower():
            raise RuntimeError(f'SHA-256 mismatch for {url}')

        version_dir.parent.mkdir(parents=True, exist_ok=True)
        tmp_dir.rename(version_dir)
    except Exception:
        # Preparation only removes its disposable attempt and raises. The sync
        # caller decides whether this version is required or an optional prefetch.
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise
