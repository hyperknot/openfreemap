#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import click


# btrfs cannot shrink smaller than 256 MiB
SMALLEST_SIZE = 256 * 1024 * 1024


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
        sys.exit('  needs sudo')

    current_dir = Path.cwd()

    mnt_dir = Path(tempfile.mkdtemp(dir=current_dir, prefix='tmp_shrink_'))
    subprocess.run(['mount', '-t', 'btrfs', btrfs_img, mnt_dir], check=True)

    # shink until max. 10 MB left or reached SMALLEST_SIZE or failure
    while True:
        # needs to start with a balancing
        # https://btrfs.readthedocs.io/en/latest/Balance.html
        # https://marc.merlins.org/perso/btrfs/post_2014-05-04_Fixing-Btrfs-Filesystem-Full-Problems.html
        do_balancing(mnt_dir)

        free_bytes = get_usage(mnt_dir, 'Device unallocated')
        device_size = get_usage(mnt_dir, 'Device size')
        shrink_idea = free_bytes * 0.7

        # workaround for the SMALLEST_SIZE limit
        if device_size - free_bytes < SMALLEST_SIZE:
            shrink_idea = (device_size - SMALLEST_SIZE) * 0.7

        # stop if 10 MB left
        if shrink_idea < 10_000_000:
            break

        # stop if process error
        if not do_shrink(mnt_dir, shrink_idea):
            break

    total_size = get_usage(mnt_dir, 'Device size')

    subprocess.run(['umount', mnt_dir])
    mnt_dir.rmdir()

    subprocess.run(['truncate', '-s', str(total_size), btrfs_img])
    print(f'Truncated {btrfs_img} to {total_size//1_000_000} MB size')
    print('shrink_btrfs.py DONE')


def get_usage(mnt: Path, key: str):
    p = subprocess.run(
        ['btrfs', 'filesystem', 'usage', '-b', mnt], text=True, capture_output=True, check=True
    )
    for line in p.stdout.splitlines():
        if f'{key}:' not in line:
            continue
        free = int(line.split(':')[1])
        return free


def do_shrink(mnt: Path, delta_size: float):
    delta_size = int(delta_size)
    print(f'Trying to shrink by {delta_size//1_000_000} MB')
    p = subprocess.run(['btrfs', 'filesystem', 'resize', str(-delta_size), mnt])
    return p.returncode == 0


def do_balancing(mnt: Path):
    print('Starting btrfs balancing')
    p = subprocess.run(
        ['btrfs', 'balance', 'start', '-dusage=100', mnt], capture_output=True, text=True
    )
    if p.returncode:
        print(f'Balance error: {p.stdout} {p.stderr}')
    print('Balancing done')


if __name__ == '__main__':
    cli()
