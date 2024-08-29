from datetime import datetime, timezone

from http_host_lib.assets import download_assets
from http_host_lib.btrfs import download_area_version
from http_host_lib.config import config
from http_host_lib.mount import auto_mount_unmount
from http_host_lib.nginx import write_nginx_config
from http_host_lib.utils import assert_linux, assert_sudo
from http_host_lib.versions import sync_version_files


def full_sync(force=False):
    """
    Runs the sync task, normally called by cron every minute
    On a new server this also takes care of everything, no need to run anything manually.
    """

    print('---')
    print('running full_sync')
    print(datetime.now(tz=timezone.utc))

    assert_linux()
    assert_sudo()

    download_done = False
    download_done += download_area_version(area='monaco', version='latest')

    if not config.host_config.get('skip_planet'):
        download_done += download_area_version(area='planet', version='latest')

    if download_done or force:
        auto_mount_unmount()

    download_assets()

    versions_changed = sync_version_files()

    if download_done or versions_changed or force:
        write_nginx_config()
