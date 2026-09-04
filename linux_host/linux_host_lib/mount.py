import subprocess

from linux_host.linux_host_lib.linux_host_config import get_linux_host_config


def reconcile_mounts(retained_versions: dict[str, set[str]]) -> None:
    """Mount every retained image that is not yet mounted."""
    for area, versions in retained_versions.items():
        for version in sorted(versions):
            btrfs_file = get_linux_host_config().versions_dir / area / version / 'tiles.btrfs'
            if not btrfs_file.is_file():
                continue

            mnt = get_linux_host_config().mnt_dir / f'{area}-{version}'
            if subprocess.run(['mountpoint', '-q', str(mnt)]).returncode != 0:
                mnt.mkdir(parents=True, exist_ok=True)
                subprocess.run(['mount', '-o', 'loop,ro', str(btrfs_file), str(mnt)], check=True)
            if not (mnt / 'metadata.json').is_file():
                raise RuntimeError(f'mounted version is missing metadata.json: {area} {version}')
