#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

import click


@click.command()
def cli():
    """
    Mounts/unmounts the btrfs images from /data/ofm/http_host/runs automatically.
    When finished, /mnt/ofm dir will have all the present tiles.btrfs files mounted in a read-only way.
    """

    if not Path('/etc/fstab').exists():
        sys.exit('Needs to be run on Linux')

    if os.geteuid() != 0:
        sys.exit('Needs sudo')

    if not Path('/data/ofm/http_host/runs').exists():
        sys.exit('downloader.py needs to be run first')

    clean_up_mounts()

    fstab_new = []

    for area in ['planet', 'monaco']:
        area_dir = (Path('/data/ofm/http_host/runs') / area).resolve()
        if not area_dir.exists():
            continue

        versions = sorted(area_dir.iterdir())
        for version in versions:
            version_str = version.name
            btrfs_file = area_dir / version_str / 'tiles.btrfs'
            if not btrfs_file.is_file():
                continue

            mnt_folder = Path('/mnt/ofm') / f'{area}-{version_str}'
            mnt_folder.mkdir(exist_ok=True, parents=True)

            fstab_new.append(f'{btrfs_file} {mnt_folder} btrfs loop,ro 0 0\n')
            print(f'Created fstab entry for {btrfs_file} -> {mnt_folder}')

    with open('/etc/fstab') as fp:
        fstab_orig = [l for l in fp.readlines() if '/mnt/ofm/' not in l]

    with open('/etc/fstab', 'w') as fp:
        fp.writelines(fstab_orig + fstab_new)

    print('Running mount -a')
    subprocess.run(['mount', '-a'], check=True)

    clean_up_mounts()
    print('DONE')


def clean_up_mounts():
    mnt_dir = Path('/mnt/ofm')
    if not mnt_dir.exists():
        return

    print('Cleaning up mounts')

    with open('/etc/fstab') as fp:
        fstab_str = fp.read()

    for subdir in mnt_dir.iterdir():
        if f'{subdir} ' in fstab_str:
            continue

        subprocess.run(['umount', subdir])
        subdir.rmdir()


if __name__ == '__main__':
    cli()
