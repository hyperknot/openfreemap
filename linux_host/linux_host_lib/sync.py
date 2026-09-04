import shutil
import subprocess
from pathlib import Path

from linux_host.linux_host_lib.assets import download_assets
from linux_host.linux_host_lib.btrfs import prepare_version
from linux_host.linux_host_lib.linux_host_config import get_linux_host_config
from linux_host.linux_host_lib.lock import host_lock
from linux_host.linux_host_lib.mount import reconcile_mounts
from linux_host.linux_host_lib.nginx_config_gen import write_nginx_config_if_changed
from linux_host.linux_host_lib.telegram_alerts import send_telegram_alert
from linux_host.linux_host_lib.utils import assert_linux, assert_sudo
from linux_host.linux_host_lib.versions import (
    get_local_deployed_versions,
    get_remote_deployed_versions,
    write_version_files,
)
from shared_lib.utils.get_version import get_versions_for_area


def full_sync() -> None:
    assert_linux()
    assert_sudo()

    with host_lock():
        remote_deployed = get_remote_deployed_versions()
        missing_areas = set(get_linux_host_config().areas) - remote_deployed.keys()
        if missing_areas:
            raise RuntimeError(
                f'cannot determine deployed versions for: {", ".join(sorted(missing_areas))}'
            )

        candidates = get_candidates() if get_linux_host_config().auto_update else {}
        shutil.rmtree(get_linux_host_config().tmp_dir, ignore_errors=True)

        try:
            download_assets()
        except Exception as e:
            send_telegram_alert(f'ERROR\nasset sync failed\n{type(e).__name__}: {e}')
            raise

        for area in get_linux_host_config().areas:
            deployed = remote_deployed[area]
            try:
                prepare_version(area, deployed)
            except Exception as e:
                send_telegram_alert(
                    f'ERROR\nBTRFS download failed\n{area} {deployed}\n{type(e).__name__}: {e}'
                )
                raise

            candidate = candidates.get(area)
            if candidate and candidate != deployed:
                try:
                    prepare_version(area, candidate)
                except Exception as e:
                    print(f'candidate download failed: {area} {candidate}: {type(e).__name__}: {e}')

        write_version_files(remote_deployed)
        active_versions = get_local_deployed_versions()
        # This explicit set is the complete retention policy. Do not infer a
        # rollback version from directory ordering or resumable staging state.
        retained_versions = {area: {version} for area, version in active_versions.items()}
        for area, candidate in candidates.items():
            if (get_linux_host_config().versions_dir / area / candidate / 'tiles.btrfs').is_file():
                retained_versions.setdefault(area, set()).add(candidate)

        reconcile_mounts(retained_versions)
        write_nginx_config_if_changed(retained_versions, active_versions)
        # Loaded nginx configuration must stop referencing data before removal.
        garbage_collect(retained_versions)


def get_candidates() -> dict[str, str]:
    candidates: dict[str, str] = {}
    for area in get_linux_host_config().areas:
        try:
            candidates[area] = get_versions_for_area(area)[-1]
        except Exception as e:
            print(f'cannot fetch newest version for {area}: {type(e).__name__}: {e}')
    return candidates


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

        if not get_linux_host_config().mnt_dir.is_dir():
            continue
        kept_mounts = {get_linux_host_config().mnt_dir / f'{area}-{version}' for version in keep}
        for mnt in get_linux_host_config().mnt_dir.glob(f'{area}-*'):
            if mnt not in kept_mounts:
                _remove_mount(mnt)

    shutil.rmtree(get_linux_host_config().tmp_dir, ignore_errors=True)


def _remove_mount(mnt: Path) -> bool:
    if subprocess.run(['mountpoint', '-q', str(mnt)]).returncode == 0:
        if subprocess.run(['umount', str(mnt)]).returncode != 0:
            print(f'deferred: {mnt} busy')
            return False
    if mnt.exists():
        mnt.rmdir()
    return True
