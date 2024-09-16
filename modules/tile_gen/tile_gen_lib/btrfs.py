import os
import shutil
import subprocess
from pathlib import Path

from tile_gen_lib.config import config
from tile_gen_lib.utils import python_venv_executable


IMAGE_SIZE = '200G'


def make_btrfs(run_folder: Path):
    os.chdir(run_folder)

    cleanup_folder(run_folder)

    # make an empty file that's definitely bigger then the current OSM output
    for image in ['image.btrfs', 'image2.btrfs']:
        subprocess.run(['fallocate', '-l', IMAGE_SIZE, image], check=True)
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

    # extract mbtiles
    extract_script = config.tile_gen_scripts_dir / 'extract_mbtiles.py'
    with open('extract_out.log', 'w') as out, open('extract_err.log', 'w') as err:
        subprocess.run(
            [
                python_venv_executable(),
                extract_script,
                'tiles.mbtiles',
                'mnt_rw/extract',
            ],
            check=True,
            stdout=out,
            stderr=err,
        )

    # remove mbtiles, only keep the btrfs file
    # disabled for now, saving both files currently
    # os.unlink('tiles.mbtiles')

    shutil.copy('mnt_rw/extract/osm_date', '.')

    # process logs
    subprocess.run('grep fixed extract_out.log > dedupl_fixed.log', shell=True)

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
                f.write(f"\n\n{' '.join(cmd)}\n")
                result = subprocess.run(['sudo'] + cmd, check=True, capture_output=True, text=True)
                f.write(result.stdout)

    # unmount and cleanup
    for mount in ['mnt_rw', 'mnt_rw2']:
        subprocess.run(['sudo', 'umount', mount], check=True)

    shutil.rmtree('mnt_rw')
    shutil.rmtree('mnt_rw2')

    # shrink btrfs
    shrink_script = config.tile_gen_scripts_dir / 'shrink_btrfs.py'
    with open('shrink_out.log', 'w') as out, open('shrink_err.log', 'w') as err:
        subprocess.run(
            ['sudo', python_venv_executable(), shrink_script, 'image2.btrfs'],
            check=True,
            stdout=out,
            stderr=err,
        )

    os.unlink('image.btrfs')
    shutil.move('image2.btrfs', 'tiles.btrfs')

    # parallel gzip (pigz)
    subprocess.run(['pigz', 'tiles.btrfs', '--fast'], check=True)

    # move logs
    Path('logs').mkdir()
    for pattern in ['*.log', '*.txt']:
        for file in Path().glob(pattern):
            shutil.move(file, 'logs')

    print('extract_btrfs.py DONE')


def cleanup_folder(run_folder: Path):
    print(f'cleaning up {run_folder}')

    for mount in ['mnt_rw', 'mnt_rw2']:
        subprocess.run(['sudo', 'umount', run_folder / mount], capture_output=True)

    for pattern in ['mnt_rw*', 'tmp_*', '*.btrfs', '*.gz', '*.log', '*.txt', 'logs', 'osm_date']:
        for item in run_folder.glob(pattern):
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
