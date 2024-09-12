import requests

from http_host_lib.config import config
from http_host_lib.shared import get_deployed_version
from http_host_lib.utils import assert_linux, assert_sudo


def fetch_version_files() -> bool:
    """
    Syncs the version files from remote to local.
    Remote versions are specified by https://assets.openfreemap.com/versions/deployed_{area}.txt
    """

    print('Syncing local version files')

    assert_linux()
    assert_sudo()

    need_nginx_sync = False

    for area in config.areas:
        deployed_version = get_deployed_version(area)
        if not deployed_version:
            print(f'  deployed version not found: {area}')
            continue
        print(f'  deployed version {area}: {deployed_version}')

        local_version_file = config.deployed_versions_dir / f'{area}.txt'

        try:
            local_version_old = local_version_file.read_text()
        except Exception:
            local_version_old = None

        if deployed_version != local_version_old:
            config.deployed_versions_dir.mkdir(exist_ok=True, parents=True)
            local_version_file.write_text(deployed_version)
            need_nginx_sync = True

    return need_nginx_sync
