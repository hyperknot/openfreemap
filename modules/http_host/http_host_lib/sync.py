import shutil
from datetime import datetime, timezone

from http_host_lib.assets import download_assets
from http_host_lib.btrfs import download_area_version
from http_host_lib.config import config
from http_host_lib.mount import auto_mount, clean_up_mounts
from http_host_lib.nginx import write_nginx_config
from http_host_lib.utils import assert_linux, assert_sudo
from http_host_lib.versions import fetch_version_files


def full_sync(force=False):
    """
    Runs the sync task, normally called by cron every minute
    On a new server this also takes care of everything, no need to run anything manually.
    """

    assert_linux()
    assert_sudo()

    # start

    versions_changed = fetch_version_files()

    download_assets()

    btrfs_downloaded = False

    # download latest and deployed monaco
    btrfs_downloaded += download_area_version(area='monaco', version='latest')
    btrfs_downloaded += download_area_version(area='monaco', version='deployed')

    # download latest and deployed planet
    if not config.ofm_config.get('skip_planet'):
        btrfs_downloaded += download_area_version(area='planet', version='latest')
        btrfs_downloaded += download_area_version(area='planet', version='deployed')

    if btrfs_downloaded or versions_changed or force:
        auto_clean_btrfs()
        auto_mount()

        write_nginx_config()

        clean_up_mounts(config.mnt_dir)


def auto_clean_btrfs():
    """
    Clean old btrfs runs

    For each area we keep max two versions:
    1. The newest one available locally
    2. The one currently deployed, specified in /data/ofm/config/deployed_versions
    3. If there is no deployed version, then we include the second newest one
    """

    for area in config.areas:
        area_dir = config.runs_dir / area
        if not area_dir.is_dir():
            continue

        local_versions = sorted([i.name for i in area_dir.iterdir()])

        versions_to_keep = set()

        # add newest version
        if local_versions:
            versions_to_keep.add(local_versions[-1])

        # add deployed version
        try:
            deployed_version_file = config.deployed_versions_dir / f'{area}.txt'
            deployed_version = deployed_version_file.read_text().strip()
            if (config.runs_dir / area / deployed_version).exists():
                versions_to_keep.add(deployed_version)
        except Exception:
            pass

        # if still only one version, we include the second newest one
        if len(versions_to_keep) == 1 and len(local_versions) >= 2:
            versions_to_keep.add(local_versions[-2])

        print(f'  keeping versions for {area}: {sorted(versions_to_keep)}')

        versions_to_remove = set(local_versions).difference(versions_to_keep)

        for version in versions_to_remove:
            print(f'  removing version for {area}: {version}')
            version_dir = config.runs_dir / area / version
            shutil.rmtree(version_dir)
