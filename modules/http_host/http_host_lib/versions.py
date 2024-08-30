import requests

from http_host_lib.config import config
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
        r = requests.get(f'https://assets.openfreemap.com/deployed_versions/{area}.txt', timeout=30)
        r.raise_for_status()
        remote_version = r.text.strip()
        assert remote_version
        print(f'  remote version for {area}: {remote_version}')

        local_version_file = config.deployed_versions_dir / f'{area}.txt'

        try:
            local_version_old = local_version_file.read_text()
        except Exception:
            local_version_old = None

        if remote_version != local_version_old:
            config.deployed_versions_dir.mkdir(exist_ok=True, parents=True)
            local_version_file.write_text(remote_version)
            need_nginx_sync = True

    return need_nginx_sync
