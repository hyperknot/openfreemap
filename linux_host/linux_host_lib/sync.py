import shutil

from linux_host.linux_host_lib.assets import download_assets
from linux_host.linux_host_lib.btrfs import download_area_version
from linux_host.linux_host_lib.linux_host_config import linux_host_config
from linux_host.linux_host_lib.mount import auto_mount, clean_up_mounts
from linux_host.linux_host_lib.nginx_config_gen import write_nginx_config
from linux_host.linux_host_lib.utils import assert_linux, assert_sudo
from linux_host.linux_host_lib.versions import get_remote_deployed_versions, write_version_files


def full_sync(force=False):
    """
    Runs the sync task, normally called by cron every minute
    On a new server this also takes care of everything, no need to run anything manually.
    """

    assert_linux()
    assert_sudo()

    # if it's a manual/forced run, we clean up old/deleted mounts
    if force:
        clean_up_mounts(linux_host_config.mnt_dir)

    remote_versions = {
        area: version
        for area, version in get_remote_deployed_versions().items()
        if area != 'planet' or not linux_host_config.json_config.get('skip_planet')
    }

    assets_changed = download_assets()

    btrfs_downloaded = False
    for area in linux_host_config.areas:
        if area == 'planet' and linux_host_config.json_config.get('skip_planet'):
            continue

        deployed_version = remote_versions.get(area)
        if deployed_version:
            btrfs_downloaded += download_area_version(area=area, version=deployed_version)

        btrfs_downloaded += download_area_version(area=area, version='latest')

    versions_changed = write_version_files(remote_versions)

    if btrfs_downloaded or versions_changed or assets_changed or force:
        auto_clean_btrfs()
        auto_mount()

        write_nginx_config()

        clean_up_mounts(linux_host_config.mnt_dir)


def auto_clean_btrfs():
    """
    Clean old btrfs runs

    For each area we keep max two versions:
    1. The newest one available locally
    2. The one currently deployed, specified in /data/ofm/config/linux_host/deployed_versions
    3. If there is no deployed version, then we include the second newest one
    """

    print('Running auto clean btrfs')

    for area in linux_host_config.areas:
        area_dir = linux_host_config.runs_dir / area
        if not area_dir.is_dir():
            continue

        local_versions = sorted([i.name for i in area_dir.iterdir()])

        versions_to_keep = set()

        # add newest version
        if local_versions:
            versions_to_keep.add(local_versions[-1])

        # add deployed version
        try:
            deployed_version_file = linux_host_config.deployed_versions_dir / f'{area}.txt'
            deployed_version = deployed_version_file.read_text().strip()
            if (linux_host_config.runs_dir / area / deployed_version).exists():
                versions_to_keep.add(deployed_version)
        except Exception:
            pass

        # if still only one version, we include the second newest one
        if len(versions_to_keep) == 1 and len(local_versions) >= 2:
            versions_to_keep.add(local_versions[-2])

        print(f'  keeping runs for {area}: {sorted(versions_to_keep)}')

        versions_to_remove = set(local_versions).difference(versions_to_keep)

        for version in versions_to_remove:
            # Interesting bit: linux allows us to remove the disk image file for a mount
            # while the mount is still being used.
            # We delete the disk image, update nginx config and only then unmount the /mnt dir.
            print(f'  removing runs for {area}: {version}')
            version_dir = linux_host_config.runs_dir / area / version
            shutil.rmtree(version_dir)
