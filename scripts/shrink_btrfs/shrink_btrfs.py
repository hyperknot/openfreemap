#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import click


# btrfs cannot shrink smaller than about 268 MB
SMALLEST_SIZE = 270_000_000


@click.command()
@click.argument(
    'btrfs_img',
    type=click.Path(exists=True, dir_okay=False, file_okay=True, path_type=Path),
)
def cli(btrfs_img: Path):
    """
    Shrinks a BTRFS image
    // I cannot believe that BTRFS is over 15 years old,
    // yet there is no resize2fs tool which can shrink a disk image
    // to minimum size.
    // It cannot even tell you how much should be the right size,
    // it just randomly fails after which you have to umount and mount again.
    // So we have to make a loop which tries to shrink it until it fails.

    // Also, WONTFIX bugs like how instead of telling you that
    // minimum fs size is 256 MB, it says "ERROR: unable to resize - Invalid argument"
    // https://bugzilla.kernel.org/show_bug.cgi?id=118111
    """

    if os.geteuid() != 0:
        sys.exit('Needs sudo')

    current_dir = Path.cwd()

    mnt_dir = Path(tempfile.mkdtemp(dir=current_dir, prefix='tmp_shrink_'))
    subprocess.run(['mount', '-t', 'btrfs', btrfs_img, mnt_dir], check=True)

    # needs to start with a balancing
    # https://btrfs.readthedocs.io/en/latest/Balance.html
    # https://marc.merlins.org/perso/btrfs/post_2014-05-04_Fixing-Btrfs-Filesystem-Full-Problems.html
    print('Starting btrfs balancing')
    p = subprocess.run(
        ['btrfs', 'balance', 'start', '-dusage=100', mnt_dir], capture_output=True, text=True
    )
    if p.returncode:
        # subprocess.run(['umount', mnt_dir])
        # mnt_dir.rmdir()
        print(f'Balance error: {p.stdout} {p.stderr}')
    print('Balancing done')

    # shink until max. 10 MB left, or failure
    free_bytes = get_usage(mnt_dir, 'Device unallocated')
    while free_bytes > 10_000_000:
        if not shrink(mnt_dir, int(free_bytes * 0.9)):
            break
        free_bytes = get_usage(mnt_dir, 'Device unallocated')

    total_size = get_usage(mnt_dir, 'Device size')

    subprocess.run(['umount', mnt_dir])
    mnt_dir.rmdir()

    subprocess.run(['truncate', '-s', str(total_size), btrfs_img])
    print(f'Truncated {btrfs_img} to {total_size//1_000_000} MB size')


def get_usage(mnt: Path, key: str):
    p = subprocess.run(
        ['btrfs', 'filesystem', 'usage', '-b', mnt], text=True, capture_output=True, check=True
    )
    for line in p.stdout.splitlines():
        if f'{key}:' not in line:
            continue
        free = int(line.split(':')[1])
        return free


def shrink(mnt: Path, delta_size: int):
    print(f'Trying to shrink by {delta_size//1_000_000} MB')
    p = subprocess.run(['btrfs', 'filesystem', 'resize', str(-delta_size), mnt])
    return p.returncode == 0


if __name__ == '__main__':
    cli()
