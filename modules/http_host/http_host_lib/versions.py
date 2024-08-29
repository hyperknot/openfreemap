import sys
from pathlib import Path

import requests

from http_host_lib.config import config
from http_host_lib.utils import assert_linux, assert_sudo


def sync_version_files() -> bool:
    """
    Syncs the version files from remote to local.
    Remove versions are specified by https://assets.openfreemap.com/versions/deployed_{area}.txt
    """

    print('Syncing local version files')

    assert_linux()
    assert_sudo()

    if not config.mnt_dir.exists():
        sys.exit('  mount needs to be run first')

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

        mnt_file = Path(f'/mnt/ofm/{area}-{remote_version}/metadata.json')
        if not mnt_file.exists():
            print('    local version does not exist')
            if local_version_old is not None:
                local_version_file.unlink()
                need_nginx_sync = True
            continue

        if remote_version != local_version_old:
            local_version_file.write_text(remote_version)
            need_nginx_sync = True

    return need_nginx_sync
