import contextlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from tilegen.tilegen_lib.mbtiles import extract_mbtiles


IMAGE_SIZE = '200G'


def make_btrfs(run_folder: Path, area: str):
    """Create tiles.btrfs from tiles.mbtiles. Does not gzip or move logs."""
    os.chdir(run_folder)

    cleanup_folder(run_folder)

    image_size = '1G' if area == 'monaco' else IMAGE_SIZE

    # make an empty file that's definitely bigger then the current OSM output
    for image in ['image.btrfs', 'image2.btrfs']:
        subprocess.run(['fallocate', '-l', image_size, image], check=True)
        subprocess.run(['mkfs.btrfs', '-m', 'single', image], check=True, capture_output=True)

    for image, mount in [('image.btrfs', 'mnt_rw'), ('image2.btrfs', 'mnt_rw2')]:
        Path(mount).mkdir()

        # https://btrfs.readthedocs.io/en/latest/btrfs-man5.html#mount-options
        # compression doesn't make sense, data is already gzip compressed
        subprocess.run(
            [
                'sudo',
                'mount',
                '-t',
                'btrfs',
                '-o',
                'noacl,nobarrier,noatime,max_inline=4096',
                image,
                mount,
            ],
            check=True,
        )

        subprocess.run(['sudo', 'chown', 'ofm:ofm', '-R', mount], check=True)

    with (
        open('extract_out.log', 'w') as out,
        open('extract_err.log', 'w') as err,
        contextlib.redirect_stdout(out),
        contextlib.redirect_stderr(err),
    ):
        extract_mbtiles(Path('tiles.mbtiles'), Path('mnt_rw/extract'))

    shutil.copy('mnt_rw/extract/osm_date', '.')
    write_dedupl_fixed_log()

    # unfortunately, by deleting files from the btrfs partition, the partition size grows
    # so we need to rsync onto a new partition instead of deleting
    with open('rsync_out.log', 'w') as out, open('rsync_err.log', 'w') as err:
        subprocess.run(
            [
                'rsync',
                '-avH',
                '--max-alloc=4294967296',
                '--exclude',
                'dedupl',
                'mnt_rw/extract/',
                'mnt_rw2/',
            ],
            check=True,
            stdout=out,
            stderr=err,
        )

    # collect stats
    for i, mount in enumerate(['mnt_rw', 'mnt_rw2'], 1):
        with open(f'stats{i}.txt', 'w') as f:
            for cmd in [
                ['df', '-h', mount],
                ['btrfs', 'filesystem', 'df', mount],
                ['btrfs', 'filesystem', 'show', mount],
                ['btrfs', 'filesystem', 'usage', mount],
            ]:
                f.write(f'\n\n{" ".join(cmd)}\n')
                result = subprocess.run(['sudo'] + cmd, check=True, capture_output=True, text=True)
                f.write(result.stdout)

    # unmount and cleanup
    for mount in ['mnt_rw', 'mnt_rw2']:
        subprocess.run(['sudo', 'umount', mount], check=True)

    shutil.rmtree('mnt_rw')
    shutil.rmtree('mnt_rw2')

    with (
        open('shrink_out.log', 'w') as out,
        open('shrink_err.log', 'w') as err,
        contextlib.redirect_stdout(out),
        contextlib.redirect_stderr(err),
    ):
        shrink_btrfs(Path('image2.btrfs'))

    os.unlink('image.btrfs')
    shutil.move('image2.btrfs', 'tiles.btrfs')

    print('make_btrfs DONE')


def shrink_btrfs(btrfs_img: Path):
    """Shrink a Btrfs image as much as btrfs allows."""
    mnt_dir = Path(tempfile.mkdtemp(dir=Path.cwd(), prefix='tmp_shrink_'))
    mounted = False

    try:
        subprocess.run(['sudo', 'mount', '-t', 'btrfs', btrfs_img, mnt_dir], check=True)
        mounted = True

        while True:
            balance_btrfs(mnt_dir)

            free_bytes = get_btrfs_usage(mnt_dir, 'Device unallocated')
            device_size = get_btrfs_usage(mnt_dir, 'Device size')
            shrink_bytes = free_bytes * 0.7

            # Btrfs cannot shrink smaller than 256 MiB.
            if device_size - free_bytes < 256 * 1024 * 1024:
                shrink_bytes = (device_size - 256 * 1024 * 1024) * 0.7

            if shrink_bytes < 10_000_000 or not shrink_btrfs_mount(mnt_dir, int(shrink_bytes)):
                break

        total_size = get_btrfs_usage(mnt_dir, 'Device size')
    finally:
        if mounted:
            subprocess.run(['sudo', 'umount', mnt_dir], check=False)
        mnt_dir.rmdir()

    subprocess.run(['truncate', '-s', str(total_size), btrfs_img], check=True)
    print(f'Truncated {btrfs_img} to {total_size // 1_000_000} MB size')
    print('shrink_btrfs DONE')


def gzip_btrfs(run_folder: Path):
    """Gzip tiles.btrfs using pigz. Removes the original tiles.btrfs."""
    os.chdir(run_folder)
    subprocess.run(['pigz', 'tiles.btrfs', '--fast'], check=True)


def move_logs(run_folder: Path):
    """Move log and stats files into a logs/ subdirectory."""
    os.chdir(run_folder)
    Path('logs').mkdir(exist_ok=True)
    for pattern in ['*.log', '*.txt']:
        for file in Path().glob(pattern):
            shutil.move(file, 'logs')


def append_sha256sum(file, mode='a'):
    file = Path(file)
    with (file.parent / 'SHA256SUMS').open(mode) as out:
        subprocess.run(['sha256sum', file.name], cwd=file.parent, check=True, stdout=out)


def get_btrfs_usage(mnt: Path, key: str) -> int:
    result = subprocess.run(
        ['sudo', 'btrfs', 'filesystem', 'usage', '-b', mnt],
        text=True,
        capture_output=True,
        check=True,
    )
    for line in result.stdout.splitlines():
        if f'{key}:' in line:
            return int(line.split(':')[1])
    raise ValueError(f'Could not find {key!r} in btrfs usage output')


def shrink_btrfs_mount(mnt: Path, shrink_bytes: int) -> bool:
    print(f'Trying to shrink by {shrink_bytes // 1_000_000} MB')
    result = subprocess.run(['sudo', 'btrfs', 'filesystem', 'resize', str(-shrink_bytes), mnt])
    return result.returncode == 0


def balance_btrfs(mnt: Path) -> None:
    print('Starting btrfs balancing')
    result = subprocess.run(
        ['sudo', 'btrfs', 'balance', 'start', '-dusage=100', mnt],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        print(f'Balance error: {result.stdout} {result.stderr}')
    print('Balancing done')


def write_dedupl_fixed_log():
    fixed_lines = [
        line for line in Path('extract_out.log').read_text().splitlines() if 'fixed' in line
    ]
    Path('dedupl_fixed.log').write_text('\n'.join(fixed_lines))


def cleanup_folder(run_folder: Path):
    print(f'cleaning up {run_folder}')

    mounts = [run_folder / 'mnt_rw', run_folder / 'mnt_rw2', *run_folder.glob('tmp_*')]
    for mount in mounts:
        subprocess.run(['sudo', 'umount', mount], capture_output=True)

    for pattern in ['mnt_rw*', 'tmp_*', '*.btrfs', '*.gz', '*.log', '*.txt', 'logs', 'osm_date']:
        for item in run_folder.glob(pattern):
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
