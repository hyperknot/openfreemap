import shutil
import subprocess
from pathlib import Path

from linux_host.linux_host_lib.assets import download_assets
from linux_host.linux_host_lib.btrfs import prepare_version
from linux_host.linux_host_lib.linux_host_config import get_linux_host_config
from linux_host.linux_host_lib.lock import host_lock
from linux_host.linux_host_lib.mount import reconcile_mounts
from linux_host.linux_host_lib.nginx_config_gen import write_nginx_config_if_changed
from linux_host.linux_host_lib.telegram_alerts import send_telegram
from linux_host.linux_host_lib.utils import assert_linux, assert_sudo
from linux_host.linux_host_lib.versions import (
    get_remote_deployed_versions,
    write_version_files,
)
from shared_lib.utils.cloudflare import CLOUDFLARE_ERRORS
from shared_lib.utils.get_version import get_versions_by_area


def full_sync() -> None:
    assert_linux()
    assert_sudo()
    config = get_linux_host_config()

    with host_lock():
        # nginx is disabled at boot. Mount every complete image on disk before
        # starting it, as the existing nginx config can reference any of them
        # (e.g. a prefetched candidate).
        local_versions: dict[str, set[str]] = {}
        for image in config.versions_dir.glob('*/*/tiles.btrfs'):
            local_versions.setdefault(image.parent.parent.name, set()).add(image.parent.name)
        reconcile_mounts(local_versions)
        subprocess.run(['systemctl', 'start', 'nginx'], check=True)

        # auto_update false: no network access after the first successful sync.
        # Deploy wipes state/, so a redeploy syncs once more.
        if not config.auto_update and all(
            (config.deployed_versions_dir / f'{area}.txt').is_file() for area in config.areas
        ):
            return

        try:
            remote_deployed = get_remote_deployed_versions()
            # Raises on files.txt failure: without candidates, GC would delete a
            # prefetched one.
            candidates = get_candidates() if config.auto_update else {}
            shutil.rmtree(config.tmp_dir, ignore_errors=True)

            for area in config.areas:
                prepare_version(area, remote_deployed[area])

            for area, candidate in candidates.items():
                if candidate != remote_deployed[area]:
                    try:
                        prepare_version(area, candidate)
                    except Exception as e:
                        msg = f'candidate download failed: {area} {candidate}: {type(e).__name__}: {e}'
                        print(msg)
                        if not isinstance(e, CLOUDFLARE_ERRORS):
                            send_telegram(msg)

            active_versions = remote_deployed
            # This explicit set is the complete retention policy. Do not infer a
            # rollback version from directory ordering or resumable staging state.
            retained_versions = {area: {version} for area, version in active_versions.items()}
            for area, candidate in candidates.items():
                if (config.versions_dir / area / candidate / 'tiles.btrfs').is_file():
                    retained_versions.setdefault(area, set()).add(candidate)

            reconcile_mounts(retained_versions)
            write_nginx_config_if_changed(retained_versions, active_versions)
            # Written after the reload, so the file means this version is live.
            write_version_files(remote_deployed)
            # Loaded nginx configuration must stop referencing data before removal.
            garbage_collect(retained_versions)

            download_assets()
        except CLOUDFLARE_ERRORS as e:
            # Public endpoint reads are unreliable: no alert, the next run retries.
            print(f'cloudflare: {type(e).__name__}: {e}; retrying next minute')


def get_candidates() -> dict[str, str]:
    versions = get_versions_by_area(list(get_linux_host_config().areas))
    return {area: area_versions[-1] for area, area_versions in versions.items()}


def garbage_collect(retained_versions: dict[str, set[str]]) -> None:
    for area in get_linux_host_config().areas:
        keep = retained_versions.get(area, set())
        area_dir = get_linux_host_config().versions_dir / area
        if area_dir.is_dir():
            for version_dir in sorted(area_dir.iterdir()):
                if not version_dir.is_dir() or version_dir.name in keep:
                    continue
                if _remove_mount(get_linux_host_config().mnt_dir / f'{area}-{version_dir.name}'):
                    shutil.rmtree(version_dir)


def _remove_mount(mnt: Path) -> bool:
    if subprocess.run(['mountpoint', '-q', str(mnt)]).returncode == 0:
        if subprocess.run(['umount', str(mnt)]).returncode != 0:
            print(f'deferred: {mnt} busy')
            return False
    if mnt.exists():
        mnt.rmdir()
    return True
