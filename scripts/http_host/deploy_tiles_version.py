#!/usr/bin/env python3
import datetime
import os
import subprocess
import sys
from pathlib import Path

import click
import requests


@click.command()
def cli():
    """
    Deploys the version of tiles specified by https://assets.openfreemap.com/versions/deployed_tiles_planet.txt

    1. Checking if the given version is present on the disk and mounted
    2. Writing to a version file
    3. Calling nginx_sync to update the /planet location block
    """

    print(datetime.datetime.now(tz=datetime.timezone.utc))

    if not Path('/etc/fstab').exists():
        sys.exit('Needs to be run on Linux')

    if os.geteuid() != 0:
        sys.exit('Needs sudo')

    if not Path('/mnt/ofm').exists():
        sys.exit('mounter.py needs to be run first')

    need_nginx_sync = False

    for area in ['planet', 'monaco']:
        r = requests.get(f'https://assets.openfreemap.com/versions/deployed_tiles_{area}.txt')
        r.raise_for_status()
        version_str = r.text.strip()
        print(f'remote version for {area}: {version_str}')

        local_version_file = Path(f'/data/ofm/config/deployed_tiles_{area}.txt')

        if not local_version_file.exists():
            local_version_start = None
        else:
            with open(local_version_file) as fp:
                local_version_start = fp.read()

        if not version_str:
            print('  remote version not specified')
            if local_version_start is not None:
                local_version_file.unlink()
                need_nginx_sync = True
            continue

        mnt_file = Path(f'/mnt/ofm/{area}-{version_str}/metadata.json')
        if not mnt_file.exists():
            print('  local version does not exist')
            if local_version_start is not None:
                local_version_file.unlink()
                need_nginx_sync = True
            continue

        if version_str != local_version_start:
            with open(local_version_file, 'w') as fp:
                fp.write(version_str)
            need_nginx_sync = True

    if need_nginx_sync:
        print('running nginx_sync.py')

        subprocess.run(
            [sys.executable, Path(__file__).parent / 'nginx_sync' / 'nginx_sync.py'],
            check=True,
        )

    print('\n\n\n')


if __name__ == '__main__':
    cli()
