import subprocess
import sys
from pathlib import Path

from http_host_lib.config import config
from http_host_lib.utils import assert_linux, assert_sudo


def auto_mount():
    """
    Mounts/unmounts the btrfs images from /data/ofm/http_host/runs automatically.
    When finished, /mnt/ofm dir will have all the present tiles.btrfs files mounted in a read-only way.
    """

    print('running mount')

    assert_linux()
    assert_sudo()

    if not config.runs_dir.exists():
        sys.exit('  download-btrfs needs to be run first')

    clean_up_mounts(config.mnt_dir)
    create_fstab()

    print('  running mount -a')
    subprocess.run(['mount', '-a'], check=True)


def create_fstab():
    fstab_new = []

    for area in ['planet', 'monaco']:
        area_dir = (config.runs_dir / area).resolve()
        if not area_dir.exists():
            continue

        versions = sorted(area_dir.iterdir())
        for version in versions:
            version_str = version.name
            btrfs_file = area_dir / version_str / 'tiles.btrfs'
            if not btrfs_file.is_file():
                continue

            mnt_folder = config.mnt_dir / f'{area}-{version_str}'
            mnt_folder.mkdir(exist_ok=True, parents=True)

            fstab_new.append(f'{btrfs_file} {mnt_folder} btrfs loop,ro 0 0\n')
            print(f'  created fstab entry for {btrfs_file} -> {mnt_folder}')

    with open('/etc/fstab') as fp:
        fstab_orig = [l for l in fp.readlines() if f'{config.mnt_dir}/' not in l]

    with open('/etc/fstab', 'w') as fp:
        fp.writelines(fstab_orig + fstab_new)


def clean_up_mounts(mnt_dir):
    if not mnt_dir.exists():
        return

    print('  cleaning up mounts')

    # handle deleted files
    p = subprocess.run(['mount'], capture_output=True, text=True, check=True)
    lines = [l for l in p.stdout.splitlines() if f'{mnt_dir}/' in l and '(deleted)' in l]

    for l in lines:
        mnt_path = Path(l.split('(deleted) on ')[1].split(' type btrfs')[0])
        print(f'  removing deleted mount {mnt_path}')
        assert mnt_path.exists()
        subprocess.run(['umount', mnt_path], check=True)
        mnt_path.rmdir()

    # clean all mounts not in current fstab
    with open('/etc/fstab') as fp:
        fstab_str = fp.read()

    for subdir in mnt_dir.iterdir():
        if f'{subdir} ' in fstab_str:
            continue

        print(f'  removing old mount {subdir}')
        subprocess.run(['umount', subdir], check=True)
        subdir.rmdir()
